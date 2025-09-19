FROM --platform=linux/amd64 python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema de forma enxuta
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg2 ca-certificates unzip xvfb libnss3 libgtk-3-0 \
    libx11-xcb1 libxss1 libasound2 curl fonts-liberation \
    libu2f-udev xdg-utils \
  && rm -rf /var/lib/apt/lists/*

RUN pip install uvicorn

# Baixar e instalar o Google Chrome
# Outra fonte possivel https://mirror.kraski.tv/soft/google_chrome/linux/114.0.5735.90/google-chrome-stable_114.0.5735.90-1_amd64.deb
RUN wget -q https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb \
    -O /tmp/google-chrome-stable.deb \
  && apt-get install -y /tmp/google-chrome-stable.deb \
  && rm /tmp/google-chrome-stable.deb

# Instalar Chromedriver
COPY ./chromedriver_linux64.zip /tmp/chromedriver.zip
RUN unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Copiar aplicação
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Volume para persistir tokens e logs
VOLUME ["/data"]

# Variável de ambiente para porta
ENV PORT=8000

# Expor porta
EXPOSE ${PORT}

# Comando default
CMD ["sh", "-c", "uvicorn app_api:app --host 0.0.0.0 --port ${PORT}"]
