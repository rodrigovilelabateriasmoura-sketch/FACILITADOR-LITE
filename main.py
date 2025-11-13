# main.py
# FACILITADOR LITE - versão funcional para Render
import os
import logging
from flask import Flask, request, Response
import telegram
from telegram import Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

# ----------------------------
# CONFIGURAÇÃO (token embutido conforme solicitado)
# ----------------------------
TELEGRAM_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
WEBHOOK_PATH = "/webhooks/telegram/action"
PORT = int(os.environ.get("PORT", 10000))

# ----------------------------
# LOGGING
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------------------
# FLASK + TELEGRAM BOT
# ----------------------------
app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# ----------------------------
# HANDLERS DO BOT
# ----------------------------
def start(update, context):
    """Handler para /start"""
    user = update.effective_user
    name = user.first_name if user and user.first_name else "amigo"
    msg = (
        f"👋 Olá {name}! Eu sou o *FACILITADOR LITE*.\n\n"
        "Envie o modelo do veículo para eu buscar a bateria indicada, "
        "ou use o menu de opções."
    )
    update.message.reply_text(msg, parse_mode="Markdown")

def echo(update, context):
    """Handler que responde a qualquer texto"""
    txt = update.message.text or ""
    low = txt.lower()

    if low == "ping":
        update.message.reply_text("pong")
        return

    keywords = ["corolla", "onix", "gol", "hb20", "civic", "uno", "toro", "hilux"]
    if any(k in low for k in keywords):
        update.message.reply_text(
            f"🔎 Buscando bateria ideal para *{txt}*...\n"
            f"➡️ Resposta simulada: *M60GD*",
            parse_mode="Markdown"
        )
    else:
        update.message.reply_text(f"Você disse: {txt}")

# adiciona handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

# ----------------------------
# ROTAS FLASK
# ----------------------------
@app.route('/')
def index():
    return "🤖 FACILITADOR LITE - ativo"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    """Recebe POST do Telegram e envia update ao dispatcher"""
    try:
        raw = request.get_json(force=True)
        if not raw:
            logger.warning("POST sem JSON recebido")
            return Response("Sem JSON", status=400)

        update = Update.de_json(raw, bot)
        logger.info(f"Recebido update: {update.update_id}")
        dispatcher.process_update(update)
    except Exception as e:
        logger.exception("Erro ao processar update: %s", e)
        return Response("Erro interno", status=200)
    return Response("OK", status=200)

# ----------------------------
# EXECUÇÃO LOCAL / RENDER
# ----------------------------
if __name__ == "__main__":
    logger.info(f"Iniciando FACILITADOR LITE na porta {PORT}")
    app.run(host="0.0.0.0", port=PORT)
