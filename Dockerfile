FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip

RUN pip install ably alpaca-py tensorflow==2.15.0 pandas asyncio scikit-learn numpy

# Set environment variables
ENV ALPACA_KEY="PKODZGQ3BIWGQJ6A3HJ4" \
    ENV_VAR2="WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ" \
    SUPABASE_ID="yygimsahwbrurnvyfmul" \
    API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5Z2ltc2Fod2JydXJudnlmbXVsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxMDY4ODI2OCwiZXhwIjoyMDI2MjY0MjY4fQ.A0EiE0m1Ze_bYOz-8LBymdBwHvQwMr3n0wO6ajvJtzw"\
    ABLY="rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw"

COPY . client.py \ 
    model.py \
    utils.py \

CMD ["python", "client.py"]
