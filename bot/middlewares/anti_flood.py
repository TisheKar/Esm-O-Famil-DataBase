import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class AntiFloodMiddleware(BaseMiddleware):
    """Simple per-user cooldown (seconds)."""

    def __init__(self, cooldown: float = 0.5):
        super().__init__()
        self.cooldown = cooldown
        self._last: dict[int, float] = {}

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = time.time()

        if now - self._last.get(user_id, 0) < self.cooldown:
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ کمی صبر کنید.", show_alert=False)
            return None

        self._last[user_id] = now
        return await handler(event, data)
