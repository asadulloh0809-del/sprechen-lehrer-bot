import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
import config
from handlers import router
import database as db

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")
    
    while True:
        await asyncio.sleep(3600)

async def main():
    logging.basicConfig(level=logging.INFO)
    db.init_db()
    
    session = AiohttpSession(timeout=120.0)
    bot = Bot(token=config.BOT_TOKEN, session=session)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    print("Bot ishga tushdi... Telegramda botga yozishingiz mumkin!")
    await bot.delete_webhook(drop_pending_updates=True)
    
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot, polling_timeout=60)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot to'xtatildi.")
