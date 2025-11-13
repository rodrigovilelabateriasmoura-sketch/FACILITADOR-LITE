import os
import asyncio
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
import logging

# ---------------------------
# CONFIGURAÇÕES GERAIS
# ---------------------------
# Nota: É altamente recomendável usar variáveis de ambiente para tokens e URLs.
BOT_TOKEN = "8279037967:AAGWG7SnQFAT-GdpJvRTsL9rYW1ZFXgwraA"
# É vital que esta URL seja a URL pública do seu serviço no Render
WEBHOOK_URL = "https://facilitador-lite.onrender.com/webhooks/telegram/action"

app = Flask(__name__)
# Configuração de logging
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

    if update.message:
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
    if update.message:
        texto = update.message.text
        user = update.message.from_user.first_name
        await update.message.reply_text(f"Olá {user}, recebi: '{texto}' 😉")


# ---------------------------
# FUNÇÕES DE SETUP ROBUSTAS
# ---------------------------
async def setup_ptb_application():
    """Inicializa, configura e define o webhook do Application do PTB (Assíncrono)."""
    global application
    
    # 1. Cria a instância do Application
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # 2. Adiciona Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_mensagem))
    
    # 3. Inicializa os componentes internos (A CORREÇÃO PRINCIPAL)
    # Isso é crucial para ambientes de webhook fora do loop de Application.run()
    await application.initialize()
    logger.info("Application do PTB inicializada com sucesso.")
    
    # 4. Define o webhook
    try:
        current_webhook = await application.bot.get_webhook_info()
        if current_webhook.url != WEBHOOK_URL:
             # Remove webhook antigo e define o novo
            await application.bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"Webhook definido para: {WEBHOOK_URL}")
        else:
            logger.info("Webhook já está definido corretamente.")
    except Exception as e:
        logger.error(f"Erro ao definir o webhook: {e}")

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
    e delega o processamento ao PTB de forma ASSÍNCRONA.
    """
    global application
    
    if not application:
        logger.error("Aplicação do PTB não inicializada. Retornando 500.")
        return jsonify({"status": "error", "message": "Application not initialized"}), 500

    if request.method == "POST":
        try:
            update_data = request.get_json(force=True)
            
            # 1. Cria o objeto Update do PTB
            update = Update.de_json(update_data, application.bot)
            
            # 2. Processa o update de forma assíncrona
            asyncio.run(application.process_update(update))
            
            return "OK", 200
        
        except Exception as e:
            # Captura exceções durante o processamento
            logger.error(f"Erro ao processar o update (exceção): {e}")
            return jsonify({"status": "error", "message": "Update processing failed"}), 500
    
    return "OK", 200

# ---------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------
if __name__ == "__main__":
    
    # 1. Inicializa o PTB e o webhook de forma assíncrona
    try:
        asyncio.run(setup_ptb_application())
    except Exception as e:
        logger.error(f"Falha crítica ao configurar o PTB e o Webhook: {e}")
        
    # 2. Inicia o servidor Flask
    port = int(os.environ.get("PORT", 5000))
    
    logger.info(f"Iniciando servidor Flask na porta {port}")
    app.run(host="0.0.0.0", port=port)
