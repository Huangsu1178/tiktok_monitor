"""
TikTok Monitor - Scheduler Module
基于APScheduler的定时任务调度模块
"""
import sys
import os
from datetime import datetime
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


class MonitorScheduler:
    """TikTok监控定时任务调度器"""

    def __init__(self):
        self._scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self._scheduler.add_listener(self._on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self._status_callback: Optional[Callable] = None
        self._is_running = False

    def set_status_callback(self, callback: Callable):
        """设置状态更新回调函数（用于更新GUI）"""
        self._status_callback = callback

    def _on_job_event(self, event):
        """任务执行事件监听"""
        if event.exception:
            msg = f"[调度器] 任务 {event.job_id} 执行失败: {event.exception}"
        else:
            msg = f"[调度器] 任务 {event.job_id} 执行完成"
        print(msg)
        if self._status_callback:
            self._status_callback(msg)

    def start(self):
        """启动调度器"""
        if not self._is_running:
            self._scheduler.start()
            self._is_running = True
            print("[调度器] 已启动")

    def stop(self):
        """停止调度器"""
        if self._is_running:
            self._scheduler.shutdown(wait=False)
            self._is_running = False
            print("[调度器] 已停止")

    def add_fetch_job(self, job_id: str, fetch_func: Callable,
                      interval_hours: float = 1.0, run_immediately: bool = False):
        """
        添加定时抓取任务
        
        Args:
            job_id: 任务唯一ID（通常使用博主username）
            fetch_func: 抓取函数（无参数）
            interval_hours: 轮询间隔（小时）
            run_immediately: 是否立即执行一次
        """
        # 移除已存在的同名任务
        self.remove_job(job_id)

        self._scheduler.add_job(
            fetch_func,
            trigger=IntervalTrigger(hours=interval_hours),
            id=job_id,
            name=f"TikTok监控: {job_id}",
            replace_existing=True,
            misfire_grace_time=300,  # 允许5分钟的延迟容忍
        )
        print(f"[调度器] 已添加任务: {job_id}, 间隔: {interval_hours}小时")

        if run_immediately:
            fetch_func()

    def add_global_fetch_job(self, fetch_all_func: Callable, interval_hours: float = 1.0):
        """添加全局轮询任务（一次性抓取所有激活的博主）"""
        self.add_fetch_job(
            job_id="global_fetch",
            fetch_func=fetch_all_func,
            interval_hours=interval_hours
        )

    def remove_job(self, job_id: str):
        """移除指定任务"""
        try:
            self._scheduler.remove_job(job_id)
            print(f"[调度器] 已移除任务: {job_id}")
        except Exception:
            pass

    def pause_job(self, job_id: str):
        """暂停指定任务"""
        try:
            self._scheduler.pause_job(job_id)
        except Exception:
            pass

    def resume_job(self, job_id: str):
        """恢复指定任务"""
        try:
            self._scheduler.resume_job(job_id)
        except Exception:
            pass

    def get_jobs_info(self) -> list:
        """获取所有任务信息"""
        jobs = []
        for job in self._scheduler.get_jobs():
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "已暂停"
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run,
            })
        return jobs

    def is_running(self) -> bool:
        return self._is_running

    def update_interval(self, job_id: str, interval_hours: float):
        """更新任务执行间隔"""
        job = self._scheduler.get_job(job_id)
        if job:
            job.reschedule(trigger=IntervalTrigger(hours=interval_hours))
            print(f"[调度器] 任务 {job_id} 间隔已更新为 {interval_hours} 小时")
