# Usa un'immagine base Python
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia il file requirements.txt e il codice del bot nella container
COPY requirements.txt requirements.txt
COPY bot.py bot.py

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Imposta la variabile d'ambiente per il token di Telegram
ENV TELEGRAM_TOKEN="tuo_token_telegram"

# Avvia il bot
CMD ["python", "bot.py"]
