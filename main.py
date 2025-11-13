from flask import Flask, request
import requests
import os

app = Flask(_name_)

# Substitua abaixo pelo SEU token do BotFather
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("⚠ TELEGRAM_TOKEN não definido nas variáveis de ambiente!")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ======== ROTA RAIZ =========
@app.route('/')
def home():
    return "🤖 FACILITADOR LITE - Online e funcionando!"

# ======== ROTA DO WEBHOOK =========
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if not data:
        return {"status": "ignored", "reason": "empty payload"}, 400

    # Extrai dados da mensagem
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return {"status": "ignored", "reason": "no chat_id or text"}, 200

    print(f"📩 Mensagem recebida: {text} de {chat_id}")

    if text.lower().startswith("/start"):
        send_message(chat_id, "👋 Olá! Eu sou o FACILITADOR LITE.\n\nEnvie a placa do veículo ou o modelo para descobrir a bateria ideal Moura 🔋", parse_mode="Markdown")

    elif len(text.strip()) >= 3:
        # Aqui simulamos uma resposta simples
        resposta = f"🔍 Buscando informações sobre o veículo: {text}\nAguarde um momento..."
        send_message(chat_id, resposta, parse_mode="Markdown")
    else:
        send_message(chat_id, "❗ Digite algo válido, por favor.")

    return {"status": "ok"}, 200


# ======== FUNÇÃO PARA ENVIAR MENSAGEM =========
def send_message(chat_id, text, parse_mode=None):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print("⚠ Erro ao enviar mensagem:", response.text)


# ======== INICIALIZAÇÃO LOCAL =========
if _name_ == '_main_':
    print("🚀 FACILITADOR LITE iniciado!")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))