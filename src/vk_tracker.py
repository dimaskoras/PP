import asyncio
import logging
import os
import time
import vk_api
from vk_api.exceptions import ApiError, AuthError
from config import (
    VK_LOGIN, VK_PASSWORD, VK_SERVICE_TOKEN, VK_APP_ID,
    VK_CLIENT_SECRET, POLLING_INTERVAL, format_time, ADMIN_CHAT_ID
)
from database import Database

logger = logging.getLogger(__name__)

# Получаем пользовательский токен из переменных окружения
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN", "")

class VKTracker:
    """Класс для отслеживания онлайн-статуса пользователей VK"""

    def __init__(self, bot):
        self.bot = bot
        self.vk_session = None
        self.vk = None
        self.tracking_task = None
        self.activity_tracking_task = None  # Задача для отслеживания активности
        self.is_running = False

    async def send_notification(self, chat_id, message, disable_preview=False):
        """Вспомогательный метод для отправки уведомлений с корректным отображением ссылок"""
        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    disable_web_page_preview=disable_preview,
                    parse_mode=None  # Используем plain text для корректного отображения ссылок
                )
                return  # Если успешно отправлено, выходим
            except Exception as e:
                if "Flood control" in str(e) and attempt < max_retries - 1:
                    # Извлекаем время ожидания из сообщения об ошибке
                    try:
                        # Пробуем извлечь число секунд из сообщения "Retry in X seconds"
                        retry_seconds = int(str(e).split("Retry in ")[1].split(" ")[0])
                    except:
                        retry_seconds = retry_delay

                    logger.warning(f"Превышен лимит отправки сообщений. Повторная попытка через {retry_seconds} секунд")
                    await asyncio.sleep(retry_seconds)
                else:
                    logger.error(f"Ошибка при отправке уведомления пользователю {chat_id}: {e}")
                    if attempt == max_retries - 1:
                        # Если это последняя попытка, пытаемся отправить упрощенное сообщение
                        try:
                            simple_message = f"Уведомление о пользователе VK (ошибка отображения полного сообщения)"
                            await self.bot.send_message(
                                chat_id=chat_id,
                                text=simple_message
                            )
                            logger.info(f"Отправлено упрощенное уведомление пользователю {chat_id}")
                        except Exception as simple_err:
                            logger.error(f"Не удалось отправить даже упрощенное уведомление: {simple_err}")
                    break

    async def resolve_username(self, username):
        """Преобразование короткого имени пользователя VK в числовой ID

        Аргументы:
            username (str): Короткое имя пользователя (например, 'durov')

        Возвращает:
            int: Числовой ID пользователя VK или None в случае ошибки
        """
        if not self.vk:
            if not await self.authenticate():
                return None

        try:
            # Удаляем префикс 'https://' и 'vk.com/' если они есть
            if '://' in username:
                username = username.split('://', 1)[1]
            if 'vk.com/' in username:
                username = username.split('vk.com/', 1)[1]

            # Если остался префикс 'id' и далее идут цифры, сразу возвращаем ID
            if username.startswith('id') and username[2:].isdigit():
                return int(username[2:])

            # Делаем запрос к API
            logger.info(f"Резолвинг короткого имени: {username}")
            result = await asyncio.to_thread(
                self.vk.users.get,
                user_ids=username,
                v="5.131"
            )

            if result and len(result) > 0:
                return result[0]['id']
            else:
                logger.warning(f"Не удалось получить ID для имени: {username}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при резолвинге короткого имени: {e}")
            return None

    async def authenticate(self):
        """Аутентификация в VK API"""
        try:
            # Пробуем сначала пользовательский токен (имеет больше всего прав)
            if VK_USER_TOKEN:
                logger.info("Авторизация через пользовательский токен")
                self.vk_session = await asyncio.to_thread(
                    vk_api.VkApi, token=VK_USER_TOKEN
                )
            # Потом пробуем сервисный токен
            elif VK_SERVICE_TOKEN:
                logger.info("Авторизация через service token")
                self.vk_session = await asyncio.to_thread(
                    vk_api.VkApi, token=VK_SERVICE_TOKEN
                )
            # Если нет токенов, используем логин/пароль
            elif VK_LOGIN and VK_PASSWORD:
                logger.info("Авторизация через логин/пароль")
                # Используем асинхронный запуск синхронной функции vk_api
                # Используем Kate Mobile app_id для расширенных прав
                self.vk_session = await asyncio.to_thread(
                    vk_api.VkApi,
                    login=VK_LOGIN,
                    password=VK_PASSWORD,
                    app_id=2685278  # Kate Mobile app_id
                )
                # Авторизация
                await asyncio.to_thread(self.vk_session.auth)
            else:
                logger.error("Не заданы параметры аутентификации VK API")
                if ADMIN_CHAT_ID:
                    await self.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text="❌ Ошибка: Не заданы параметры аутентификации VK API"
                    )
                return False

            self.vk = self.vk_session.get_api()
            # Проверка работоспособности
            await asyncio.to_thread(
                self.vk.users.get
            )
            logger.info("Успешная авторизация в VK API")
            return True

        except AuthError as e:
            logger.error(f"Ошибка авторизации VK API: {e}")
            if ADMIN_CHAT_ID:
                await self.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"❌ Ошибка авторизации VK API: {e}"
                )
            return False
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при авторизации VK API: {e}")
            if ADMIN_CHAT_ID:
                await self.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"❌ Непредвиденная ошибка при авторизации VK API: {e}"
                )
            return False

    async def start_tracking(self):
        """Запуск отслеживания онлайн-статуса и активности"""
        if self.is_running:
            return

        # Аутентификация в VK API
        if not await self.authenticate():
            return

        self.is_running = True
        self.tracking_task = asyncio.create_task(self._track_online_status())
        self.activity_tracking_task = asyncio.create_task(self._track_user_activity())
        logger.info("Запущено отслеживание онлайн-статуса и активности пользователей VK")

    async def stop_tracking(self):
        """Остановка отслеживания онлайн-статуса и активности"""
        if not self.is_running:
            return

        self.is_running = False
        if self.tracking_task:
            self.tracking_task.cancel()
            try:
                await self.tracking_task
            except asyncio.CancelledError:
                pass

        if self.activity_tracking_task:
            self.activity_tracking_task.cancel()
            try:
                await self.activity_tracking_task
            except asyncio.CancelledError:
                pass

        logger.info("Остановлено отслеживание онлайн-статуса и активности пользователей VK")

    async def _track_online_status(self):
        """Основной цикл отслеживания онлайн-статуса"""
        while self.is_running:
            try:
                # Получение списка отслеживаемых VK ID
                vk_ids = await Database.get_all_tracked_vk_ids()

                if not vk_ids:
                    # Если нет отслеживаемых пользователей, пропускаем цикл
                    await asyncio.sleep(POLLING_INTERVAL)
                    continue

                # Разбиваем список на группы по 100 ID (лимит VK API)
                for i in range(0, len(vk_ids), 100):
                    batch = vk_ids[i:i+100]
                    await self._process_batch(batch)

                # Ожидание перед следующим опросом
                await asyncio.sleep(POLLING_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка при отслеживании онлайн-статуса: {e}")
                await asyncio.sleep(10)  # В случае ошибки, ждем 10 секунд

    async def _process_batch(self, vk_ids):
        """Обработка группы VK ID (не более 100)"""
        try:
            # Запрос к VK API для получения статуса пользователей
            vk_ids_str = ','.join(map(str, vk_ids))
            users_info = await asyncio.to_thread(
                self.vk.users.get,
                user_ids=vk_ids_str,
                fields="online,last_seen",
                v="5.131"
            )

            # Обработка полученной информации
            current_time = int(time.time())
            for user in users_info:
                vk_id = user.get('id')
                online = user.get('online', 0)
                last_seen = user.get('last_seen', {}).get('time', current_time) if not online else current_time

                # Получение предыдущего статуса
                prev_status = await Database.get_user_status(vk_id)

                # Если статус изменился или это первый запрос
                if not prev_status or prev_status['online'] != online:
                    # Обновление статуса в базе данных
                    await Database.update_user_status(vk_id, online, last_seen)

                    # Если это не первый запрос, отправляем уведомления
                    if prev_status:
                        await self._send_status_change_notifications(vk_id, online, last_seen)

        except ApiError as e:
            if e.code == 6:  # Too many requests
                logger.warning("Слишком много запросов к VK API. Ожидание 10 секунд.")
                await asyncio.sleep(10)
            elif e.code == 5:  # User authorization failed
                logger.error(f"Ошибка авторизации VK API: {e}")
                if ADMIN_CHAT_ID:
                    await self.bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        text=f"❌ Ошибка авторизации VK API: {e}"
                    )
                # Пробуем переавторизоваться
                await self.authenticate()
            else:
                logger.error(f"Ошибка API VK: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке статусов: {e}")

    async def _send_status_change_notifications(self, vk_id, online, last_seen):
        """Отправка уведомлений подписчикам о изменении статуса"""
        # Получение списка Telegram chat_id, подписанных на этого пользователя
        subscribers = await Database.get_subscribers_for_vk_id(vk_id)

        if not subscribers:
            return

        # Получаем имя и фамилию пользователя
        try:
            user_info = await asyncio.to_thread(
                self.vk.users.get,
                user_ids=str(vk_id),
                v="5.131"
            )
            if user_info and len(user_info) > 0:
                first_name = user_info[0].get('first_name', '')
                last_name = user_info[0].get('last_name', '')
                user_name = f"{first_name} {last_name}".strip()
            else:
                user_name = f"VK ID {vk_id}"
        except Exception as e:
            logger.error(f"Ошибка при получении имени пользователя {vk_id}: {e}")
            user_name = f"VK ID {vk_id}"

        # Формирование сообщения
        time_str = format_time(last_seen)
        if online:
            message = f"👤 Пользователь {user_name} вошёл в сеть в {time_str}"
        else:
            message = f"👤 Пользователь {user_name} вышел из сети в {time_str}"

        # Отправка уведомлений всем подписчикам
        for chat_id in subscribers:
            await self.send_notification(chat_id, message, disable_preview=True)

    async def _track_user_activity(self):
        """Основной цикл отслеживания активности пользователей (друзья, группы, посты, лайки, комментарии)"""
        # Интервал для проверки активности (раз в 5 минут)
        ACTIVITY_INTERVAL = 300

        while self.is_running:
            try:
                # Получение списка пользователей с включенным отслеживанием активности
                vk_ids = await Database.get_users_with_activity_tracking()

                if not vk_ids:
                    # Если нет пользователей для отслеживания активности, пропускаем цикл
                    await asyncio.sleep(ACTIVITY_INTERVAL)
                    continue

                # Получаем текущее время для записи в базу данных
                current_time = int(time.time())

                # Обрабатываем каждого пользователя индивидуально
                for vk_id in vk_ids:
                    await self._process_user_activity(vk_id, current_time)

                # Ожидание перед следующей проверкой
                await asyncio.sleep(ACTIVITY_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка при отслеживании активности: {e}")
                await asyncio.sleep(30)  # В случае ошибки, ждем 30 секунд

    async def _process_user_activity(self, vk_id, current_time):
        """Обработка активности для одного пользователя"""
        try:
            # Проверяем каждый тип активности
            await self._check_friends(vk_id, current_time)
            await self._check_groups(vk_id, current_time)
            await self._check_wall_posts(vk_id, current_time)
            await self._check_likes(vk_id, current_time)
            await self._check_comments(vk_id, current_time)

        except ApiError as e:
            if e.code == 6:  # Too many requests
                logger.warning("Слишком много запросов к VK API. Ожидание 10 секунд.")
                await asyncio.sleep(10)
            elif e.code == 5:  # User authorization failed
                logger.error(f"Ошибка авторизации VK API при отслеживании активности: {e}")
                await self.authenticate()
            else:
                logger.error(f"Ошибка API VK при отслеживании активности: {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при отслеживании активности для {vk_id}: {e}")

    async def _check_friends(self, vk_id, current_time):
        """Проверка новых друзей пользователя"""
        # Получаем подписчиков, которые хотят отслеживать друзей
        subscribers = await Database.get_subscribers_with_tracking(vk_id, "track_friends")
        if not subscribers:
            return

        try:
            # Запрос к VK API для получения списка друзей
            friends_response = await asyncio.to_thread(
                self.vk.friends.get,
                user_id=vk_id,
                v="5.131"
            )

            # Проверяем, что ответ содержит друзей
            if friends_response and 'items' in friends_response:
                friend_ids = friends_response['items']

                # Обновляем список друзей и получаем новых
                new_friends = await Database.update_friends(vk_id, friend_ids, current_time)

                # Если есть новые друзья, отправляем уведомления
                if new_friends:
                    await self._send_new_friends_notifications(vk_id, new_friends, subscribers)

        except Exception as e:
            logger.error(f"Ошибка при проверке друзей пользователя {vk_id}: {e}")

    async def _check_groups(self, vk_id, current_time):
        """Проверка новых групп пользователя"""
        # Получаем подписчиков, которые хотят отслеживать группы
        subscribers = await Database.get_subscribers_with_tracking(vk_id, "track_groups")
        if not subscribers:
            return

        try:
            # Запрос к VK API для получения списка групп
            groups_response = await asyncio.to_thread(
                self.vk.groups.get,
                user_id=vk_id,
                v="5.131"
            )

            # Проверяем, что ответ содержит группы
            if groups_response and 'items' in groups_response:
                group_ids = groups_response['items']

                # Обновляем список групп и получаем новые
                new_groups = await Database.update_groups(vk_id, group_ids, current_time)

                # Если есть новые группы, отправляем уведомления
                if new_groups:
                    await self._send_new_groups_notifications(vk_id, new_groups, subscribers)

        except Exception as e:
            logger.error(f"Ошибка при проверке групп пользователя {vk_id}: {e}")

    async def _check_wall_posts(self, vk_id, current_time):
        """Проверка новых постов на стене пользователя"""
        # Получаем подписчиков, которые хотят отслеживать посты
        subscribers = await Database.get_subscribers_with_tracking(vk_id, "track_posts")
        if not subscribers:
            return

        try:
            # Запрос к VK API для получения последних постов
            posts_response = await asyncio.to_thread(
                self.vk.wall.get,
                owner_id=vk_id,
                count=20,  # Ограничиваем количество проверяемых постов
                v="5.131"
            )

            # Проверяем, что ответ содержит посты
            if posts_response and 'items' in posts_response:
                posts = posts_response['items']

                # Обновляем список постов и получаем новые
                new_posts = await Database.update_posts(vk_id, posts)

                # Если есть новые посты, отправляем уведомления
                if new_posts:
                    await self._send_new_posts_notifications(vk_id, new_posts, subscribers)

        except Exception as e:
            logger.error(f"Ошибка при проверке постов пользователя {vk_id}: {e}")

    async def _check_likes(self, vk_id, current_time):
        """Проверка новых лайков пользователя"""
        # Получаем подписчиков, которые хотят отслеживать лайки
        subscribers = await Database.get_subscribers_with_tracking(vk_id, "track_likes")
        if not subscribers:
            return

        # Проверяем используется ли пользовательский токен (имеет больше прав)
        is_user_token = bool(VK_USER_TOKEN)

        try:
            # Получаем лайки пользователя через API VK
            # К сожалению, нет прямого метода для получения всех последних лайков,
            # поэтому используем несколько методов для разных типов контента

            likes = []

            # 1. Проверяем лайки на стене пользователя (работает с сервисным токеном)
            try:
                # Получаем последние записи со стены пользователя
                wall_response = await asyncio.to_thread(
                    self.vk.wall.get,
                    owner_id=vk_id,
                    count=10,
                    v="5.131"
                )

                if wall_response and 'items' in wall_response:
                    for post in wall_response['items']:
                        # Проверяем, есть ли лайк от пользователя на этой записи
                        # (На своей записи пользователь может поставить лайк)
                        if post.get('likes', {}).get('user_likes') == 1:
                            like_info = {
                                "type": "post",
                                "owner_id": post.get("owner_id", vk_id),
                                "item_id": post.get("id"),
                                "date": post.get("date", int(time.time()))
                            }
                            likes.append(like_info)
            except Exception as wall_err:
                logger.error(f"Ошибка при проверке лайков на стене: {wall_err}")

            # Следующие методы доступны только с пользовательским токеном
            if is_user_token:
                # 2. Получаем новости пользователя и проверяем лайки на них
                try:
                    # Получаем последние записи из новостной ленты
                    newsfeed_response = await asyncio.to_thread(
                        self.vk.newsfeed.get,
                        filters="post",
                        count=15,
                        v="5.131"
                    )

                    if newsfeed_response and 'items' in newsfeed_response:
                        for item in newsfeed_response['items']:
                            # Проверяем лайк от пользователя на записи из ленты
                            post_id = item.get('post_id')
                            source_id = item.get('source_id')

                            if post_id and source_id and item.get('likes', {}).get('user_likes') == 1:
                                like_info = {
                                    "type": "post",
                                    "owner_id": source_id,
                                    "item_id": post_id,
                                    "date": item.get("date", int(time.time()))
                                }
                                likes.append(like_info)
                except Exception as newsfeed_err:
                    logger.error(f"Ошибка при проверке лайков в новостной ленте: {newsfeed_err}")

                # 3. Проверяем лайки на фотографиях
                try:
                    # Получаем новости с фотографиями
                    photos_feed_response = await asyncio.to_thread(
                        self.vk.newsfeed.get,
                        filters="photo",
                        count=10,
                        v="5.131"
                    )

                    if photos_feed_response and 'items' in photos_feed_response:
                        for item in photos_feed_response['items']:
                            if 'photos' in item and 'items' in item['photos']:
                                for photo in item['photos']['items']:
                                    if photo.get('likes', {}).get('user_likes') == 1:
                                        like_info = {
                                            "type": "photo",
                                            "owner_id": photo.get("owner_id"),
                                            "item_id": photo.get("id"),
                                            "date": photo.get("date", int(time.time()))
                                        }
                                        likes.append(like_info)
                except Exception as photos_err:
                    logger.error(f"Ошибка при проверке лайков на фотографиях: {photos_err}")
            else:
                logger.info(f"Проверка лайков в новостной ленте и на фотографиях пропущена для пользователя {vk_id}: требуется пользовательский токен")

            # Добавляем небольшую задержку для избежания ограничений API
            await asyncio.sleep(0.3)

            # Обновляем список лайков и получаем новые
            new_likes = await Database.update_likes(vk_id, likes, current_time)

            # Если есть новые лайки, отправляем уведомления
            if new_likes:
                await self._send_new_likes_notifications(vk_id, new_likes, subscribers)

        except Exception as e:
            logger.error(f"Ошибка при проверке лайков пользователя {vk_id}: {e}")

    async def _check_comments(self, vk_id, current_time):
        """Проверка новых комментариев пользователя"""
        # Получаем подписчиков, которые хотят отслеживать комментарии
        subscribers = await Database.get_subscribers_with_tracking(vk_id, "track_comments")
        if not subscribers:
            return

        # Проверяем используется ли пользовательский токен (имеет больше прав)
        is_user_token = bool(VK_USER_TOKEN)

        try:
            comments = []

            # Сначала получаем посты пользователя, чтобы затем проверить комментарии на них
            try:
                # Получаем последние посты со стены
                wall_response = await asyncio.to_thread(
                    self.vk.wall.get,
                    owner_id=vk_id,
                    count=10,  # Ограничиваем количество проверяемых постов
                    v="5.131"
                )

                if wall_response and 'items' in wall_response:
                    posts = wall_response['items']

                    # Для каждого поста получаем комментарии
                    for post in posts:
                        post_id = post.get('id')
                        if not post_id:
                            continue

                        try:
                            # Получаем комментарии к посту
                            post_comments_response = await asyncio.to_thread(
                                self.vk.wall.getComments,
                                owner_id=vk_id,
                                post_id=post_id,
                                count=20,
                                sort="desc",
                                v="5.131"
                            )

                            # Добавляем небольшую задержку между запросами
                            await asyncio.sleep(0.2)

                            if post_comments_response and 'items' in post_comments_response:
                                for comment in post_comments_response['items']:
                                    # Проверяем, что комментарий от отслеживаемого пользователя
                                    if comment.get('from_id') == vk_id:
                                        comment_info = {
                                            "id": comment.get("id"),
                                            "post_id": post_id,
                                            "owner_id": vk_id,
                                            "date": comment.get("date", int(time.time())),
                                            "text": comment.get("text", "")
                                        }
                                        comments.append(comment_info)
                        except ApiError as api_err:
                            # Игнорируем ошибку "post_id is required" - уже учтено в коде
                            if "post_id is required" in str(api_err):
                                continue
                            else:
                                logger.error(f"Ошибка API при получении комментариев для поста {post_id}: {api_err}")

                        except Exception as post_err:
                            logger.error(f"Ошибка при получении комментариев для поста {post_id}: {post_err}")

            except Exception as wall_err:
                logger.error(f"Ошибка при получении постов пользователя {vk_id}: {wall_err}")

            # Обновляем список комментариев и получаем новые
            new_comments = await Database.update_comments(vk_id, comments)

            # Если есть новые комментарии, отправляем уведомления
            if new_comments:
                await self._send_new_comments_notifications(vk_id, new_comments, subscribers)

        except Exception as e:
            logger.error(f"Ошибка при проверке комментариев пользователя {vk_id}: {e}")

    async def _get_user_name(self, vk_id):
        """Получение имени и фамилии пользователя"""
        try:
            user_info = await asyncio.to_thread(
                self.vk.users.get,
                user_ids=str(vk_id),
                v="5.131"
            )
            if user_info and len(user_info) > 0:
                first_name = user_info[0].get('first_name', '')
                last_name = user_info[0].get('last_name', '')
                return f"{first_name} {last_name}".strip()
            else:
                return f"VK ID {vk_id}"
        except Exception as e:
            logger.error(f"Ошибка при получении имени пользователя {vk_id}: {e}")
            return f"VK ID {vk_id}"

    async def _send_new_friends_notifications(self, vk_id, new_friends, subscribers):
        """Отправка уведомлений о новых друзьях"""
        try:
            # Получаем имя пользователя
            user_name = await self._get_user_name(vk_id)

            # Получаем имена новых друзей
            friends_info = await asyncio.to_thread(
                self.vk.users.get,
                user_ids=','.join(map(str, new_friends)),
                v="5.131"
            )

            for friend_info in friends_info:
                friend_id = friend_info.get('id')
                friend_name = f"{friend_info.get('first_name', '')} {friend_info.get('last_name', '')}".strip()

                # Формируем сообщение
                message = f"👥 {user_name} добавил(а) нового друга: {friend_name}\n" \
                          f"🔗 https://vk.com/id{friend_id}"

                # Отправляем уведомления всем подписчикам
                for chat_id in subscribers:
                    await self.send_notification(chat_id, message, disable_preview=False)

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о новых друзьях: {e}")

    async def _send_new_groups_notifications(self, vk_id, new_groups, subscribers):
        """Отправка уведомлений о новых группах"""
        try:
            # Получаем имя пользователя
            user_name = await self._get_user_name(vk_id)

            # Получаем информацию о новых группах
            groups_info = await asyncio.to_thread(
                self.vk.groups.getById,
                group_ids=','.join(map(str, new_groups)),
                v="5.131"
            )

            for group_info in groups_info:
                group_id = group_info.get('id')
                group_name = group_info.get('name', 'Группа')
                group_screen_name = group_info.get('screen_name', f"club{group_id}")

                # Формируем сообщение
                message = f"👥 {user_name} вступил(а) в группу: {group_name}\n" \
                          f"🔗 https://vk.com/{group_screen_name}"

                # Отправляем уведомления всем подписчикам
                for chat_id in subscribers:
                    await self.send_notification(chat_id, message, disable_preview=False)

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о новых группах: {e}")

    async def _send_new_posts_notifications(self, vk_id, new_posts, subscribers):
        """Отправка уведомлений о новых постах"""
        try:
            # Получаем имя пользователя
            user_name = await self._get_user_name(vk_id)

            for post in new_posts:
                post_id = post.get("id")
                owner_id = post.get("owner_id")
                post_text = post.get("text", "")

                # Ограничиваем длину текста для сообщения
                if post_text:
                    if len(post_text) > 200:
                        post_text = post_text[:200] + "..."

                # Формируем сообщение
                message = f"📝 {user_name} опубликовал(а) новый пост:\n\n"
                if post_text:
                    message += f"{post_text}\n\n"
                message += f"🔗 https://vk.com/wall{owner_id}_{post_id}"

                # Отправляем уведомления всем подписчикам
                for chat_id in subscribers:
                    await self.send_notification(chat_id, message, disable_preview=False)

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о новых постах: {e}")

    async def _send_new_likes_notifications(self, vk_id, new_likes, subscribers):
        """Отправка уведомлений о новых лайках"""
        try:
            # Получаем имя пользователя
            user_name = await self._get_user_name(vk_id)

            for like in new_likes:
                like_type = like.get("type")
                owner_id = like.get("owner_id")
                item_id = like.get("item_id")

                # Формируем ссылку в зависимости от типа контента
                link = "https://vk.com/"
                type_name = "запись"

                if like_type == "post":
                    link = f"https://vk.com/wall{owner_id}_{item_id}"
                    type_name = "запись"
                elif like_type == "photo":
                    link = f"https://vk.com/photo{owner_id}_{item_id}"
                    type_name = "фотографию"
                elif like_type == "video":
                    link = f"https://vk.com/video{owner_id}_{item_id}"
                    type_name = "видео"
                elif like_type == "comment":
                    link = f"https://vk.com/wall{owner_id}_{item_id}?reply={item_id}"
                    type_name = "комментарий"

                # Получаем доп. информацию о контенте, на который поставлен лайк
                try:
                    if like_type == "post":
                        # Пытаемся получить текст поста, если это возможно
                        post_info = await asyncio.to_thread(
                            self.vk.wall.getById,
                            posts=f"{owner_id}_{item_id}",
                            v="5.131"
                        )

                        if post_info and len(post_info) > 0:
                            post_text = post_info[0].get('text', '')
                            post_preview = post_text[:100] + "..." if len(post_text) > 100 else post_text
                            if post_preview:
                                type_name = f"запись:\n\"{post_preview}\""
                except Exception as e:
                    logger.error(f"Ошибка при получении доп. информации о контенте: {e}")

                # Формируем сообщение
                message = f"❤️ {user_name} поставил(а) лайк на {type_name}\n" \
                          f"🔗 {link}"

                # Отправляем уведомления всем подписчикам
                for chat_id in subscribers:
                    await self.send_notification(chat_id, message, disable_preview=False)

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о новых лайках: {e}")

    async def _send_new_comments_notifications(self, vk_id, new_comments, subscribers):
        """Отправка уведомлений о новых комментариях"""
        try:
            # Получаем имя пользователя
            user_name = await self._get_user_name(vk_id)

            for comment in new_comments:
                comment_id = comment.get("id")
                post_id = comment.get("post_id")
                owner_id = comment.get("owner_id")
                comment_text = comment.get("text", "")

                # Ограничиваем длину текста для сообщения
                if comment_text:
                    if len(comment_text) > 200:
                        comment_text = comment_text[:200] + "..."

                # Формируем ссылку на комментарий
                link = f"https://vk.com/wall{owner_id}_{post_id}?reply={comment_id}"

                # Формируем сообщение
                message = f"💬 {user_name} оставил(а) новый комментарий:\n\n"
                if comment_text:
                    message += f"{comment_text}\n\n"
                message += f"🔗 {link}"

                # Отправляем уведомления всем подписчикам
                for chat_id in subscribers:
                    await self.send_notification(chat_id, message, disable_preview=False)

        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о новых комментариях: {e}")
