import time
import threading
from typing import Callable, Dict, Any, List
from ai_crawler_cli.utils.logger import log
from ai_crawler_cli.core.thread_manager import thread_manager
import uuid

class Task:
    def __init__(self, fn: Callable, interval_seconds: int, args: tuple = (), kwargs: dict = None):
        self.id = str(uuid.uuid4())
        self.fn = fn
        self.interval = interval_seconds
        self.args = args
        self.kwargs = kwargs or {}
        self.last_run = 0.0
        self.active = True

class CustomScheduler:
    def __init__(self):
        self.tasks: List[Task] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        
    def start(self):
        log.info("Starting CustomScheduler...")
        self._thread.start()
        
    def stop(self):
        log.info("Stopping CustomScheduler...")
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join()

    def add_job(self, fn: Callable, interval_seconds: int, *args, **kwargs) -> str:
        task = Task(fn, interval_seconds, args, kwargs)
        with self._lock:
            self.tasks.append(task)
        log.info(f"Added scheduled job {task.id} running every {interval_seconds}s")
        return task.id

    def remove_job(self, task_id: str):
        with self._lock:
            self.tasks = [t for t in self.tasks if t.id != task_id]
        log.info(f"Removed job {task_id}")

    def _run_loop(self):
        while not self._stop_event.is_set():
            now = time.time()
            with self._lock:
                for task in self.tasks:
                    if task.active and (now - task.last_run >= task.interval):
                        task.last_run = now
                        log.debug(f"Scheduler dispatching task {task.id}")
                        thread_manager.submit_task(f"sched_{task.id}", task.fn, *task.args, **task.kwargs)
            # Sleep briefly to prevent high CPU usage
            time.sleep(1)

# Global scheduler
scheduler = CustomScheduler()
