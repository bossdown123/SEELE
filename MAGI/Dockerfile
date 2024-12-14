FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip

RUN pip install ably alpaca-py tensorflow==2.15.0 pandas asyncio scikit-learn numpy simfin


COPY .env /app/

RUN export $(grep -v '^#' /app/.env | xargs)

COPY client.py model.keras multi_scaler.pickle utils.py prediction_utils.py order_logic.py /app/

WORKDIR /app

CMD ["python", "client.py"]