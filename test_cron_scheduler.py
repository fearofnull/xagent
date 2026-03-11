#!/usr/bin/env python3
"""测试定时任务调度器"""
import sys
import time
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 导入定时任务模块
from src.xagent.core.crons.manager import CronManager
from src.xagent.core.crons.models import (
    CronJobSpec,
    CronJobSchedule,
    CronJobDispatch,
    CronJobTarget,
    CronJobRuntime
)

def test_cron_scheduler():
    """测试定时任务调度器"""
    logger.info("=" * 60)
    logger.info("开始测试定时任务调度器")
    logger.info("=" * 60)
    
    # 创建一个简单的 channel_manager mock
    class MockChannelManager:
        async def send_message(self, channel, chat_id, user_id, content, mode):
            logger.info(f"📨 [MOCK] 发送消息: channel={channel}, chat_id={chat_id}, user_id={user_id}")
            logger.info(f"📨 [MOCK] 消息内容: {content}")
    
    try:
        # 1. 初始化 CronManager
        logger.info("\n步骤 1: 初始化 CronManager")
        channel_manager = MockChannelManager()
        cron_manager = CronManager(channel_manager=channel_manager)
        logger.info("✅ CronManager 初始化成功")
        
        # 2. 启动 CronManager
        logger.info("\n步骤 2: 启动 CronManager")
        cron_manager.start_sync()
        logger.info("✅ CronManager 启动成功")
        
        # 3. 检查调度器状态
        logger.info("\n步骤 3: 检查调度器状态")
        logger.info(f"调度器类型: {type(cron_manager._scheduler).__name__}")
        logger.info(f"调度器运行状态: {cron_manager._scheduler.running if cron_manager._scheduler else 'None'}")
        logger.info(f"CronManager 启动状态: {cron_manager._started}")
        
        # 4. 列出现有任务
        logger.info("\n步骤 4: 列出现有任务")
        jobs = cron_manager.list_jobs_sync()
        logger.info(f"找到 {len(jobs)} 个任务:")
        for job in jobs:
            logger.info(f"  - {job.id}: {job.name} (enabled={job.enabled}, cron={job.schedule.cron})")
            
            # 检查任务是否在调度器中
            aps_job = cron_manager._scheduler.get_job(job.id)
            if aps_job:
                logger.info(f"    ✅ 任务已注册到调度器")
                logger.info(f"    下次运行时间: {aps_job.next_run_time}")
            else:
                logger.info(f"    ❌ 任务未注册到调度器")
        
        # 5. 创建一个测试任务 (每分钟执行一次)
        logger.info("\n步骤 5: 创建测试任务")
        test_job = CronJobSpec(
            id="test-scheduler",
            name="调度器测试任务",
            enabled=True,
            schedule=CronJobSchedule(
                type="cron",
                cron="* * * * *",  # 每分钟执行
                timezone="UTC"
            ),
            task_type="text",
            text="🧪 这是一个测试消息",
            dispatch=CronJobDispatch(
                type="channel",
                channel="console",
                target=CronJobTarget(
                    chat_id="test-chat-id",
                    user_id="test-user-id"
                ),
                mode="final"
            ),
            runtime=CronJobRuntime(
                max_concurrency=1,
                timeout_seconds=30,
                misfire_grace_seconds=10
            )
        )
        
        cron_manager.create_or_replace_job_sync(test_job)
        logger.info("✅ 测试任务创建成功")
        
        # 6. 验证任务已注册
        logger.info("\n步骤 6: 验证任务已注册到调度器")
        aps_job = cron_manager._scheduler.get_job("test-scheduler")
        if aps_job:
            logger.info(f"✅ 测试任务已注册")
            logger.info(f"下次运行时间: {aps_job.next_run_time}")
        else:
            logger.error("❌ 测试任务未注册到调度器!")
            return False
        
        # 7. 等待任务执行
        logger.info("\n步骤 7: 等待任务自动执行 (最多等待 90 秒)")
        logger.info("提示: 任务会在下一分钟的开始时执行")
        
        start_time = time.time()
        max_wait = 90  # 最多等待 90 秒
        
        while time.time() - start_time < max_wait:
            # 检查任务状态
            state = cron_manager.get_state_sync("test-scheduler")
            
            if state.last_run_at:
                logger.info(f"\n✅ 任务已执行!")
                logger.info(f"最后执行时间: {state.last_run_at}")
                logger.info(f"执行状态: {state.last_status}")
                if state.last_error:
                    logger.error(f"执行错误: {state.last_error}")
                break
            
            # 每 5 秒打印一次等待信息
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                logger.info(f"等待中... ({elapsed}/{max_wait} 秒)")
            
            time.sleep(1)
        else:
            logger.error(f"\n❌ 任务在 {max_wait} 秒内未执行!")
            logger.error("可能的原因:")
            logger.error("  1. 调度器未正常运行")
            logger.error("  2. 回调函数有问题")
            logger.error("  3. 任务被暂停")
            return False
        
        # 8. 清理测试任务
        logger.info("\n步骤 8: 清理测试任务")
        cron_manager.delete_job_sync("test-scheduler")
        logger.info("✅ 测试任务已删除")
        
        # 9. 停止 CronManager
        logger.info("\n步骤 9: 停止 CronManager")
        cron_manager.stop_sync()
        logger.info("✅ CronManager 已停止")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 测试通过! 定时任务调度器工作正常")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_cron_scheduler()
    sys.exit(0 if success else 1)
