from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from .models import Test, Question, TestResult, User
import asyncio
from asgiref.sync import sync_to_async

MODULE_TIME_LIMIT = 27 * 60  # 27 minutes in seconds

def calculate_score(m1_correct, m1_total, m2_correct, m2_total):
    """Calculate estimated SAT score"""
    total_correct = m1_correct + m2_correct
    total_questions = m1_total + m2_total
    percentage = (total_correct / total_questions) * 100
    estimated_score = int(200 + (percentage / 100) * 600)
    return estimated_score

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_message=False):
    """Show main menu with test selection"""
    user = context.user_data.get('user')
    
    # Get all complete and active tests
    tests = await sync_to_async(list)(Test.objects.filter(is_complete=True, is_active=True).order_by('-created_date'))
    
    keyboard = []
    for test in tests:
        keyboard.append([InlineKeyboardButton(
            f"📚 {test.name}", 
            callback_data=f'test_{test.id}'
        )])
    
    keyboard.append([InlineKeyboardButton("📊 My Results", callback_data='my_results')])
    keyboard.append([InlineKeyboardButton("🚪 Logout", callback_data='logout')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f'👋 Welcome, {user["first_name"]} {user["last_name"]}!\n\n'
    if tests:
        text += '📋 Choose a test to start practicing:'
    else:
        text += '⚠️ No tests available yet. Please check back later.'
    
    if is_message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE, test_id: int):
    """Start a test"""
    query = update.callback_query
    await query.answer()
    
    try:
        test = await sync_to_async(Test.objects.get)(id=test_id, is_complete=True, is_active=True)
    except Test.DoesNotExist:
        await query.edit_message_text('❌ Test not found or not available.')
        return
    
    context.user_data['test_id'] = test_id
    context.user_data['test_name'] = test.name
    context.user_data['current_module'] = 1
    context.user_data['current_question'] = 0
    context.user_data['answers'] = {}
    context.user_data['module1_start'] = datetime.now()
    
    await query.edit_message_text(
        f'📚 Starting: {test.name}\n\n'
        f'⏱ Module 1: 27 minutes\n'
        f'📝 27 questions\n\n'
        f'Get ready...'
    )
    
    await asyncio.sleep(2)
    await show_question(update, context)

async def show_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display current question"""
    query = update.callback_query
    await query.answer()
    
    test_id = context.user_data['test_id']
    module = context.user_data['current_module']
    q_index = context.user_data['current_question']
    
    # Get questions for current module
    questions = await sync_to_async(list)(Question.objects.filter(
        test_id=test_id, 
        module=module
    ).order_by('question_number'))
    
    if q_index >= len(questions):
        if module == 1:
            await end_module(update, context)
        else:
            await end_test(update, context)
        return
    
    question = questions[q_index]
    
    # Calculate time remaining
    if module == 1:
        start_time = context.user_data['module1_start']
    else:
        start_time = context.user_data['module2_start']
    
    elapsed = (datetime.now() - start_time).total_seconds()
    remaining = MODULE_TIME_LIMIT - elapsed
    
    if remaining <= 0:
        if module == 1:
            await end_module(update, context)
        else:
            await end_test(update, context)
        return
    
    minutes_remaining = int(remaining // 60)
    seconds_remaining = int(remaining % 60)
    
    # Get current answer
    answer_key = f'module{module}_q{q_index}'
    current_answer = context.user_data['answers'].get(answer_key)
    
    # Build question text
    text = f'⏱ Module {module} - Time: {minutes_remaining}:{seconds_remaining:02d}\n\n'
    text += f'Question {q_index + 1}/{len(questions)}\n\n'
    text += f'{question.question_text}\n\n'
    
    # Add options to the message text
    text += 'Options:\n'
    for option_letter in ['A', 'B', 'C', 'D']:
        option_text = getattr(question, f'option_{option_letter.lower()}')
        prefix = '✅ ' if current_answer == option_letter else ''
        text += f'{prefix}{option_letter}) {option_text}\n'
    text += '\n'
    
    # Build keyboard with options
    keyboard = []
    for option_letter in ['A', 'B', 'C', 'D']:
        prefix = '✅ ' if current_answer == option_letter else ''
        keyboard.append([InlineKeyboardButton(
            f'{prefix}{option_letter}',
            callback_data=f'answer_{option_letter}'
        )])
    
    # Navigation buttons
    nav_buttons = []
    if q_index > 0:
        nav_buttons.append(InlineKeyboardButton('⬅️ Previous', callback_data='prev_question'))
    if q_index < len(questions) - 1:
        nav_buttons.append(InlineKeyboardButton('Next ➡️', callback_data='next_question'))
    else:
        nav_buttons.append(InlineKeyboardButton('✅ Finish Module', callback_data='finish_module'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.delete_message()
    
    if question.image:
        with open(question.image.path, 'rb') as photo_file:
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=photo_file,
                caption=text,
                reply_markup=reply_markup
            )
    else:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=reply_markup
        )

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE, answer: str):
    """Record answer and refresh question display"""
    module = context.user_data['current_module']
    q_index = context.user_data['current_question']
    answer_key = f'module{module}_q{q_index}'
    
    context.user_data['answers'][answer_key] = answer
    await show_question(update, context)

async def next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Move to next question"""
    query = update.callback_query
    await query.answer()
    
    test_id = context.user_data['test_id']
    module = context.user_data['current_module']
    
    questions_count = await sync_to_async(Question.objects.filter(test_id=test_id, module=module).count)()
    
    if context.user_data['current_question'] < questions_count - 1:
        context.user_data['current_question'] += 1
        await show_question(update, context)

async def prev_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Move to previous question"""
    query = update.callback_query
    await query.answer()
    
    if context.user_data['current_question'] > 0:
        context.user_data['current_question'] -= 1
        await show_question(update, context)

async def end_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End current module and show results"""
    query = update.callback_query
    await query.answer()
    
    test_id = context.user_data['test_id']
    
    # Calculate Module 1 results
    m1_total = await sync_to_async(Question.objects.filter(test_id=test_id, module=1).count)()
    questions = await sync_to_async(list)(Question.objects.filter(test_id=test_id, module=1).order_by('question_number'))
    
    m1_correct = 0
    
    for i, question in enumerate(questions):
        answer_key = f'module1_q{i}'
        user_answer = context.user_data['answers'].get(answer_key)
        if user_answer == question.correct_answer:
            m1_correct += 1
    
    # Calculate time taken
    elapsed = (datetime.now() - context.user_data['module1_start']).total_seconds()
    context.user_data['module1_time'] = int(elapsed)
    context.user_data['module1_results'] = (m1_correct, m1_total)
    
    await query.edit_message_text(
        f'✅ Module 1 Complete!\n\n'
        f'Results: {m1_correct}/{m1_total}\n'
        f'Time: {int(elapsed // 60)} minutes {int(elapsed % 60)} seconds\n\n'
        f'Get ready for Module 2...'
    )
    
    await asyncio.sleep(3)
    
    # Start Module 2
    context.user_data['current_module'] = 2
    context.user_data['current_question'] = 0
    
    keyboard = [[InlineKeyboardButton('Start Module 2 ▶️', callback_data='start_module2')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f'🔄 Module 2\n\n'
        f'⏱ Time: 27 minutes\n'
        f'📝 Questions: 27\n\n'
        f'Ready?',
        reply_markup=reply_markup
    )

async def start_module2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Module 2"""
    context.user_data['module2_start'] = datetime.now()
    await show_question(update, context)

async def end_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """End test and save results"""
    query = update.callback_query
    await query.answer()
    
    test_id = context.user_data['test_id']
    phone = context.user_data['user']['phone']
    
    # Calculate Module 2 results
    m2_total = await sync_to_async(Question.objects.filter(test_id=test_id, module=2).count)()
    questions = await sync_to_async(list)(Question.objects.filter(test_id=test_id, module=2).order_by('question_number'))
    m2_correct = 0
    
    for i, question in enumerate(questions):
        answer_key = f'module2_q{i}'
        user_answer = context.user_data['answers'].get(answer_key)
        if user_answer == question.correct_answer:
            m2_correct += 1
    
    # Calculate time taken
    elapsed = (datetime.now() - context.user_data['module2_start']).total_seconds()
    m2_time = int(elapsed)
    
    m1_correct, m1_total = context.user_data['module1_results']
    m1_time = context.user_data['module1_time']
    
    estimated_score = calculate_score(m1_correct, m1_total, m2_correct, m2_total)
    
    # Save results to database
    user = await sync_to_async(User.objects.get)(phone=phone)
    test = await sync_to_async(Test.objects.get)(id=test_id)
    
    await sync_to_async(TestResult.objects.create)(
        user=user,
        test=test,
        module1_correct=m1_correct,
        module1_total=m1_total,
        module2_correct=m2_correct,
        module2_total=m2_total,
        estimated_score=estimated_score,
        module1_time_taken=m1_time,
        module2_time_taken=m2_time
    )
    
    result_text = (
        f'🎉 Test Complete!\n\n'
        f'📊 Your Results:\n'
        f'━━━━━━━━━━━━━━\n'
        f'Module 1: {m1_correct}/{m1_total}\n'
        f'Module 2: {m2_correct}/{m2_total}\n'
        f'━━━━━━━━━━━━━━\n'
        f'📈 Estimated Score: {estimated_score}/800\n\n'
        f'Great job! Keep practicing to improve your score. 💪'
    )
    
    keyboard = [[InlineKeyboardButton('🏠 Main Menu', callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(result_text, reply_markup=reply_markup)

async def show_my_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's test results"""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data.get('user')
    if not user:
        await query.edit_message_text('❌ Please log in first.')
        return
    
    # Get user's results
    results = await sync_to_async(list)(TestResult.objects.filter(user__phone=user['phone']).select_related('test').order_by('-test_date'))
    
    if not results:
        text = '📊 You haven\'t taken any tests yet.\n\nChoose a test from the main menu to get started!'
        keyboard = [[InlineKeyboardButton('🏠 Main Menu', callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
        return
    
    # Format results
    text = '📊 Your Test Results:\n\n'
    for i, result in enumerate(results, 1):
        text += f'#{i} - {result.test.name}\n'
        text += f'📅 Date: {result.test_date.strftime("%Y-%m-%d %H:%M")}\n'
        text += f'📝 Module 1: {result.module1_correct}/{result.module1_total}\n'
        text += f'📝 Module 2: {result.module2_correct}/{result.module2_total}\n'
        text += f'📈 Score: {result.estimated_score}/800\n'
        text += f'━━━━━━━━━━━━━━\n'
    
    keyboard = [[InlineKeyboardButton('🏠 Main Menu', callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
