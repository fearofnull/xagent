# -*- coding: utf-8 -*-
"""HTTP API 接口"""
from fastapi import APIRouter, Depends, HTTPException, Request

from .manager import CronManager
from .models import CronJobSpec, CronJobView

router = APIRouter(prefix="/cron", tags=["cron"])


def get_cron_manager(request: Request) -> CronManager:
    """获取 CronManager 实例

    Args:
        request: 请求对象

    Returns:
        CronManager: CronManager 实例

    Raises:
        HTTPException: CronManager 未初始化
    """
    mgr = getattr(request.app.state, "cron_manager", None)
    if mgr is None:
        raise HTTPException(
            status_code=503,
            detail="cron manager not initialized",
        )
    return mgr


@router.get("/jobs", response_model=list[CronJobSpec])
async def list_jobs(mgr: CronManager = Depends(get_cron_manager)):
    """列出所有定时任务"""
    return await mgr.list_jobs()


@router.post("/jobs", response_model=CronJobSpec)
async def create_job(spec: CronJobSpec, mgr: CronManager = Depends(get_cron_manager)):
    """创建定时任务"""
    await mgr.create_or_replace_job(spec)
    return spec


@router.get("/jobs/{job_id}", response_model=CronJobView)
async def get_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    """获取定时任务详情"""
    job = await mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return CronJobView(spec=job, state=mgr.get_state(job_id))


@router.put("/jobs/{job_id}", response_model=CronJobSpec)
async def update_job(job_id: str, spec: CronJobSpec, mgr: CronManager = Depends(get_cron_manager)):
    """更新定时任务"""
    if spec.id != job_id:
        raise HTTPException(status_code=400, detail="job id in path and body must match")
    await mgr.create_or_replace_job(spec)
    return spec


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    """删除定时任务"""
    deleted = await mgr.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="job not found")
    return {"deleted": True}


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    """暂停定时任务"""
    try:
        await mgr.pause_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="job not found") from e
    return {"paused": True}


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    """恢复定时任务"""
    try:
        await mgr.resume_job(job_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="job not found") from e
    return {"resumed": True}


@router.post("/jobs/{job_id}/run")
async def run_job(job_id: str, mgr: CronManager = Depends(get_cron_manager)):
    """立即执行定时任务"""
    try:
        await mgr.run_job(job_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="job not found") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"started": True}
