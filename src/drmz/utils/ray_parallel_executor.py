# ⚡ ray_parallel_executor.py
# Ray-based parallel execution for CrewAI flows to speed up processing

import os
import ray
import time
from pathlib import Path
from typing import Callable, Any, Dict, List
from drmz.utils.logger import get_logger

log = get_logger("RayParallelExecutor")


@ray.remote
def execute_task_parallel(task_func: Callable, *args, **kwargs):
    """Ray remote function to execute a task in parallel."""
    try:
        start_time = time.time()
        result = task_func(*args, **kwargs)
        execution_time = time.time() - start_time
        return {
            "success": True,
            "result": result,
            "execution_time": execution_time
        }
    except Exception as e:
        log.exception(f"Error in parallel task execution: {e}")
        return {
            "success": False,
            "error": str(e),
            "result": None
        }


class RayParallelExecutor:
    """Execute CrewAI tasks in parallel using Ray for faster processing."""
    
    def __init__(self, initialize_ray: bool = True):
        """Initialize Ray if not already initialized."""
        self.ray_initialized = False
        if initialize_ray:
            self._init_ray()
    
    def _init_ray(self):
        """Initialize Ray cluster."""
        try:
            if not ray.is_initialized():
                # Check if Ray address is set (for cluster mode)
                if os.environ.get("RAY_ADDRESS"):
                    ray.init(address=os.environ["RAY_ADDRESS"], ignore_reinit_error=True)
                    log.info(f"🔗 Connected to Ray cluster: {os.environ['RAY_ADDRESS']}")
                else:
                    # Local mode - use all available cores
                    ray.init(
                        num_cpus=None,  # Use all available CPUs
                        ignore_reinit_error=True,
                        _temp_dir="/tmp/ray"  # Use /tmp for faster I/O
                    )
                    log.info("🚀 Ray initialized in local mode (all cores)")
                self.ray_initialized = True
            else:
                log.info("✅ Ray already initialized")
                self.ray_initialized = True
        except Exception as e:
            log.warning(f"⚠️ Could not initialize Ray: {e}. Falling back to sequential execution.")
            self.ray_initialized = False
    
    def execute_parallel(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks in parallel using Ray.
        
        Args:
            tasks: List of task dictionaries with:
                - 'func': Callable function to execute
                - 'args': Positional arguments
                - 'kwargs': Keyword arguments
                - 'name': Optional task name for logging
        
        Returns:
            List of results in the same order as input tasks
        """
        if not self.ray_initialized:
            log.warning("Ray not initialized, executing sequentially")
            return self._execute_sequential(tasks)
        
        log.info(f"⚡ Executing {len(tasks)} tasks in parallel with Ray")
        start_time = time.time()
        
        # Create Ray futures for all tasks
        futures = []
        for task in tasks:
            func = task.get('func')
            args = task.get('args', [])
            kwargs = task.get('kwargs', {})
            name = task.get('name', 'unnamed')
            
            future = execute_task_parallel.remote(func, *args, **kwargs)
            futures.append((future, name))
        
        # Wait for all tasks to complete
        results = []
        for future, name in futures:
            try:
                result = ray.get(future, timeout=300)  # 5 minute timeout per task
                results.append(result)
                if result.get('success'):
                    log.info(f"✅ Task '{name}' completed in {result.get('execution_time', 0):.2f}s")
                else:
                    log.error(f"❌ Task '{name}' failed: {result.get('error')}")
            except Exception as e:
                log.exception(f"Error waiting for task '{name}': {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "result": None
                })
        
        total_time = time.time() - start_time
        log.info(f"⚡ Parallel execution completed in {total_time:.2f}s ({len(tasks)} tasks)")
        
        return results
    
    def _execute_sequential(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback sequential execution if Ray is not available."""
        log.info(f"Executing {len(tasks)} tasks sequentially")
        results = []
        for task in tasks:
            try:
                func = task.get('func')
                args = task.get('args', [])
                kwargs = task.get('kwargs', {})
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                results.append({
                    "success": True,
                    "result": result,
                    "execution_time": execution_time
                })
            except Exception as e:
                log.exception(f"Error in sequential task: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "result": None
                })
        return results
    
    def shutdown(self):
        """Shutdown Ray if we initialized it."""
        if self.ray_initialized and ray.is_initialized():
            try:
                ray.shutdown()
                log.info("🛑 Ray shutdown")
            except Exception as e:
                log.warning(f"Error shutting down Ray: {e}")


# Global executor instance (lazy initialization)
_executor = None


def get_ray_executor() -> RayParallelExecutor:
    """Get or create global Ray executor instance."""
    global _executor
    if _executor is None:
        _executor = RayParallelExecutor()
    return _executor

