import asyncio
import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class LobbyScheduler:
    """ manages lobby countdown timers (one per game) """

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    async def start(
        self,
        game_id: str,
        timeout: int,
        warning_at: int,
        on_warning: Callable[[], Awaitable[None]],
        on_expire: Callable[[], Awaitable[None]],
    ) -> None:
        self.cancel(game_id)
        task = asyncio.create_task(
            self._run(game_id, timeout, warning_at, on_warning, on_expire)
        )
        self._tasks[game_id] = task

    def cancel(self, game_id: str) -> None:
        task = self._tasks.pop(game_id, None)
        if task and not task.done():
            task.cancel()

    async def _run(self, game_id, timeout, warning_at, on_warning, on_expire):
        try:
            await asyncio.sleep(warning_at)
            await on_warning()
            await asyncio.sleep(timeout - warning_at)
            await on_expire()
        except asyncio.CancelledError:
            logger.debug("Lobby timer cancelled: %s", game_id)
        except Exception:
            logger.exception("Lobby timer error: %s", game_id)
        finally:
            self._tasks.pop(game_id, None)
