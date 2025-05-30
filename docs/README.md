# 📚 Документация проекта

## 📋 Общая информация

### Период проведения практики
31.03.2025 - 21.05.2025

### Участники
- Кондратенко Дмитрий

### Руководители
- **Ответственный по практике:** Меньшикова Наталия Павловна
- **Куратор по проектной деятельности:** Никулина Анна Константиновна

# 🎯 Часть 1: Основной проект "Робобол"

## Описание проекта
"Робобол" — это инновационная физическая игра с элементами образования, направленная на развитие технических навыков у детей через интерактивное взаимодействие с роботизированными машинками.

## Веб-сайт проекта

### Технологии
- HTML5
- CSS3 (с CSS Variables)
- JavaScript
- Feather Icons
- Google Fonts (Montserrat, Roboto)

### Структура сайта
- **Главная** — Hero-секция с видео
- **О проекте** — описание концепции
- **Игровая машинка** — технические характеристики
- **Игровое поле** — описание арены
- **Галерея** — фото и видео
- **Команда** — участники проекта

### Особенности реализации
- Адаптивный дизайн
- Интерактивные элементы
- Модальные окна для галереи
- Мобильное меню
- Видео-презентация проекта

# 🤖 Часть 2: Вариативное задание - Telegram-бот

## Описание задания
Разработка Telegram-бота на Python для отслеживания активности пользователей ВКонтакте.

### Технологии
- Python 3.8+
- python-telegram-bot
- vk_api
- aiosqlite
- asyncio

### Основной функционал
- Мониторинг онлайн-статуса
- Отслеживание изменений в друзьях
- Мониторинг активности в группах
- Отслеживание постов/лайков/комментариев
- Система уведомлений
- База данных SQLite

### Структура исходного кода
```
src/
├── main.py   # Запуск бота
├── bot_commands.py   # Команды бота
├── vk_tracker.py     # Логика отслеживания
├── database.py       # Работа с БД
├── env.txt           # Все необходимые токены
└── config.py         # Конфигурация
```

### Команды бота
- `/start` — начало работы
- `/help` — справка
- `/subscribe` — подписка на пользователя
- `/unsubscribe` — отписка
- `/list` — список отслеживаемых
- `/settings` — настройки
- `/toggle` — управление параметрами

## 📊 Результаты практики

### Достигнутые цели
1. **Основная часть:**
   - Разработан информационный веб-сайт проекта "Робобол"
   - Создан адаптивный и современный дизайн
   - Реализован интерактивный интерфейс

2. **Вариативная часть:**
   - Реализован функциональный Telegram-бот
   - Настроено взаимодействие с VK API
   - Создана система мониторинга активности
   - Организовано хранение данных в SQLite

### Технические навыки
- Git/GitHub
- HTML/CSS/JavaScript
- Python
- API (Telegram, VK)
- SQLite
