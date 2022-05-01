docker-compose down --remove-orphans
docker rmi -f telebot_postgres
docker rmi -f telebot_bot_app
docker volume prune
