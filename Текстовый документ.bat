@echo off

cd C:\Users\gik47\OneDrive\Desktop\my-project

set /p commit_message="Messsage for commit: "

git add .
git commit -m "%commit_message%"

git branch -M main

git push -u origin main --force

pause
