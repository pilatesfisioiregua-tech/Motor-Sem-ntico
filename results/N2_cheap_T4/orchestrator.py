import asyncio
import logging
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 5
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff base
TIMEOUT_SECONDS = 60

# --- Data Models ---

@dataclass
class Task:
    model_id: str
    prompt: str
    max_tokens: int

@dataclass
class Result:
    task: Task
    status: str  # "ok" or "error"
    response: Optional[Dict[str, Any]]
    error_message: Optional[str]
    latency_ms: float
    retries_used: int

# --- Core Logic ---

async def _execute_single_task(
    session: ClientSession,
    semaphore: asyncio.Semaphore,
    task: Task,
    endpoint: str,
    api_key: str
) -> Result:
    """
    Executes a single task with retry logic and semaphore control.
    """
    start_time = time.perf_counter()
    
    async with semaphore:  # Rate limiting gate
        for attempt in range(MAX_RETRIES + 1):
            try:
                # Prepare request
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": task.model_id,
                    "prompt": task.prompt,
                    "max_tokens": task.max_tokens
                }

                # Execute request
                async with session.post(
                    endpoint, 
                    json=payload, 
                    headers=headers,
                    timeout=ClientTimeout(total=TIMEOUT_SECONDS)
                ) as response:
                    
                    # Check for HTTP errors (4xx, 5xx)
                    if response.status >= 400:
                        error_text = await response.text()
                        raise ClientError(f"HTTP {response.status}: {error_text}")

                    data = await response.json()
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    
                    return Result(
                        task=task,
                        status="ok",
                        response=data,
                        error_message=None,
                        latency_ms=latency_ms,
                        retries_used=attempt
                    )

            except (asyncio.TimeoutError, ClientError) as e:
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAYS[attempt]
                    logger.warning(
                        f"Task failed (attempt {attempt + 1}/{MAX_RETRIES + 1}): {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    # Final failure
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    logger.error(f"Task failed permanently after {MAX_RETRIES} retries: {str(e)}")
                    return Result(
                        task=task,
                        status="error",
                        response=None,
                        error_message=str(e),
                        latency_ms=latency_ms,
                        retries_used=attempt
                    )

async def orchestrate(
    tasks: List[Task], 
    endpoint: str, 
    api_key: str
) -> List[Result]:
    """
    Main entry point: Orchestrates parallel execution of tasks.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # Create a single session for all requests
    async with ClientSession() as session:
        # Create tasks for asyncio.gather
        coroutines = [
            _execute_single_task(session, semaphore, task, endpoint, api_key)
            for task in tasks
        ]
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        # Post-process results to handle unexpected exceptions
        final_results: List[Result] = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                # This catches unexpected errors in the coroutine itself
                logger.error(f"Unexpected error in task {i}: {res}")
                final_results.append(Result(
                    task=tasks[i],
                    status="error",
                    response=None,
                    error_message=str(res),
                    latency_ms=0.0,
                    retries_used=0
                ))
            else:
                final_results.append(res)
                
        return final_results