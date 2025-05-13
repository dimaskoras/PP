import aiosqlite
import logging
from config import DB_PATH

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных SQLite"""
    
    @staticmethod
    async def init_db():
        """Инициализация базы данных и создание таблиц при необходимости"""
        async with aiosqlite.connect(DB_PATH) as db:
            # Создание таблицы для хранения подписок
            await db.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    chat_id INTEGER,
                    vk_id INTEGER,
                    PRIMARY KEY (chat_id, vk_id)
                )
            ''')
            
            # Создание таблицы для хранения статусов пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_statuses (
                    vk_id INTEGER PRIMARY KEY,
                    online INTEGER,
                    last_seen INTEGER
                )
            ''')
            
            # Создание таблицы для хранения друзей пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_friends (
                    vk_id INTEGER,
                    friend_id INTEGER,
                    added_at INTEGER,
                    PRIMARY KEY (vk_id, friend_id)
                )
            ''')
            
            # Создание таблицы для хранения групп пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_groups (
                    vk_id INTEGER,
                    group_id INTEGER,
                    added_at INTEGER,
                    PRIMARY KEY (vk_id, group_id)
                )
            ''')
            
            # Создание таблицы для хранения постов пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_posts (
                    vk_id INTEGER,
                    post_id INTEGER,
                    owner_id INTEGER,
                    date INTEGER,
                    text TEXT,
                    PRIMARY KEY (owner_id, post_id)
                )
            ''')
            
            # Создание таблицы для хранения лайков пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_likes (
                    vk_id INTEGER,
                    item_id INTEGER,
                    owner_id INTEGER,
                    type TEXT,
                    added_at INTEGER,
                    PRIMARY KEY (vk_id, type, owner_id, item_id)
                )
            ''')
            
            # Создание таблицы для хранения комментариев пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_comments (
                    vk_id INTEGER,
                    comment_id INTEGER,
                    post_id INTEGER,
                    owner_id INTEGER,
                    date INTEGER,
                    text TEXT,
                    PRIMARY KEY (vk_id, owner_id, post_id, comment_id)
                )
            ''')
            
            # Создание таблицы для дополнительных настроек мониторинга
            await db.execute('''
                CREATE TABLE IF NOT EXISTS monitoring_settings (
                    chat_id INTEGER,
                    vk_id INTEGER,
                    track_online INTEGER DEFAULT 1,
                    track_friends INTEGER DEFAULT 0,
                    track_groups INTEGER DEFAULT 0,
                    track_posts INTEGER DEFAULT 0,
                    track_likes INTEGER DEFAULT 0,
                    track_comments INTEGER DEFAULT 0,
                    PRIMARY KEY (chat_id, vk_id)
                )
            ''')
            
            await db.commit()
            logger.info("База данных инициализирована")
    
    @staticmethod
    async def add_subscription(chat_id, vk_id):
        """Добавление подписки на VK-пользователя"""
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute(
                    "INSERT OR IGNORE INTO subscriptions (chat_id, vk_id) VALUES (?, ?)",
                    (chat_id, vk_id)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка при добавлении подписки: {e}")
                return False
    
    @staticmethod
    async def remove_subscription(chat_id, vk_id):
        """Удаление подписки на VK-пользователя"""
        async with aiosqlite.connect(DB_PATH) as db:
            try:
                await db.execute(
                    "DELETE FROM subscriptions WHERE chat_id = ? AND vk_id = ?",
                    (chat_id, vk_id)
                )
                await db.commit()
                # Проверяем, остались ли подписки на этого vk_id
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM subscriptions WHERE vk_id = ?",
                    (vk_id,)
                )
                count = await cursor.fetchone()
                
                # Если нет подписок, удаляем информацию о статусе
                if count[0] == 0:
                    await db.execute("DELETE FROM user_statuses WHERE vk_id = ?", (vk_id,))
                    await db.commit()
                    
                return True
            except Exception as e:
                logger.error(f"Ошибка при удалении подписки: {e}")
                return False
    
    @staticmethod
    async def get_subscriptions(chat_id):
        """Получение списка VK ID, на которые подписан пользователь"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT vk_id FROM subscriptions WHERE chat_id = ?",
                (chat_id,)
            )
            result = await cursor.fetchall()
            return [row[0] for row in result]
    
    @staticmethod
    async def get_all_tracked_vk_ids():
        """Получение списка всех отслеживаемых VK ID"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT DISTINCT vk_id FROM subscriptions")
            result = await cursor.fetchall()
            return [row[0] for row in result]
    
    @staticmethod
    async def get_subscribers_for_vk_id(vk_id):
        """Получение списка Telegram chat_id, подписанных на VK-пользователя"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT chat_id FROM subscriptions WHERE vk_id = ?",
                (vk_id,)
            )
            result = await cursor.fetchall()
            return [row[0] for row in result]
    
    @staticmethod
    async def get_user_status(vk_id):
        """Получение текущего статуса VK-пользователя из базы данных"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT online, last_seen FROM user_statuses WHERE vk_id = ?",
                (vk_id,)
            )
            result = await cursor.fetchone()
            if result:
                return {"online": result[0], "last_seen": result[1]}
            return None
    
    @staticmethod
    async def update_user_status(vk_id, online, last_seen):
        """Обновление статуса VK-пользователя в базе данных"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO user_statuses (vk_id, online, last_seen)
                VALUES (?, ?, ?)
                """,
                (vk_id, online, last_seen)
            )
            await db.commit()
            
    @staticmethod
    async def init_monitoring_settings(chat_id, vk_id):
        """Инициализация настроек мониторинга для пользователя"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO monitoring_settings 
                (chat_id, vk_id, track_online, track_friends, track_groups, track_posts, track_likes, track_comments)
                VALUES (?, ?, 1, 0, 0, 0, 0, 0)
                """,
                (chat_id, vk_id)
            )
            await db.commit()
    
    @staticmethod
    async def update_monitoring_settings(chat_id, vk_id, settings):
        """Обновление настроек мониторинга для пользователя"""
        async with aiosqlite.connect(DB_PATH) as db:
            # Формируем запрос на обновление только переданных настроек
            query_parts = []
            params = []
            
            for setting, value in settings.items():
                if setting in ["track_online", "track_friends", "track_groups", "track_posts", "track_likes", "track_comments"]:
                    query_parts.append(f"{setting} = ?")
                    params.append(value)
            
            if not query_parts:
                return False
            
            query = f"UPDATE monitoring_settings SET {', '.join(query_parts)} WHERE chat_id = ? AND vk_id = ?"
            params.extend([chat_id, vk_id])
            
            await db.execute(query, params)
            await db.commit()
            return True
    
    @staticmethod
    async def get_monitoring_settings(chat_id, vk_id):
        """Получение настроек мониторинга для пользователя"""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                """
                SELECT track_online, track_friends, track_groups, track_posts, track_likes, track_comments
                FROM monitoring_settings
                WHERE chat_id = ? AND vk_id = ?
                """,
                (chat_id, vk_id)
            )
            result = await cursor.fetchone()
            
            if result:
                return {
                    "track_online": bool(result[0]),
                    "track_friends": bool(result[1]),
                    "track_groups": bool(result[2]),
                    "track_posts": bool(result[3]),
                    "track_likes": bool(result[4]),
                    "track_comments": bool(result[5])
                }
            
            return None
    
    @staticmethod
    async def get_users_with_activity_tracking():
        """Получение списка пользователей с включенным отслеживанием активности"""
        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем пользователей с любым отслеживанием активности (кроме онлайн-статуса)
            cursor = await db.execute(
                """
                SELECT DISTINCT vk_id FROM monitoring_settings
                WHERE track_friends = 1 OR track_groups = 1 OR track_posts = 1 OR 
                      track_likes = 1 OR track_comments = 1
                """
            )
            result = await cursor.fetchall()
            return [row[0] for row in result]
    
    @staticmethod
    async def get_subscribers_with_tracking(vk_id, track_type):
        """Получение списка подписчиков с определенным типом отслеживания"""
        if track_type not in ["track_online", "track_friends", "track_groups", "track_posts", "track_likes", "track_comments"]:
            return []
            
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                f"""
                SELECT chat_id FROM monitoring_settings
                WHERE vk_id = ? AND {track_type} = 1
                """,
                (vk_id,)
            )
            result = await cursor.fetchall()
            return [row[0] for row in result]
            
    # Методы для работы с друзьями
    @staticmethod
    async def update_friends(vk_id, friends, current_time):
        """Обновление списка друзей пользователя и получение новых друзей"""
        new_friends = []
        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем текущий список друзей
            cursor = await db.execute(
                "SELECT friend_id FROM user_friends WHERE vk_id = ?",
                (vk_id,)
            )
            existing_friends = {row[0] for row in await cursor.fetchall()}
            
            # Обрабатываем новых друзей
            for friend_id in friends:
                if friend_id not in existing_friends:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO user_friends (vk_id, friend_id, added_at)
                        VALUES (?, ?, ?)
                        """,
                        (vk_id, friend_id, current_time)
                    )
                    new_friends.append(friend_id)
            
            await db.commit()
        return new_friends
        
    # Методы для работы с группами
    @staticmethod
    async def update_groups(vk_id, groups, current_time):
        """Обновление списка групп пользователя и получение новых групп"""
        new_groups = []
        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем текущий список групп
            cursor = await db.execute(
                "SELECT group_id FROM user_groups WHERE vk_id = ?",
                (vk_id,)
            )
            existing_groups = {row[0] for row in await cursor.fetchall()}
            
            # Обрабатываем новые группы
            for group_id in groups:
                if group_id not in existing_groups:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO user_groups (vk_id, group_id, added_at)
                        VALUES (?, ?, ?)
                        """,
                        (vk_id, group_id, current_time)
                    )
                    new_groups.append(group_id)
            
            await db.commit()
        return new_groups
    
    # Методы для работы с постами
    @staticmethod
    async def update_posts(vk_id, posts):
        """Обновление списка постов пользователя и получение новых постов"""
        new_posts = []
        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем текущие посты
            cursor = await db.execute(
                "SELECT owner_id, post_id FROM user_posts WHERE vk_id = ?",
                (vk_id,)
            )
            existing_posts = {(row[0], row[1]) for row in await cursor.fetchall()}
            
            # Обрабатываем новые посты
            for post in posts:
                post_id = post.get("id")
                owner_id = post.get("owner_id")
                post_date = post.get("date")
                text = post.get("text", "")
                
                post_key = (owner_id, post_id)
                if post_key not in existing_posts:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO user_posts (vk_id, post_id, owner_id, date, text)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (vk_id, post_id, owner_id, post_date, text)
                    )
                    new_posts.append(post)
            
            await db.commit()
        return new_posts
    
    # Методы для работы с лайками
    @staticmethod
    async def update_likes(vk_id, likes, current_time):
        """Обновление списка лайков пользователя и получение новых лайков"""
        new_likes = []
        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем текущие лайки
            cursor = await db.execute(
                "SELECT type, owner_id, item_id FROM user_likes WHERE vk_id = ?",
                (vk_id,)
            )
            existing_likes = {(row[0], row[1], row[2]) for row in await cursor.fetchall()}
            
            # Обрабатываем новые лайки
            for like in likes:
                like_type = like.get("type")
                owner_id = like.get("owner_id")
                item_id = like.get("item_id")
                
                like_key = (like_type, owner_id, item_id)
                if like_key not in existing_likes:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO user_likes (vk_id, type, owner_id, item_id, added_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (vk_id, like_type, owner_id, item_id, current_time)
                    )
                    new_likes.append(like)
            
            await db.commit()
        return new_likes
    
    # Методы для работы с комментариями
    @staticmethod
    async def update_comments(vk_id, comments):
        """Обновление списка комментариев пользователя и получение новых комментариев"""
        new_comments = []
        async with aiosqlite.connect(DB_PATH) as db:
            # Получаем текущие комментарии
            cursor = await db.execute(
                "SELECT owner_id, post_id, comment_id FROM user_comments WHERE vk_id = ?",
                (vk_id,)
            )
            existing_comments = {(row[0], row[1], row[2]) for row in await cursor.fetchall()}
            
            # Обрабатываем новые комментарии
            for comment in comments:
                comment_id = comment.get("id")
                post_id = comment.get("post_id")
                owner_id = comment.get("owner_id")
                date = comment.get("date")
                text = comment.get("text", "")
                
                comment_key = (owner_id, post_id, comment_id)
                if comment_key not in existing_comments:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO user_comments (vk_id, comment_id, post_id, owner_id, date, text)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (vk_id, comment_id, post_id, owner_id, date, text)
                    )
                    new_comments.append(comment)
            
            await db.commit()
        return new_comments
