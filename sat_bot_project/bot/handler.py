from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from django.conf import settings
import logging
from . import registerlogin, main

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import necessary handlers
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await registerlogin.show_auth_menu(update, context)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    data = query.data
    
    # Authentication callbacks
    if data == 'register':
        await registerlogin.handle_register(update, context)
    elif data == 'login':
        await registerlogin.handle_login(update, context)
    elif data == 'logout':
        await registerlogin.handle_logout(update, context)
    
    # Main menu callbacks
    elif data == 'main_menu':
        await main.show_main_menu(update, context)
    elif data.startswith('test_'):
        test_id = int(data.split('_')[1])
        await main.start_test(update, context, test_id)
    elif data == 'my_results':
        await main.show_my_results(update, context)
    
    # Test navigation callbacks
    elif data.startswith('answer_'):
        answer = data.split('_')[1]
        await main.answer_question(update, context, answer)
    elif data == 'next_question':
        await main.next_question(update, context)
    elif data == 'prev_question':
        await main.prev_question(update, context)
    elif data == 'finish_module':
        module = context.user_data.get('current_module', 1)
        if module == 1:
            await main.end_module(update, context)
        else:
            await main.end_test(update, context)
    elif data == 'start_module2':
        await main.start_module2(update, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages and contact sharing"""
    action = context.user_data.get('action')
    
    # Handle contact sharing (phone number button)
    if update.message.contact:
        if action in ['register', 'login']:
            await registerlogin.process_phone(update, context)
        else:
            await update.message.reply_text(
                'Please use the menu buttons or type /start to begin.'
            )
    # Handle text messages
    elif update.message.text:
        if action in ['register', 'login']:
            await registerlogin.process_phone(update, context)
        elif action == 'get_first_name':
            await registerlogin.process_first_name(update, context)
        elif action == 'get_last_name':
            await registerlogin.process_last_name(update, context)
        else:
            await update.message.reply_text(
                'Please use the menu buttons or type /start to begin.'
            )

def run():
    """Main function to run the bot"""
    # Get token from Django settings
    token = settings.TELEGRAM_BOT_TOKEN
    
    if not token or token == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set TELEGRAM_BOT_TOKEN in settings.py")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers - ORDER MATTERS!
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Contact handler (must come before text handler)
    application.add_handler(MessageHandler(filters.CONTACT, message_handler))
    
    # Text handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Start the bot
    logger.info('Bot is running...')
    application.run_polling(allowed_updates=Update.ALL_TYPES)



