# app/telegram/bot_listener.py

import asyncio
import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    Application,
    filters,
)
from telegram import Update
from app.agent.agent__telegram_assistant import TelegramAssistant
from app.bootstrap.bootstrap__postgres import BootstrapPostgres
from app.core.config import Config, get_config



class TelegramAssistantListener:
    def __init__(self, cfg: Config, db: BootstrapPostgres):
        self.token = cfg.TELEGRAM_BOT_TOKEN
        self.app: Application = ApplicationBuilder().token(self.token).build()

        self.agent = TelegramAssistant(cfg.LLM_GENERAL_MODEL, cfg.LLM_MODE, cfg.LLM_API_BASE_URL, cfg.LLM_API_API_KEY, cfg.SERPAPI_API_KEY, db)

        self._setup_handlers()

    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Halo! Saya adalah asisten AI.\n\n"
            "Ketik perintah seperti:\n"
            "- mencari riset tentang topik tertentu\n"
            "- analisa kesehatan berdasarkan keluhan Anda"
        )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        response = self.agent.handle_command(user_input)
        await update.message.reply_text(response)

    async def run(self):
        await self.app.initialize()  # Init internal stuff
        await self.app.start()       # Start the application
        await self.app.updater.start_polling()

        try:
            while True:
                await asyncio.sleep(3600)  # loop forever, or until stopped externally
        finally:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
