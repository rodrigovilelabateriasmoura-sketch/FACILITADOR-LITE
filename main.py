import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, filters

TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
bot = Bot(token=TOKEN)

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Handlers
def start(update: Update, context):
    update.message.reply_text("Olá! Sou o bot Facilitador Lite. Envie uma mensagem!")

def help_command(update: Update, context):
    update.message.reply_text("Use /start para começar ou envie qualquer mensagem.")

def handle_message(update: Update, context):
    user_text = update.message.text
    response = f"Você enviou: {user_text}"
    update.message.reply_text(response)

# Dispatcher (síncrono)
dispatcher = Dispatcher(bot, None, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook principal
@app.route("/")
def index():
    return "Bot ativo e rodando com sucesso!"

@app.route(f"/webhooks/telegram/action", methods=["POST"])
def telegram_webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "ok"

if __name__ == "__main__":
    import os

    # Configura o webhook automaticamente no início
    URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"
    bot.delete_webhook()
    bot.set_webhook(URL)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
