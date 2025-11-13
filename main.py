import os
import asyncio
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
# Nota: É altamente recomendável usar variáveis de ambiente para tokens e URLs.
# BOT_TOKEN = os.environ.get("BOT_TOKEN", "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA")
# WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://facilitador-lite.onrender.com/webhooks/telegram/action")
BOT_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
WEBHOOK_URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"

app = Flask(__name__)
# Configuração de logging (melhorada para ser mais informativa)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Variável global para armazenar a instância do Application do PTB
application = None 

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

    # Verifica se a atualização é de uma mensagem antes de tentar acessar update.message
    if update.message:
        await update.message.reply_text(
            "🤖 *FACILITADOR LITE*\nEscolha uma das opções abaixo:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde a botões do menu"""
    query = update.callback_query
    # Sempre responda à consulta de callback
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
    # Use edit_message_text para modificar a mensagem do botão
    await query.edit_message_text(text=texto, parse_mode="Markdown")


async def receber_mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resposta genérica a mensagens"""
    if update.message:
        texto = update.message.text
        user = update.message.from_user.first_name
        await update.message.reply_text(f"Olá {user}, recebi: '{texto}' 😉")


# ---------------------------
# FUNÇÃO PRINCIPAL DE SETUP
# ---------------------------
def setup_application():
    """Inicializa e configura o Application do python-telegram-bot (síncrono)."""
    global application
    
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # Comandos e handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    # Filtra mensagens de texto que não são comandos
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem))
    
    logger.info("Application do PTB configurada.")
    return application

async def set_initial_webhook(app_instance):
    """Define o webhook de forma assíncrona ao iniciar a aplicação."""
    # Remove qualquer webhook antigo primeiro
    await app_instance.bot.set_webhook(url=None)
    # Define o novo webhook
    await app_instance.bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook definido para: {WEBHOOK_URL}")

# ---------------------------
# FLASK ENDPOINTS
# ---------------------------
@app.route("/")
def home():
    """Endpoint de status para verificar se o serviço está ativo."""
    return "🤖 FACILITADOR LITE ativo e rodando no Render 🚀"


@app.route("/webhooks/telegram/action", methods=["POST"])
def telegram_webhook():
    """
    Recebe updates do Telegram. Esta rota é SÍNCRONA,
    mas executa o processamento do PTB de forma ASSÍNCRONA
    usando asyncio.run().
    """
    global application
    
    if not application:
        logger.error("Aplicação do PTB não inicializada.")
        return "Internal Server Error", 500

    if request.method == "POST":
        update_data = request.get_json(force=True)
        
        # 1. Cria o objeto Update do PTB
        update = Update.de_json(update_data, application.bot)
        
        # 2. Processa o update de forma assíncrona dentro do contexto síncrono do Flask
        try:
            asyncio.run(application.process_update(update))
            return "OK", 200
        except Exception as e:
            logger.error(f"Erro ao processar o update: {e}")
            return "Internal Server Error", 500
    
    return "OK", 200

# ---------------------------
# EXECUÇÃO
# ---------------------------
if __name__ == "__main__":
    
    # 1. Inicializa a aplicação do PTB e os handlers
    application = setup_application()
    
    # 2. Define o webhook inicial de forma assíncrona
    try:
        asyncio.run(set_initial_webhook(application))
    except Exception as e:
        logger.error(f"Erro ao definir o webhook inicial: {e}")

    # 3. Inicia o servidor Flask
    port = int(os.environ.get("PORT", 5000))
    # Para produção, você usaria um WSGI/ASGI como Gunicorn.
    # Em ambientes como o Render, ele pode ser iniciado por gunicorn automaticamente.
    # Para testes locais, o Flask é suficiente.
    logger.info(f"Iniciando servidor Flask na porta {port}")
    app.run(host="0.0.0.0", port=port)
