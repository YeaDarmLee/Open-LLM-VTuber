import asyncio
import time
import random
from loguru import logger
from typing import Callable, Coroutine, Any

from ..config_manager.idle import IdleTalkConfig

class IdleScheduler:
    """Schedules idle talk events when the chat is quiet."""

    def __init__(
        self,
        config: IdleTalkConfig,
        trigger_callback: Callable[[], Coroutine[Any, Any, None]]
    ):
        self.config = config
        self.trigger_callback = trigger_callback
        self.last_activity = time.time()
        self.last_idle_talk = 0.0
        self.task: asyncio.Task | None = None
        self._running = False
        self.current_delay = 0.0
        self._reset_delay()

    def update_activity(self):
        """Update the last activity timestamp to prevent idle triggers."""
        # Reset the timer
        self.last_activity = time.time()
        self._reset_delay()

    def _reset_delay(self):
        self.current_delay = random.uniform(self.config.min_delay, self.config.max_delay)

    def start(self):
        """Start the background scheduler task."""
        if not self.config.enabled:
            return
        logger.info(f"IdleScheduler starting. min_delay={self.config.min_delay}, max_delay={self.config.max_delay}, cooldown={self.config.cooldown}")
        self._running = True
        self.last_activity = time.time()
        self._reset_delay()
        self.task = asyncio.create_task(self._loop())

    def stop(self):
        """Stop the background scheduler task."""
        self._running = False
        if self.task and not self.task.done():
            self.task.cancel()
        self.task = None
        logger.debug("IdleScheduler stopped.")

    async def _loop(self):
        # Initial sleep just to prevent starting immediately
        await asyncio.sleep(5.0)
        
        while self._running:
            # Check every 2 seconds to be responsive
            await asyncio.sleep(2.0)
            
            now = time.time()

            if now - self.last_activity >= self.current_delay:
                # We reached the delay. Check cooldown.
                if now - self.last_idle_talk >= self.config.cooldown:
                    # Roll probability
                    if random.random() < self.config.probability:
                        logger.info("Idle talk triggered.")
                        self.last_idle_talk = time.time()
                        self.update_activity() # reset activity and delay
                        
                        try:
                            # Fire and forget the callback
                            asyncio.create_task(self.trigger_callback())
                        except Exception as e:
                            logger.error(f"Error in idle talk trigger callback: {e}")
                    else:
                        logger.debug("Idle talk probability check failed, staying silent.")
                        self.update_activity()
                else:
                    # In cooldown. We should wait at least until cooldown is over.
                    self.update_activity()
