@echo off

cd C:\Users\gik47\OneDrive\Desktop\my-project

:: Запрос текста от пользователя
set /p commit_message="Messsage for commit: "

:: Добавляем изменения и выполняем коммит с введённым сообщением
git add .
git commit -m "%commit_message%"

:: Переименовываем ветку в main (если нужно)
git branch -M main

:: Пушим изменения в основную ветку репозитория
git push -u origin main --force

pause
