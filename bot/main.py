import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN, DATABASE_PATH, LOG_LEVEL
from db.database import init as init_db
from bot.handlers.lobby import router as lobby_router
from bot.handlers.round import router as round_router
from bot.handlers.settings import router as settings_router
from bot.middlewares.anti_flood import AntiFloodMiddleware


async def main():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(name)-16s | %(levelname)-5s | %(message)s",
    )
    logger = logging.getLogger(__name__)

    init_db(DATABASE_PATH)
    logger.info("Database initialized.")

    # دانلود کلمات همزمان با کار بات (.blocking نیست)
    from db.words import download_words_async
    asyncio.create_task(download_words_async())

    # بدون پروکسی
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    dp.message.middleware(AntiFloodMiddleware(cooldown=0.5))
    dp.callback_query.middleware(AntiFloodMiddleware(cooldown=0.3))

    dp.include_router(lobby_router)
    dp.include_router(settings_router)
    dp.include_router(round_router)

    logger.info("🤖 Bot is starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
