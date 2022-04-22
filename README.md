## Установка зависимостей
``` 
./install.sh 
```

## Добавление ENV в .env.local для локальной разработки

``` 
LEVEL=<LEVEL>
API_TELEGRAM_BOT_TOKEN=<API-TOKEN> 
DB_URL=<URL>
```
после применить переменные окружения
```
source .env.local
```

## Запуск сервера
``` 
./start.sh 
```

## Предварительный просмотр схемы базы данных
### https://app.quickdatabasediagrams.com/#/d/TfFxRs


## Конвертировать схему базы данных в Pydantic model
```
cd models && omm schema.sql -m pydantic
```

### https://github.com/xnuinside/omymodels