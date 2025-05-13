import asyncio
import logging
import os
from telegram import Bot
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
from config import TELEGRAM_TOKEN, logger
from database import Database
from vk_tracker import VKTracker
import bot_commands
from bot_commands import (
    start_command, help_command, subscribe_command, 
    unsubscribe_command, list_command, settings_command, toggle_command
)

# Инициализация глобальных переменных
vk_tracker = None

async def setup_database():
    """Инициализация базы данных"""
    await Database.init_db()

async def on_startup(application: Application):
    """Функция, выполняемая при запуске бота"""
    global vk_tracker
    
    # Инициализация базы данных
    await setup_database()
    
    # Создание и запуск трекера VK
    vk_tracker = VKTracker(application.bot)
    await vk_tracker.start_tracking()
    
    # Передаем экземпляр VKTracker в модуль bot_commands
    bot_commands.vk_tracker = vk_tracker
    
    logger.info("Бот успешно запущен и готов к работе")

async def on_shutdown(application: Application):
    """Функция, выполняемая при остановке бота"""
    global vk_tracker
    
    # Остановка трекера VK
    if vk_tracker:
        await vk_tracker.stop_tracking()
    
    logger.info("Бот остановлен")

def main():
    """Основная функция для запуска бота"""
    # Проверка наличия токена
    if not TELEGRAM_TOKEN:
        logger.critical("Не указан токен Telegram бота. Остановка запуска.")
        return
    
    # Создание экземпляра приложения
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("toggle", toggle_command))
    
    # Регистрация функций, выполняемых при запуске и остановке бота
    application.post_init = on_startup
    application.post_shutdown = on_shutdown
    
    # Запуск бота в режиме polling
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
