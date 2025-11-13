import os
import asyncio
import logging
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
# CONFIGURAÇÕES GERAIS
# ---------------------------
BOT_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
WEBHOOK_URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variáveis globais
application = None
bot_loop = None
bot_thread = None


# ---------------------------
# FUNÇÃO: Iniciar loop assíncrono em thread separada
# ---------------------------
def start_bot_event_loop():
    global bot_loop
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    logger.info("Event loop do bot iniciado em thread dedicada.")
    bot_loop.run_forever()


# ---------------------------
# HANDLERS DO BOT
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
            "*FACILITADOR LITE*\nEscolha uma das opções abaixo:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    respostas = {
        "estoque": "*Consulta de Estoque*\nEnvie o código da bateria ou o modelo do veículo.",
        "financeiro": "*Financeiro*\nAqui você poderá consultar status de pagamentos e limites.",
        "faturamento": "*Faturamento*\nVerifique notas emitidas e pedidos em andamento.",
        "sucata": "*SUCATA*\nEnvie o número do lote para análise de descarte.",
        "garantia": "*GARANTIA*\nEnvie o número de série ou nota fiscal para validação.",
        "marketing": "*MARKETING*\nEnvie o nome da campanha ou solicitação de material."
    }

    texto = respostas.get(data, "Selecione uma opção válida.")
    await query.edit_message_text(text=texto, parse_mode="Markdown")


async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        texto = update.message.text
        user = update.message.from_user.first_name
        await update.message.reply_text(f"Olá {user}, recebi: '{texto}'")


# ---------------------------
# SETUP DO BOT (assíncrono, mas chamado de forma síncrona)
# ---------------------------
async def setup_ptb_application():
    global application

    # Cliente HTTP assíncrono (sem event_loop obsoleto)
    client = httpx.AsyncClient()

    # Cria o Application
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

    # Inicializa
    await application.initialize()
    logger.info("Application do PTB inicializada.")

    # Configura webhook
    try:
        webhook_info = await application.bot.get_webhook_info()
        if webhook_info.url != WEBHOOK_URL:
            await application.bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"Webhook configurado: {WEBHOOK_URL}")
        else:
            logger.info("Webhook já está correto.")
    except Exception as e:
        logger.error(f"Erro ao configurar webhook: {e}")


# ---------------------------
# INICIALIZAÇÃO DO BOT (chamado uma vez)
# ---------------------------
def initialize_bot():
    global application
    if application is not None:
        return

    try:
        # Cria loop temporário para setup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(setup_ptb_application())
        loop.close()
        logger.info("Bot inicializado com sucesso.")
    except Exception as e:
        logger.error(f"Falha crítica ao inicializar o bot: {e}")
        raise


# Registra inicialização antes da primeira requisição
app.before_first_request(initialize_bot)


# ---------------------------
# FLASK ENDPOINTS
# ---------------------------
@app.route("/")
def home():
    return "FACILITADOR LITE ativo e rodando no Render"


@app.route("/webhooks/telegram/action", methods=["POST"])
def telegram_webhook():
    global application, bot_loop

    if not application:
        logger.error("Bot não inicializado.")
        return jsonify({"error": "Bot not initialized"}), 500

    if request.method == "POST":
        try:
            update_data = request.get_json(force=True)
            update = Update.de_json(update_data, application.bot)

            if not update:
                return "Invalid update", 400

            # Envia update para o loop do bot em thread segura
            future = asyncio.run_coroutine_threadsafe(
                application.process_update(update),
                bot_loop
            )
            # Opcional: aguardar com timeout
            future.result(timeout=10)

            return "OK", 200

        except Exception as e:
            logger.error(f"Erro ao processar update: {e}")
            return jsonify({"error": str(e)}), 500

    return "Method not allowed", 405


# ---------------------------
# INICIALIZAÇÃO DO LOOP DO BOT
# ---------------------------
# Inicia o loop assíncrono em uma thread separada ANTES do Flask
if not bot_thread:
    bot_thread = threading.Thread(target=start_bot_event_loop, daemon=True)
    bot_thread.start()
    # Pequena pausa para garantir que o loop inicie
    import time
    time.sleep(0.1)


# ---------------------------
# EXECUÇÃO LOCAL (para testes)
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Iniciando Flask na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
