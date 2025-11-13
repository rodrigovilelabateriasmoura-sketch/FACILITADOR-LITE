import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
WEBHOOK_URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"

app = Flask(__name__)

# Cria a aplicação do bot
application = ApplicationBuilder().token(TOKEN).build()

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Sou o bot FACILITADOR LITE. Envie uma mensagem!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /start para começar ou envie qualquer mensagem.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Você enviou: {text}")

# Registra os handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === FLASK ROUTES ===
@app.route("/")
def index():
    return "FACILITADOR LITE está ativo! 🚀"

@app.route("/webhooks/telegram/action", methods=["POST"])
def webhook():
    if request.method == "POST":
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)
        application.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    # Configura o webhook automaticamente ao iniciar
    import asyncio
    asyncio.run(application.bot.delete_webhook())
    asyncio.run(application.bot.set_webhook(url=WEBHOOK_URL))

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
