# main.py
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import logging

# ---------------------------
# CONFIGURAÇÕES GERAIS
# ---------------------------
BOT_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
WEBHOOK_URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------
# HANDLERS
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensagem inicial e menu principal"""
    keyboard = [
        [InlineKeyboardButton("📦 ESTOQUE", callback_data="estoque")],
        [InlineKeyboardButton("💰 FINANCEIRO", callback_data="financeiro")],
        [InlineKeyboardButton("🧾 FATURAMENTO", callback_data="faturamento")],
        [InlineKeyboardButton("🔧 SUCATA", callback_data="sucata")],
        [InlineKeyboardButton("🛡️ GARANTIA", callback_data="garantia")],
        [InlineKeyboardButton("📢 MARKETING", callback_data="marketing")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 *FACILITADOR LITE*\nEscolha uma das opções abaixo:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a botões do menu"""
    query = update.callback_query
    await query.answer()

    data = query.data

    respostas = {
        "estoque": "📦 *Consulta de Estoque*\nEnvie o código da bateria ou o modelo do veículo.",
        "financeiro": "💰 *Financeiro*\nAqui você poderá consultar status de pagamentos e limites.",
        "faturamento": "🧾 *Faturamento*\nVerifique notas emitidas e pedidos em andamento.",
        "sucata": "🔧 *SUCATA*\nEnvie o número do lote para análise de descarte.",
        "garantia": "🛡️ *GARANTIA*\nEnvie o número de série ou nota fiscal para validação.",
        "marketing": "📢 *MARKETING*\nEnvie o nome da campanha ou solicitação de material."
    }

    texto = respostas.get(data, "Selecione uma opção válida.")
    await query.edit_message_text(text=texto, parse_mode="Markdown")


async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resposta genérica a mensagens"""
    texto = update.message.text
    user = update.message.from_user.first_name
    await update.message.reply_text(f"Olá {user}, recebi: '{texto}' 😉")


# ---------------------------
# FUNÇÃO PRINCIPAL
# ---------------------------
async def init_app():
    """Inicializa bot e webhook"""
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # Comandos e handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem))

    # Configuração do webhook
    await application.bot.set_webhook(url=WEBHOOK_URL)

    return application


# ---------------------------
# FLASK ENDPOINTS
# ---------------------------
@app.route("/")
def home():
    return "🤖 FACILITADOR LITE ativo e rodando no Render 🚀"


@app.route("/webhooks/telegram/action", methods=["POST"])
async def telegram_webhook():
    """Recebe updates do Telegram"""
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, bot=app.bot_instance.bot)
    await app.bot_instance.process_update(update)
    return "OK", 200


# ---------------------------
# EXECUÇÃO
# ---------------------------
if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    app.bot_instance = loop.run_until_complete(init_app())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
