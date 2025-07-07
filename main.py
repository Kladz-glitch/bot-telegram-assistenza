from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)
from datetime import datetime

BOT_TOKEN = '7683254727:AAEzINwfOJU3tZRJdPu-CrIV8GtQyRkpLhE'
OPERATORS_GROUP_ID = -1002527086012

tickets = {}

SCRIVI_MSG = 1

def get_groups_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("GRUPPO WINDTRE", url="https://t.me/wind3_unofficial")],
        [InlineKeyboardButton("GRUPPO VODAFONE", url="https://t.me/vodafone_italia")],
        [InlineKeyboardButton("GRUPPO VERYMOBILE", url="https://t.me/VeryMobileUsersCommunity")],
        [InlineKeyboardButton("GRUPPO FASTWEB", url="https://t.me/fastwebit")],
        [InlineKeyboardButton("GRUPPO COOPVOCE", url="https://t.me/CoopVoce_Community")],
        [InlineKeyboardButton("GRUPPO ILIAD", url="https://t.me/iliaditaliacommunity")],
    ])

def request_confirmation_buttons(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ SI", callback_data=f"conferma_si_{user_id}"),
            InlineKeyboardButton("❌ NO", callback_data=f"conferma_no_{user_id}")
        ]
    ])

def operator_message_buttons(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Scrivi messaggio", callback_data=f"scrivi_{user_id}")
        ]
    ])

async def send_help_and_pin(app):
    help_text = (
        "📌 *Comandi utili per gli operatori:*\n\n"
        "/start - Mostra il messaggio di benvenuto\n"
        "/apri - Apri una nuova richiesta di assistenza\n"
        "/closedchat <id_utente> motivation: <motivo> - Chiudi un ticket con motivazione\n"
        "\nUsa i bottoni nella chat per gestire i ticket."
    )
    try:
        msg = await app.bot.send_message(
            OPERATORS_GROUP_ID,
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
        await app.bot.pin_chat_message(OPERATORS_GROUP_ID, msg.message_id, disable_notification=True)
    except Exception as e:
        print(f"Errore invio/pin messaggio help: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username or update.effective_user.first_name

    welcome_text = (
        f"👋 Ciao @{username}!\n\n"  
        "Sono Mandy🤖​, l’assistente digitale che ti metterà in contatto con un operatore umano.\n\n"  
        "📍 I nostri operatori, tutti con sede in Italia, risponderanno entro 30 minuti al massimo.\n\n"
        "🔧 Per avviare la conversazione con un nostro tecnico esperto, digita il comando: /apri \n\n"
        "📌 IMPORTANTE: Quando avvii la conversazione, indica il gruppo di appartenenza (es. WindTre, Vodafone...) per ricevere assistenza più rapida e mirata.\n\n"
        "⏳ In caso di prolungata inattività, il ticket verrà chiuso automaticamente. Potrai sempre riaprirlo digitando nuovamente /apri.\n\n"
        "📲 Se ti interessa, qui sotto trovi i pulsanti per visualizzare i principali gruppi di telefonia 👇 \n\n"
        "📬 Per ulteriori informazioni:\n\n"  
        "• Comando: /admin nei gruppi \n\n"  
        "• Email:assistenza.operatoritelefonici@protonmail.com \n\n"
        "  ⚠️​ TENIAMO A PRECISARE CHE QUESTO SERVIZIO, NON È ABILITATO AL SERVIZIO DI VENDITA O SEGNALAZIONI tipo: guasti,disservizi della linea etc.. \n\n"
        "🛠️ Aggiornamento bot: 07/07/2025 - ore 00:24\n\n"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_groups_keyboard())

async def apri(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    if user_id in tickets:
        status = tickets[user_id]['status']
        if status == 'aperta':
            await update.message.reply_text("Hai già una conversazione aperta con gli operatori.")
            return
        elif status == 'in_attesa':
            await update.message.reply_text("La tua richiesta è in attesa di conferma da parte degli operatori.")
            return
        elif status == 'chiusa':
            # Riapro il ticket
            tickets[user_id]['status'] = 'in_attesa'
            await update.message.reply_text("✔️ Nuova richiesta inviata, attendi conferma dagli operatori.")
            await context.bot.send_message(
                OPERATORS_GROUP_ID,
                f"👤 L’utente @{username} (ID: `{user_id}`) vuole aprire una chat con te.\n"
                "Vuoi accettare?",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=request_confirmation_buttons(user_id)
            )
            return

    else:
        tickets[user_id] = {
            'status': 'in_attesa',
            'user_name': username,
            'opened_at': datetime.now(),
        }
        await update.message.reply_text("✔️ Richiesta inviata, attendi conferma dagli operatori.")
        await context.bot.send_message(
            OPERATORS_GROUP_ID,
            f"👤 L’utente @{username} (ID: `{user_id}`) vuole aprire una chat con te.\n"
            "Vuoi accettare?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=request_confirmation_buttons(user_id)
        )

async def operator_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    action = parts[0]
    risposta = parts[1]
    user_id = int(parts[2])

    if action == "conferma":
        if risposta == "si":
            if user_id not in tickets:
                await query.edit_message_text("Ticket non trovato o già chiuso.")
                return

            tickets[user_id]['status'] = 'aperta'
            tickets[user_id]['opened_at'] = datetime.now()

            await query.edit_message_text(
                f"✅ Confermato! Puoi ora scrivere con @{tickets[user_id]['user_name']}.",
                reply_markup=operator_message_buttons(user_id)
            )

            try:
                await context.bot.send_message(user_id, "✅ La tua richiesta è stata accettata. Puoi iniziare a scrivere.")
            except Exception as e:
                print(f"Errore invio messaggio all'utente: {e}")

        else:
            if user_id in tickets:
                del tickets[user_id]

            await query.edit_message_text("❌ Richiesta rifiutata dall’operatore.")

            try:
                await context.bot.send_message(user_id, "❌ La tua richiesta è stata rifiutata dagli operatori. Riprova più tardi.")
            except Exception as e:
                print(f"Errore invio messaggio all'utente: {e}")

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text or ""

    ticket = tickets.get(user_id)
    if not ticket:
        await update.message.reply_text("⚠️ Non hai una conversazione attiva con gli operatori. Usa /apri per aprirne una.")
        return

    if ticket['status'] == 'chiusa':
        await update.message.reply_text("⚠️ Il tuo ticket è chiuso. Usa /apri per aprire una nuova richiesta.")
        return

    if ticket['status'] != 'aperta':
        await update.message.reply_text("⚠️ La conversazione non è ancora stata aperta dagli operatori.")
        return

    await context.bot.send_message(
        OPERATORS_GROUP_ID,
        f"💬 Messaggio da @{ticket['user_name']} (ID `{user_id}`):\n\n{text}",
        parse_mode=ParseMode.MARKDOWN
    )

async def operator_write_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    user_id = int(parts[1])

    ticket = tickets.get(user_id)
    if not ticket or ticket['status'] != 'aperta':
        await query.edit_message_text("❌ La conversazione non è aperta o non esiste.")
        return ConversationHandler.END

    context.user_data['target_user_id'] = user_id
    await query.message.reply_text(f"✏️ Scrivi il messaggio da inviare a @{ticket['user_name']} (ID `{user_id}`):")
    return SCRIVI_MSG

async def operator_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('target_user_id')
    if not user_id:
        await update.message.reply_text("❌ Errore interno: nessun utente selezionato.")
        return ConversationHandler.END

    ticket = tickets.get(user_id)
    if not ticket:
        await update.message.reply_text("❌ Ticket non trovato.")
        return ConversationHandler.END

    if ticket['status'] == 'chiusa':
        await update.message.reply_text("⚠️ Il ticket è chiuso. Non puoi inviare messaggi.")
        return ConversationHandler.END

    testo = update.message.text
    operator_name = update.effective_user.first_name or "Operatore"

    try:
        await context.bot.send_message(user_id, f"📩 Messaggio dall’operatore {operator_name}:\n\n{testo}")
        await update.message.reply_text("✅ Messaggio inviato all’utente.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nell’invio del messaggio: {e}")

    return ConversationHandler.END

async def closedchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != OPERATORS_GROUP_ID:
        await update.message.reply_text("❌ Comando disponibile solo nel gruppo operatori.")
        return

    text = update.message.text

    try:
        split_index = text.index("motivation:")
    except ValueError:
        await update.message.reply_text("❌ Usa il formato: /closedchat <id_utente> motivation: <motivo>")
        return

    user_id_str = text[len("/closedchat "):split_index].strip()
    motivo = text[split_index + len("motivation:"):].strip()

    if not user_id_str.isdigit():
        await update.message.reply_text("❌ ID utente non valido.")
        return

    user_id = int(user_id_str)

    if user_id not in tickets or tickets[user_id]['status'] == 'chiusa':
        await update.message.reply_text("❌ Questo ticket non esiste o è già chiuso.")
        return

    tickets[user_id]['status'] = 'chiusa'
    tickets[user_id]['closed_reason'] = motivo

    await update.message.reply_text(
        f"❌ Ticket ID {user_id} chiuso.\nMotivazione: {motivo}"
    )

    try:
        await context.bot.send_message(
            user_id,
            f"❌ Il tuo ticket è stato chiuso dagli operatori.\nMotivazione:\n{motivo}"
        )
    except Exception as e:
        print(f"Errore invio messaggio di chiusura all'utente: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END

async def on_startup(app):
    await send_help_and_pin(app)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.post_init = on_startup

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(operator_write_start, pattern="^scrivi_")],
        states={
            SCRIVI_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, operator_send_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("apri", apri))
    app.add_handler(CommandHandler("closedchat", closedchat_command))
    app.add_handler(CallbackQueryHandler(operator_callback, pattern="^conferma_"))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.Chat(OPERATORS_GROUP_ID)), user_message))

    print("Bot avviato")
    app.run_polling()

if __name__ == "__main__":
    main()
