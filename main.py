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
import httpx # Importar httpx para a correção

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
            "
