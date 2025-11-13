# main.py
import sys
import types

# ✅ Cria um módulo "imghdr" vazio para compatibilidade com Python 3.13+
if "imghdr" not in sys.modules:
    imghdr = types.ModuleType("imghdr")
    sys.modules["imghdr"] = imghdr

from flask import Flask, request
import telegram

TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ativo e rodando no Render 🚀"

@app.route(f'/webhooks/telegram/action', methods=['POST'])
def webhook_telegram():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    if update.message and update.message.text:
        chat_id = update.message.chat.id
        text = update.message.text

        # Resposta simples
        if text.lower() in ["oi", "olá", "bom dia", "boa tarde", "boa noite"]:
            bot.send_message(chat_id=chat_id, text="Olá! 👋 Eu sou o facilitador Moura!")
        else:
            bot.send_message(chat_id=chat_id, text="Recebi sua mensagem, obrigado!")

    return "ok", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
