# Crypto Lab

## Описание
Набор инструментов для автоматизации крипто-трейдинга и анализа рынка.

## Стек
- Python 3.11+
- Web3.py
- FastAPI
- Docker

## Запуск
```bash
pip install -r requirements.txt
python src/main.py
```

### Быстрый старт (арбитраж трекинг)
```bash
make install
make scan            # сформировать data/candidates.json (USDT perpetuals Binance/Bybit)
make run-spread      # запустить бесконечный цикл расчёта спреда
```

Переменные окружения для фильтрации:
1 bps = 0.01% (100 bps = 1%)
- `SPREADS_MIN_BPS` — минимальный |bps| (например 20)
- `SPREADS_MAX_BPS` — максимальный |bps| (например 150)
- `SPREADS_INTERVAL` — период в секундах (по умолчанию 30)

