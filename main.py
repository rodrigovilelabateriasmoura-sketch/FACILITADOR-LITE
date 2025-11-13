# main.py
import os
import asyncio
import logging
import time
import threading
from flask import Flask, request, jsonify
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

# Logging Avançado (para Render: logs em stdout/stderr com rotação)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variáveis globais
application = None
bot_loop = None
bot_thread = None
bot_running = False

# ---------------------------
# HANDLERS (Mesmos da versão anterior)
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
# SETUP DO BOT COM RESTART AUTOMÁTICO
# ---------------------------
async def setup_bot():
    global application, bot_running
    try:
        client = httpx.AsyncClient()
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .http_client(client)
            .build()
        )

        # Adiciona handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem))

        # Inicializa e start
        await application.initialize()
        await application.start()

        # Configura webhook
        info = await application.bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            await application.bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"Webhook configurado: {WEBHOOK_URL}")
        else:
            logger.info("Webhook já configurado.")

        bot_running = True
        logger.info("Bot iniciado com sucesso.")
    except Exception as e:
        bot_running = False
        logger.error(f"Erro ao iniciar bot: {e}")
        raise

# ---------------------------
# FUNÇÃO DE RESTART AUTOMÁTICO
# ---------------------------
def bot_supervisor():
    global bot_loop, bot_running
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)

    while True:
        if not bot_running:
            logger.warning("Detectado falha no bot. Reiniciando...")
            try:
                bot_loop.run_until_complete(setup_bot())
            except Exception as e:
                logger.error(f"Falha no restart: {e}. Tentando novamente em 10s...")
                time.sleep(10)
        else:
            time.sleep(5)  # Verifica a cada 5s se o bot ainda roda

# ---------------------------
# ENDPOINTS
# ---------------------------
@app.route("/")
def home():
    return "FACILITADOR LITE ativo! Bot online."

@app.route("/webhooks/telegram/action", methods=["POST"])
async def telegram_webhook():
    global application
    if not application or not bot_running:
        return jsonify({"error": "Bot não inicializado ou offline"}), 500

    if request.method == "POST":
        try:
            update_data = request.get_json(force=True)
            update = Update.de_json(update_data, application.bot)
            if not update:
                return "Update inválido", 400

            # Processa a atualização no mesmo loop
            await application.process_update(update)
            return "OK", 200
        except Exception as e:
            logger.error(f"Erro no webhook: {e}")
            return jsonify({"error": str(e)}), 500
    return "Método não permitido", 405

# ---------------------------
# HEALTH CHECK ENDPOINT (para Render monitorar)
# ---------------------------
@app.route("/health")
def health_check():
    if bot_running:
        return jsonify({"status": "healthy", "bot": "running"}), 200
    else:
        return jsonify({"status": "unhealthy", "bot": "offline"}), 503

# ---------------------------
# INICIALIZAÇÃO DO BOT NO STARTUP
# ---------------------------
@app.before_first_request
def initialize_bot():
    global bot_thread
    bot_thread = threading.Thread(target=bot_supervisor, daemon=True)
    bot_thread.start()
    logger.info("Supervisor do bot iniciado (com restart automático).")

# ---------------------------
# EXECUÇÃO
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
