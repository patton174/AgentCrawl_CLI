import concurrent.futures
from typing import Callable, Any, Dict
import threading
from ai_crawler_cli.utils.logger import log

class ThreadManager:
    """Manages thread pools and lifecycle of background workers."""
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.futures: Dict[concurrent.futures.Future, str] = {}
        self._lock = threading.Lock()

    def submit_task(self, task_id: str, fn: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit a task to the thread pool."""
        log.info(f"Submitting task {task_id}")
        future = self.executor.submit(fn, *args, **kwargs)
        with self._lock:
            self.futures[future] = task_id
            
        # Add callback for completion
        future.add_done_callback(self._task_done)
        return future

    def _task_done(self, future: concurrent.futures.Future):
        with self._lock:
            task_id = self.futures.pop(future, "Unknown")
            
        try:
            result = future.result()
            log.info(f"Task {task_id} completed successfully.")
        except Exception as e:
            log.error(f"Task {task_id} failed with exception: {e}")

    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool gracefully."""
        log.info("Shutting down ThreadManager...")
        self.executor.shutdown(wait=wait)
        log.info("ThreadManager shutdown complete.")

# Global thread manager
thread_manager = ThreadManager()
