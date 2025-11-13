# main.py
import os
import asyncio
import logging
import threading
from flask import Flask, request, jsonify, g
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import httpx

# ---------------------------
# CONFIGURAÇÕES
# ---------------------------
BOT_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
WEBHOOK_URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"

app = Flask(__name__)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Globais
application = None
bot_loop = None
bot_thread = None


# ---------------------------
# LOOP DO BOT EM THREAD
# ---------------------------
def start_bot_event_loop():
    global bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    logger.info("Loop do bot iniciado em thread dedicada.")
    bot_loop.run_forever()


# ---------------------------
# HANDLERS
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("ESTOQUE", callback_data="estoque")],
        [InlineKeyboardButton("FINANCEIRO", callback_data="financeiro")],
        [InlineKeyboardButton("FATURAMENTO", callback_data="faturamento")],
        [InlineKeyboardButton("SUCATA", callback_data="sucata")],
        [InlineKeyboardButton("GARANTIA", callback_data="garantia")],
        [InlineKeyboardButton("MARKETING", callback_data="marketing")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "*FACILITADOR LITE*\nEscolha uma opção:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    respostas = {
        "estoque": "*Estoque*\nEnvie código ou modelo.",
        "financeiro": "*Financeiro*\nPagamentos e limites.",
        "faturamento": "*Faturamento*\nNotas e pedidos.",
        "sucata": "*Sucata*\nEnvie número do lote.",
        "garantia": "*Garantia*\nSérie ou NF.",
        "marketing": "*Marketing*\nCampanhas."
    }

    await query.edit_message_text(
        text=respostas.get(data, "Opção inválida."),
        parse_mode="Markdown"
    )


async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user = update.message.from_user.first_name
        texto = update.message.text
        await update.message.reply_text(f"Olá {user}, recebi: '{texto}'")


# ---------------------------
# SETUP DO BOT
# ---------------------------
async def setup_ptb_application():
    global application
    client = httpx.AsyncClient()
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .http_client(client)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem))

    await application.initialize()
    logger.info("Bot inicializado.")

    try:
        info = await application.bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            await application.bot.set_webhook(url=WEBHOOK_URL)
            logger.info("Webhook configurado.")
        else:
            logger.info("Webhook já OK.")
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")


# ---------------------------
# INICIALIZAÇÃO SEGURA (Flask 3.0+)
# ---------------------------
def initialize_bot():
    global application
    if application is not None:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup_ptb_application())
        logger.info("Bot inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao inicializar bot: {e}")
        raise
    finally:
        loop.close()


@app.before_request
def ensure_bot_initialized():
    if not hasattr(g, 'bot_initialized'):
        initialize_bot()
        g.bot_initialized = True


# ---------------------------
# ENDPOINTS
# ---------------------------
@app.route("/")
def home():
    return "FACILITADOR LITE ativo!"


@app.route("/webhooks/telegram/action", methods=["POST"])
def telegram_webhook():
    global application, bot_loop

    if not application:
        return jsonify({"error": "Bot não inicializado"}), 500

    if request.method == "POST":
        try:
            update_data = request.get_json(force=True)
            update = Update.de_json(update_data, application.bot)
            if not update:
                return "Update inválido", 400

            future = asyncio.run_coroutine_threadsafe(
                application.process_update(update),
                bot_loop
            )
            future.result(timeout=10)
            return "OK", 200
        except Exception as e:
            logger.error(f"Erro: {e}")
            return jsonify({"error": str(e)}), 500

    return "Método não permitido", 405


# ---------------------------
# INICIA O LOOP DO BOT
# ---------------------------
bot_thread = threading.Thread(target=start_bot_event_loop, daemon=True)
bot_thread.start()
import time
time.sleep(0.1)  # Garante que o loop inicie


# ---------------------------
# EXECUÇÃO LOCAL
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
