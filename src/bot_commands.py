import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from database import Database

logger = logging.getLogger(__name__)

vk_tracker = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Привет! Я бот для отслеживания онлайн-статуса и активности пользователей ВКонтакте.\n\n"
        "📋 *Основные команды:*\n"
        "/subscribe <vk_id или ссылка> - Подписаться на отслеживание пользователя\n"
        "/unsubscribe <vk_id или ссылка> - Отписаться от отслеживания пользователя\n"
        "/settings <vk_id или ссылка> - Настроить параметры отслеживания\n"
        "/list - Показать список отслеживаемых пользователей\n"
        "/help - Показать справку по командам\n\n"
        "🔔 Я буду уведомлять вас об активности указанных пользователей ВКонтакте:\n"
        "• Вход/выход из сети\n"
        "• Новые друзья\n"
        "• Вступление в группы\n"
        "• Новые записи на стене\n"
        "• Лайки\n"
        "• Комментарии\n\n"
        "ℹ️ Вы можете использовать как числовой ID пользователя ВКонтакте, так и ссылку на его профиль в формате vk.com/id12345678 или короткое имя vk.com/username.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📋 *Справка по командам:*\n\n"
        "*/subscribe <vk_id или ссылка>* - Подписаться на отслеживание пользователя ВКонтакте.\n"
        "Примеры:\n"
        "• `/subscribe 12345678`\n"
        "• `/subscribe vk.com/id12345678`\n"
        "• `/subscribe https://vk.com/id12345678`\n"
        "• `/subscribe vk.com/durov`\n\n"
        "*/unsubscribe <vk_id или ссылка>* - Отписаться от отслеживания пользователя ВКонтакте.\n"
        "Примеры:\n"
        "• `/unsubscribe 12345678`\n"
        "• `/unsubscribe vk.com/id12345678`\n"
        "• `/unsubscribe vk.com/durov`\n\n"
        "*/settings <vk_id или ссылка>* - Настроить параметры отслеживания пользователя.\n"
        "Примеры:\n"
        "• `/settings 12345678`\n"
        "• `/settings vk.com/durov`\n\n"
        "*/list* - Показать список всех отслеживаемых вами пользователей ВКонтакте.\n\n"
        "🔔 *Типы отслеживаемой активности:*\n"
        "• Онлайн-статус (вход/выход из сети)\n"
        "• Новые друзья\n"
        "• Вступление в группы\n"
        "• Новые записи на стене\n"
        "• Лайки\n"
        "• Комментарии\n\n"
        "❓ *Как найти пользователя ВКонтакте:*\n"
        "1. Числовой ID: если в адресной строке вида `vk.com/id12345678`\n"
        "2. Короткое имя: если в адресной строке вида `vk.com/username`\n"
        "3. Вы можете просто скопировать и отправить полную ссылку на профиль",
        parse_mode="Markdown"
    )

async def extract_vk_id(input_text):
    """
    Извлечение VK ID из текста, который может быть числом или ссылкой на профиль VK
    Поддерживаемые форматы:
    - Числовой ID: 12345678
    - Ссылка с ID: vk.com/id12345678, https://vk.com/id12345678
    - Короткое имя: vk.com/username (через VK API)
    """
    input_text = input_text.strip()
    
    if input_text.isdigit():
        return int(input_text)
    
    # Регулярное выражение для поиска ID в формате vk.com/id12345678 или https://vk.com/id12345678
    id_pattern = re.compile(r'(?:https?://)?vk\.com/id(\d+)', re.IGNORECASE)
    match = id_pattern.search(input_text)
    if match:
        return int(match.group(1))
    
    # Для коротких имен пользуемся методом resolve_username из VKTracker
    if vk_tracker:
        # Определяем, что это ссылка на VK
        if re.search(r'(?:https?://)?vk\.com/\w+', input_text, re.IGNORECASE):
            # Пробуем разрешить короткое имя через API VK
            vk_id = await vk_tracker.resolve_username(input_text)
            if vk_id:
                return int(vk_id)
    
    # Если не удалось определить ID, возвращаем None
    return None

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /subscribe <vk_id> или /subscribe <ссылка>"""
    # Проверка аргументов
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Ошибка: Не указан VK ID или ссылка на профиль пользователя.\n"
            "Правильные форматы:\n"
            "• `/subscribe 12345678`\n"
            "• `/subscribe vk.com/id12345678`\n"
            "• `/subscribe https://vk.com/id12345678`\n"
            "• `/subscribe vk.com/username`",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Объединяем все аргументы в одну строку, чтобы обработать полную ссылку
        input_text = " ".join(context.args)
        
        # Пытаемся извлечь VK ID из текста
        vk_id = await extract_vk_id(input_text)
        
        # Если не удалось извлечь ID
        if vk_id is None:
            await update.message.reply_text(
                "❌ Не удалось определить VK ID из указанного текста.\n"
                "Поддерживаемые форматы:\n"
                "• Числовой ID: `12345678`\n"
                "• Ссылка с ID: `vk.com/id12345678`\n"
                "• Короткое имя: `vk.com/username`\n\n"
                "Убедитесь, что профиль пользователя существует и доступен.",
                parse_mode="Markdown"
            )
            return
        
        chat_id = update.effective_chat.id
        
        # Добавление подписки в базу данных
        success = await Database.add_subscription(chat_id, vk_id)
        
        if success:
            # Инициализация настроек мониторинга (по умолчанию только онлайн-статус)
            await Database.init_monitoring_settings(chat_id, vk_id)
            
            await update.message.reply_text(
                f"✅ Вы успешно подписались на отслеживание пользователя с VK ID: {vk_id}.\n"
                f"По умолчанию отслеживается только онлайн-статус.\n\n"
                f"Чтобы настроить отслеживание дополнительной активности, используйте команду:\n"
                f"`/settings {vk_id}`",
                parse_mode="Markdown"
            )
            logger.info(f"Пользователь {chat_id} подписался на отслеживание VK ID {vk_id}")
        else:
            await update.message.reply_text(
                f"❌ Произошла ошибка при подписке на пользователя с VK ID: {vk_id}."
            )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды subscribe: {e}")
        await update.message.reply_text(
            "❌ Произошла непредвиденная ошибка при обработке вашего запроса."
        )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /unsubscribe <vk_id> или /unsubscribe <ссылка>"""
    # Проверка аргументов
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Ошибка: Не указан VK ID или ссылка на профиль пользователя.\n"
            "Правильные форматы:\n"
            "• `/unsubscribe 12345678`\n"
            "• `/unsubscribe vk.com/id12345678`\n"
            "• `/unsubscribe https://vk.com/id12345678`\n"
            "• `/unsubscribe vk.com/username`",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Объединяем все аргументы в одну строку, чтобы обработать полную ссылку
        input_text = " ".join(context.args)
        
        # Пытаемся извлечь VK ID из текста
        vk_id = await extract_vk_id(input_text)
        
        # Если не удалось извлечь ID
        if vk_id is None:
            await update.message.reply_text(
                "❌ Не удалось определить VK ID из указанного текста.\n"
                "Поддерживаемые форматы:\n"
                "• Числовой ID: `12345678`\n"
                "• Ссылка с ID: `vk.com/id12345678`\n"
                "• Короткое имя: `vk.com/username`\n\n"
                "Убедитесь, что профиль пользователя существует и доступен.",
                parse_mode="Markdown"
            )
            return
        
        chat_id = update.effective_chat.id
        
        # Проверка, есть ли такая подписка
        subscriptions = await Database.get_subscriptions(chat_id)
        if vk_id not in subscriptions:
            await update.message.reply_text(
                f"⚠️ Вы не подписаны на отслеживание пользователя с VK ID: {vk_id}."
            )
            return
        
        # Удаление подписки из базы данных
        success = await Database.remove_subscription(chat_id, vk_id)
        
        if success:
            await update.message.reply_text(
                f"✅ Вы успешно отписались от отслеживания пользователя с VK ID: {vk_id}."
            )
            logger.info(f"Пользователь {chat_id} отписался от отслеживания VK ID {vk_id}")
        else:
            await update.message.reply_text(
                f"❌ Произошла ошибка при отписке от пользователя с VK ID: {vk_id}."
            )
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды unsubscribe: {e}")
        await update.message.reply_text(
            "❌ Произошла непредвиденная ошибка при обработке вашего запроса."
        )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /list"""
    try:
        chat_id = update.effective_chat.id
        
        # Получение списка отслеживаемых VK ID
        subscriptions = await Database.get_subscriptions(chat_id)
        
        if not subscriptions:
            await update.message.reply_text(
                "📋 У вас нет активных подписок на отслеживание пользователей ВКонтакте.\n"
                "Чтобы подписаться, используйте команду `/subscribe <vk_id или ссылка>`",
                parse_mode="Markdown"
            )
            return
        
        # Формирование списка подписок
        subscription_list = "\n".join([f"• VK ID: {vk_id}" for vk_id in subscriptions])
        
        await update.message.reply_text(
            f"📋 *Список отслеживаемых пользователей ВКонтакте:*\n\n"
            f"{subscription_list}\n\n"
            f"Всего подписок: {len(subscriptions)}\n\n"
            f"Для настройки параметров отслеживания используйте команду:\n"
            f"`/settings <vk_id>`",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды list: {e}")
        await update.message.reply_text(
            "❌ Произошла непредвиденная ошибка при обработке вашего запроса."
        )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /settings <vk_id> или /settings <ссылка>"""
    # Проверка аргументов
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Ошибка: Не указан VK ID или ссылка на профиль пользователя.\n"
            "Правильные форматы:\n"
            "• `/settings 12345678`\n"
            "• `/settings vk.com/id12345678`\n"
            "• `/settings vk.com/username`",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Объединяем все аргументы в одну строку, чтобы обработать полную ссылку
        input_text = " ".join(context.args)
        
        # Пытаемся извлечь VK ID из текста
        vk_id = await extract_vk_id(input_text)
        
        # Если не удалось извлечь ID
        if vk_id is None:
            await update.message.reply_text(
                "❌ Не удалось определить VK ID из указанного текста.\n"
                "Поддерживаемые форматы:\n"
                "• Числовой ID: `12345678`\n"
                "• Ссылка с ID: `vk.com/id12345678`\n"
                "• Короткое имя: `vk.com/username`\n\n"
                "Убедитесь, что профиль пользователя существует и доступен.",
                parse_mode="Markdown"
            )
            return
        
        chat_id = update.effective_chat.id
        
        # Проверка, есть ли такая подписка
        subscriptions = await Database.get_subscriptions(chat_id)
        if vk_id not in subscriptions:
            await update.message.reply_text(
                f"⚠️ Вы не подписаны на отслеживание пользователя с VK ID: {vk_id}.\n"
                f"Сначала подпишитесь с помощью команды `/subscribe {vk_id}`",
                parse_mode="Markdown"
            )
            return
        
        # Получение текущих настроек мониторинга
        settings = await Database.get_monitoring_settings(chat_id, vk_id)
        
        # Если настройки не были найдены, инициализируем их
        if not settings:
            await Database.init_monitoring_settings(chat_id, vk_id)
            settings = await Database.get_monitoring_settings(chat_id, vk_id)
        
        # Подготовка сообщения с текущими настройками отслеживания
        settings_text = f"⚙️ *Настройки отслеживания для VK ID {vk_id}:*\n\n"
        settings_text += f"1. Онлайн-статус: {'✅ Включено' if settings['track_online'] else '❌ Выключено'}\n"
        settings_text += f"2. Новые друзья: {'✅ Включено' if settings['track_friends'] else '❌ Выключено'}\n"
        settings_text += f"3. Вступление в группы: {'✅ Включено' if settings['track_groups'] else '❌ Выключено'}\n"
        settings_text += f"4. Новые записи на стене: {'✅ Включено' if settings['track_posts'] else '❌ Выключено'}\n"
        settings_text += f"5. Лайки: {'✅ Включено' if settings['track_likes'] else '❌ Выключено'}\n"
        settings_text += f"6. Комментарии: {'✅ Включено' if settings['track_comments'] else '❌ Выключено'}\n\n"
        settings_text += "Для изменения настроек отправьте: `/toggle {vk_id} N`, где N - номер настройки (1-6).\n\n"
        settings_text += "Например, чтобы включить/выключить отслеживание новых друзей, отправьте:\n"
        settings_text += f"`/toggle {vk_id} 2`"
        
        await update.message.reply_text(
            settings_text,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды settings: {e}")
        await update.message.reply_text(
            "❌ Произошла непредвиденная ошибка при обработке вашего запроса."
        )

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /toggle <vk_id> <setting_number>"""
    # Проверка аргументов
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Ошибка: Неверный формат команды.\n"
            "Правильный формат: `/toggle <vk_id> <номер_настройки>`\n\n"
            "Где номер настройки (1-6):\n"
            "1. Онлайн-статус\n"
            "2. Новые друзья\n"
            "3. Вступление в группы\n"
            "4. Новые записи на стене\n"
            "5. Лайки\n"
            "6. Комментарии",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Извлекаем VK ID и номер настройки
        if len(context.args) == 2 and context.args[0].isdigit() and context.args[1].isdigit():
            vk_id = int(context.args[0])
            setting_number = int(context.args[1])
        else:
            # Если первый аргумент не числовой, пробуем извлечь VK ID
            vk_id_text = context.args[0]
            vk_id = await extract_vk_id(vk_id_text)
            if vk_id is None:
                await update.message.reply_text(
                    "❌ Не удалось определить VK ID из указанного текста."
                )
                return
                
            # Пробуем извлечь номер настройки из второго аргумента
            try:
                setting_number = int(context.args[1])
            except ValueError:
                await update.message.reply_text(
                    "❌ Некорректный номер настройки. Должно быть число от 1 до 6."
                )
                return
        
        # Проверка корректности номера настройки
        if setting_number < 1 or setting_number > 6:
            await update.message.reply_text(
                "❌ Некорректный номер настройки. Должно быть число от 1 до 6."
            )
            return
        
        chat_id = update.effective_chat.id
        
        # Проверка, есть ли такая подписка
        subscriptions = await Database.get_subscriptions(chat_id)
        if vk_id not in subscriptions:
            await update.message.reply_text(
                f"⚠️ Вы не подписаны на отслеживание пользователя с VK ID: {vk_id}."
            )
            return
        
        # Получение текущих настроек мониторинга
        settings = await Database.get_monitoring_settings(chat_id, vk_id)
        
        # Если настройки не были найдены, инициализируем их
        if not settings:
            await Database.init_monitoring_settings(chat_id, vk_id)
            settings = await Database.get_monitoring_settings(chat_id, vk_id)
        
        # Определение ключа настройки по номеру
        setting_keys = [
            "track_online",
            "track_friends",
            "track_groups",
            "track_posts",
            "track_likes",
            "track_comments"
        ]
        
        setting_key = setting_keys[setting_number - 1]
        
        # Инвертируем значение настройки
        new_value = not settings[setting_key]
        
        # Обновляем настройку в базе данных
        success = await Database.update_monitoring_settings(chat_id, vk_id, {setting_key: int(new_value)})
        
        if success:
            setting_names = [
                "Онлайн-статус",
                "Новые друзья",
                "Вступление в группы",
                "Новые записи на стене",
                "Лайки",
                "Комментарии"
            ]
            
            setting_name = setting_names[setting_number - 1]
            status = "включено" if new_value else "выключено"
            
            await update.message.reply_text(
                f"✅ Настройка '{setting_name}' для пользователя с VK ID {vk_id} {status}.\n\n"
                f"Для просмотра всех настроек используйте команду:\n"
                f"`/settings {vk_id}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"❌ Произошла ошибка при обновлении настроек для пользователя с VK ID: {vk_id}."
            )
            
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды toggle: {e}")
        await update.message.reply_text(
            "❌ Произошла непредвиденная ошибка при обработке вашего запроса."
        )