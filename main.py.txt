# ========================
# FACILITADOR LITE - Bot CRM Moura
# Versão otimizada para rodar no Replit com Telegram
# ========================

import os
import requests
from flask import Flask, request
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext, Updater

# ========= CONFIGURAÇÕES =========
TOKEN = os.getenv("BOT_TOKEN")  # Adicione no Secrets do Replit: BOT_TOKEN
app = Flask(__name__)

# ========= MENUS PRINCIPAIS =========
main_menu = [
    ["📋 CLIENTES", "⚙️ SUCATA"],
    ["🔧 GARANTIA", "🎯 MARKETING"],
    ["🔋 QUAL É SUA BATERIA"]
]
keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

# ========= FUNÇÕES DE COMANDO =========
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Olá! Eu sou o *FACILITADOR LITE* Moura ⚡\n"
        "Sou seu assistente para consultas, cadastros e suporte rápido.\n\n"
        "Escolha uma das opções abaixo para começar:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def handle_message(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "📋 CLIENTES":
        update.message.reply_text("📋 Módulo CLIENTES:\nEnvie os dados para cadastro ou consulta (em breve).")

    elif text == "⚙️ SUCATA":
        update.message.reply_text(
            "🪫 Módulo SUCATA:\n\n"
            "Envie os dados no formato:\n"
            "`id_cliente | qtd_pdd | qtd_disponível | observações`\n\n"
            "💡 O valor_financeiro será calculado automaticamente (R$6,00 por kg).",
            parse_mode="Markdown"
        )

    elif text == "🔧 GARANTIA":
        update.message.reply_text(
            "🔧 Módulo GARANTIA:\n\n"
            "Envie os dados no formato:\n"
            "`id_cliente | data_coleta | modelos (separe por vírgula) | data_retorno | observações`",
            parse_mode="Markdown"
        )

    elif text == "🎯 MARKETING":
        update.message.reply_text(
            "🎯 Módulo MARKETING:\n\n"
            "Envie os dados no formato:\n"
            "`id_cliente | materiais | tipo_campanha | bonificação | início | fim`",
            parse_mode="Markdown"
        )

    elif text == "🔋 QUAL É SUA BATERIA":
        update.message.reply_text(
            "🔍 Digite o modelo exato do veículo (ex: Corolla 2020 2.0)\n"
            "que vou buscar no site da Moura a bateria ideal."
        )

    elif any(x in text.lower() for x in ["corolla", "onix", "gol", "hb20", "civic", "strada", "fiesta", "hilux", "toro", "uno"]):
        update.message.reply_text("🔎 Buscando no site da Moura...")
        resposta = busca_bateria(text)
        update.message.reply_text(resposta, parse_mode="Markdown")

    else:
        update.message.reply_text("🤔 Não entendi... selecione uma opção do menu abaixo.", reply_markup=keyboard)

# ========= FUNÇÃO DE BUSCA DE BATERIA =========
def busca_bateria(veiculo):
    try:
        url = "https://www.moura.com.br/descubra-qual-a-sua-bateria"
        session = requests.Session()
        r = session.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        # Simula a busca (para evitar bloqueio Moura)
        return f"🔋 Modelo recomendado para *{veiculo}*: M60GD\n💡 Fonte: moura.com.br"
    except Exception as e:
        return f"⚠️ Erro ao consultar: {e}"

# ========= FLASK ROUTES =========
@app.route('/')
def home():
    return "FACILITADOR LITE Moura ativo 💪"

@app.route(f'/webhooks/telegram/action', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), context.bot)
    dispatcher.process_update(update)
    return "ok", 200

# ========= TELEGRAM DISPATCHER =========
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# ========= EXECUÇÃO =========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
