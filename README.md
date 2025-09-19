
# EDP Solar Auth API

Uma API para autenticação na plataforma **EDP Solar** usando Selenium e OAuth2.  
Este projeto permite receber **usuário e senha** via POST e retornar os tokens de acesso (`token.json`) de forma automática.


## ⚠️ Observações

* Este projeto **não é oficial** da EDP.
* O login simula o comportamento do usuário via navegador, portanto qualquer mudança na página de login da EDP pode quebrar o fluxo.
* Tokens são salvos em `/data/token.json`.

---

## 🚀 Funcionalidades

- Simula o login na plataforma EDP Solar via **Selenium Chrome/Chromedriver**.
- Captura o **authorization code** e troca por **tokens OAuth2**.
- Retorna os tokens via **endpoint HTTP POST**.
- Pode ser executado via **Docker**, com volume `/data` para persistência de tokens/logs.
- Porta da API configurável via variável de ambiente `PORT` (default: `8000`).

---

## ⚡ Tecnologias

- Python 3.11
- FastAPI
- Selenium + Selenium Wire
- Uvicorn
- Docker

---

## 📦 Instalação

### Pré-requisitos

- Docker
- Google Chrome e Chromedriver compatível (já incluídos na imagem Docker)

### Build da imagem Docker

```bash
docker build -t edp-solar-api .
````

---

## 🔧 Uso

### Rodar com porta padrão 8000

```bash
docker run -p 8000:8000 edp-solar-api
```

### Rodar em outra porta (exemplo 8080)

```bash
docker run -e PORT=8080 -p 8080:8080 edp-solar-api
```

### Persistência de dados

O container possui volume `/data` para armazenar:

* `token.json`
* logs de execução
* screenshots do login

Exemplo de uso com volume local:

```bash
docker run -v $(pwd)/data:/data -p 8000:8000 edp-solar-api
```

---

## 📝 Endpoint

**POST /login**

Recebe JSON com:

```json
{
  "username": "seu_usuario",
  "password": "sua_senha"
}
```

Retorna JSON com tokens de acesso:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "id_token": "...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

---


## 🔑 Variáveis de ambiente

* `CLIENT_ID` – ID do cliente OAuth2
* `REDIRECT_URI` – URI de redirecionamento (default: `edpc://solar`)
* `AUTH_HOST` – Host do Cognito (default: `prd-accountlinking.auth.eu-west-1.amazoncognito.com`)
* `PORT` – Porta da API (default: `8000`)

---

## 🖼️ Logs e Debug

O container salva automaticamente:

* `/data/login.html` – página de login
* `/data/login.png` – screenshot do login
* `/data/post-login.png` – screenshot após preencher senha
* `/data/console.log` – logs do console do navegador
* `/data/logs.txt` – requests capturados pelo Selenium Wire

---

## 📌 Contato

Desenvolvido por **@VivaldiCode**
