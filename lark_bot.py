"""
飞书 AI 机器人主程序
"""
import os
import sys
import logging
import argparse
import schedule
import time
from threading import Thread
from typing import Optional

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("dotenv module not installed, using environment variables directly")

# 配置 SSL 证书
from feishu_bot.utils.ssl_config import configure_ssl
configure_ssl()

# 导入配置和主应用
from feishu_bot.config import BotConfig
from feishu_bot.feishu_bot import FeishuBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def cleanup_expired_sessions(bot: FeishuBot) -> None:
    """清理过期会话的定时任务"""
    try:
        count = bot.session_manager.cleanup_expired_sessions()
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")


def run_scheduler(bot: FeishuBot) -> None:
    """运行定时任务调度器"""
    # 每小时清理一次过期会话
    schedule.every().hour.do(cleanup_expired_sessions, bot)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次


def start_web_admin(bot: FeishuBot) -> Optional[object]:
    """启动 Web 管理界面（如果启用）
    
    Args:
        bot: FeishuBot 实例
        
    Returns:
        WebAdminServer 实例，如果未启用则返回 None
    """
    # 检查是否启用 Web 管理界面
    enable_web_admin = os.environ.get("ENABLE_WEB_ADMIN", "false").lower() == "true"
    
    if not enable_web_admin:
        logger.info("Web Admin Interface is disabled (ENABLE_WEB_ADMIN not set to 'true')")
        return None
    
    try:
        # 导入 Web 管理界面模块
        from feishu_bot.web_admin.server import WebAdminServer
        
        # 读取配置
        host = os.environ.get("WEB_ADMIN_HOST", "0.0.0.0")
        port = int(os.environ.get("WEB_ADMIN_PORT", "8080"))
        admin_password = os.environ.get("WEB_ADMIN_PASSWORD")
        jwt_secret_key = os.environ.get("JWT_SECRET_KEY")
        static_folder = os.environ.get("WEB_ADMIN_STATIC_FOLDER")
        log_level = os.environ.get("WEB_ADMIN_LOG_LEVEL", "INFO")
        log_dir = os.environ.get("WEB_ADMIN_LOG_DIR")
        enable_rate_limiting = os.environ.get("WEB_ADMIN_RATE_LIMITING", "true").lower() == "true"
        
        # 检查必需的配置
        if not admin_password:
            logger.warning("WEB_ADMIN_PASSWORD not set, using default password 'admin123'")
        
        if not jwt_secret_key:
            logger.warning("JWT_SECRET_KEY not set, using development key (not secure for production)")
        
        # 创建 Web 管理界面服务器
        logger.info("Initializing Web Admin Interface...")
        web_server = WebAdminServer(
            config_manager=bot.config_manager,
            host=host,
            port=port,
            admin_password=admin_password,
            jwt_secret_key=jwt_secret_key,
            static_folder=static_folder,
            log_level=log_level,
            log_dir=log_dir,
            enable_rate_limiting=enable_rate_limiting
        )
        
        # 在单独的线程中启动 Web 服务器
        web_thread = Thread(
            target=web_server.start,
            kwargs={"debug": False},
            daemon=True,
            name="WebAdminServer"
        )
        web_thread.start()
        logger.info("✅ Web Admin Interface started successfully")
        
        return web_server
        
    except ImportError as e:
        logger.error(f"Failed to import Web Admin module: {e}")
        logger.error("Web Admin Interface dependencies may not be installed")
        return None
    except Exception as e:
        logger.error(f"Failed to start Web Admin Interface: {e}", exc_info=True)
        return None


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='飞书 AI 机器人')
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Web 服务器实例（用于优雅关闭）
    web_server = None
    
    try:
        # 加载配置
        logger.info("Loading configuration...")
        config = BotConfig.from_env()
        logger.info("✅ Configuration loaded successfully")
        
        # 创建机器人实例
        logger.info("Initializing FeishuBot...")
        bot = FeishuBot(config)
        logger.info("✅ FeishuBot initialized successfully")
        
        # 启动定时任务线程
        scheduler_thread = Thread(target=run_scheduler, args=(bot,), daemon=True)
        scheduler_thread.start()
        logger.info("✅ Scheduler started")
        
        # 启动 Web 管理界面（如果启用）
        web_server = start_web_admin(bot)
        
        # 启动机器人
        logger.info("Starting FeishuBot...")
        bot.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        
        # 优雅关闭 Web 服务器
        if web_server is not None:
            try:
                logger.info("Stopping Web Admin Interface...")
                web_server.stop()
            except Exception as e:
                logger.error(f"Error stopping Web Admin Interface: {e}")
        
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}", exc_info=True)
        
        # 优雅关闭 Web 服务器
        if web_server is not None:
            try:
                web_server.stop()
            except Exception as e:
                logger.error(f"Error stopping Web Admin Interface: {e}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()

