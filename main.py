# main.py
# FACILITADOR LITE - versão para deploy no Render (com token embutido conforme solicitado)
import os
import logging
from flask import Flask, request, Response
import telegram
from telegram import Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# ----------------------------
# CONFIGURAÇÃO (token embutido)
# ----------------------------
TELEGRAM_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"  # <-- token que você passou
WEBHOOK_PATH = "/webhooks/telegram/action"  # rota que usaremos no webhook
PORT = int(os.environ.get("PORT", "10000"))

# ----------------------------
# logging
# ----------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# Flask app + Telegram bot
# ----------------------------
app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Dispatcher: sem polling, usaremos process_update() ao receber o POST do webhook
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# ----------------------------
# Handlers do bot
# ----------------------------
def start(update, context):
    """Handler para /start"""
    user = update.effective_user
    name = user.first_name if user and user.first_name else "amigo"
    text = (
        f"👋 Olá {name}! Eu sou o *FACILITADOR LITE*.\n\n"
        "Envie o modelo do veículo para eu buscar a bateria indicada, ou use o menu."
    )
    update.message.reply_text(text, parse_mode="Markdown")

def echo(update, context):
    """Handler que ecoa mensagens e demonstra que o bot está respondendo."""
    txt = update.message.text or ""
    # exemplo de respostas rápidas
    if txt.strip().lower() == "ping":
        update.message.reply_text("pong")
        return
    # regra simples: se detectar palavras de carro, responder busca simulada
    low = txt.lower()
    keywords = ["corolla","onix","gol","hb20","civic","fiat","uno","toro","hilux"]
    if any(k in low for k in keywords):
        # Simulação de busca (aqui você pode chamar função de scraping real)
        update.message.reply_text(f"🔎 Buscando bateria ideal para: *{txt}*\nResposta simulada: M60GD", parse_mode="Markdown")
    else:
        update.message.reply_text(f"Você disse: {txt}")

# registrar handlers no dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

# ----------------------------
# Rotas Flask
# ----------------------------
@app.route('
