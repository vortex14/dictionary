docker-compose down --remove-orphans
docker rmi -f telebot_postgres
docker rm] -f telebot_bot_app
docker volume prune
