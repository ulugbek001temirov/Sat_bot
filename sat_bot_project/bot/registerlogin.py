from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from .models import User
from django.db import IntegrityError
from asgiref.sync import sync_to_async

async def show_auth_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show registration/login menu"""
    keyboard = [
        [InlineKeyboardButton("📝 Register", callback_data='register')],
        [InlineKeyboardButton("🔐 Login", callback_data='login')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            '🎓 Welcome to SAT English Practice Bot!\n\n'
            'Please choose an option:',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            '🎓 Welcome to SAT English Practice Bot!\n\n'
            'Please choose an option:',
            reply_markup=reply_markup
        )

async def handle_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle register button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['action'] = 'register'
    
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await query.message.reply_text(
        '📱 Please share your phone number:',
        reply_markup=kb
    )

async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle login button"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['action'] = 'login'
    
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Share phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await query.message.reply_text(
        '📱 Please share your phone number to login:',
        reply_markup=kb
    )

@sync_to_async
def get_user_by_phone(phone):
    """Get user from database"""
    try:
        return User.objects.get(phone=phone)
    except User.DoesNotExist:
        return None

@sync_to_async
def update_user_telegram_id(user, telegram_id):
    """Update user's telegram ID"""
    user.telegram_id = telegram_id
    user.save()
    return user

@sync_to_async
def create_new_user(phone, first_name, last_name, telegram_id):
    """Create new user in database"""
    return User.objects.create(
        phone=phone,
        first_name=first_name,
        last_name=last_name,
        telegram_id=telegram_id
    )

async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process phone number for register/login"""
    # Get phone from contact or text
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip() if update.message.text else None
    
    if not phone:
        await update.message.reply_text(
            '❌ Please provide a valid phone number.',
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    action = context.user_data.get('action')
    telegram_id = update.effective_user.id
    
    # Check if user exists
    user = await get_user_by_phone(phone)
    
    if user:
        # User exists - auto-login regardless of register or login action
        # Update telegram_id if not set
        if not user.telegram_id:
            user = await update_user_telegram_id(user, telegram_id)
        
        context.user_data['user'] = {
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        
        # Always login if user exists
        await update.message.reply_text(
            f'✅ Welcome back, {user.first_name} {user.last_name}!',
            reply_markup=ReplyKeyboardRemove()
        )
        
        from .main import show_main_menu
        await show_main_menu(update, context, is_message=True)
    else:
        # User doesn't exist
        if action == 'login':
            keyboard = [[InlineKeyboardButton('📝 Register Now', callback_data='register')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                '❌ Phone number not found. Please register first.',
                reply_markup=reply_markup
            )
        else:  # register - start registration process
            context.user_data['phone'] = phone
            context.user_data['telegram_id'] = telegram_id
            context.user_data['action'] = 'get_first_name'
            await update.message.reply_text(
                '👤 Please enter your first name:',
                reply_markup=ReplyKeyboardRemove()
            )

async def process_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process first name during registration"""
    first_name = update.message.text.strip() if update.message.text else ""
    
    if not first_name:
        await update.message.reply_text('❌ Please enter a valid first name:')
        return
    
    context.user_data['first_name'] = first_name
    context.user_data['action'] = 'get_last_name'
    await update.message.reply_text('👤 Please enter your last name:')

async def process_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process last name and complete registration"""
    last_name = update.message.text.strip() if update.message.text else ""
    
    if not last_name:
        await update.message.reply_text('❌ Please enter a valid last name:')
        return
    
    phone = context.user_data.get('phone')
    first_name = context.user_data.get('first_name')
    telegram_id = context.user_data.get('telegram_id')
    
    if not all([phone, first_name, telegram_id]):
        await update.message.reply_text(
            '❌ Registration failed. Please start again with /start'
        )
        return
    
    try:
        user = await create_new_user(phone, first_name, last_name, telegram_id)
        
        context.user_data['user'] = {
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        
        await update.message.reply_text(
            f'✅ Registration successful!\n'
            f'Welcome, {first_name} {last_name}! 🎉'
        )
        
        from .main import show_main_menu
        await show_main_menu(update, context, is_message=True)
        
    except IntegrityError:
        await update.message.reply_text(
            '❌ Registration failed. This phone number might already be registered.\n'
            'Please try logging in instead.'
        )
        await show_auth_menu(update, context)
    except Exception as e:
        await update.message.reply_text(
            f'❌ Registration failed: {str(e)}\n'
            'Please try again with /start'
        )

async def handle_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle logout"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    await show_auth_menu(update, context)

