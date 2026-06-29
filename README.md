# Quote Builder

Калькулятор комерційних пропозицій для будівельних/оздоблювальних робіт.  
Підтримує CLI і веб-інтерфейс на базі FastAPI.

## Структура

```
QUOTE_BUILDER/
├── core/
│   ├── models.py       # Pydantic-моделі (TradeConfig, QuoteRequest, QuoteResult, …)
│   ├── calculator.py   # Бізнес-логіка calculate_quote()
│   └── rules.py        # Допоміжні правила (effective_area)
├── cli/
│   └── app.py          # Інтерактивний CLI
├── web/
│   ├── api.py          # FastAPI REST API + роздача static/
│   └── static/
│       └── index.html  # Веб-UI (vanilla JS)
├── data/
│   ├── trades.json     # Конфіг тредів і пресетів
│   └── history/        # Збережені квоти (JSON)
├── scripts/
│   └── quickcheck.py   # Швидка перевірка логіки
├── main.py             # Запуск CLI
└── main_web.py         # Запуск веб-сервера
```

## Встановлення

```bash
pip install -r requirements.txt
```

## Запуск

### CLI (термінал)

```bash
python main.py
```

### Веб-інтерфейс

```bash
python main_web.py
```

Після запуску відкрийте: [http://127.0.0.1:8000](http://127.0.0.1:8000)

API-документація (Swagger): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Швидка перевірка

```bash
python scripts/quickcheck.py
```

## Типи ціноутворення

| Тип | Опис |
|---|---|
| `FLAT_MIN_TOTAL` | Авторозрахунок з мінімальною сумою |
| `MIN_RATE_PER_SQFT` | Авторозрахунок з мінімальною ставкою за sqft |
| `CUSTOM` | Авторозрахунок або ручне введення загальної суми |

## API

| Метод | Шлях | Опис |
|---|---|---|
| GET | `/health` | Перевірка стану сервера |
| GET | `/api/trades` | Список усіх тредів і пресетів |
| POST | `/api/quote` | Розрахувати квоту |
