"""
Telegram Bot for FB OTP Automation (Local Execution)
Executes `fb_otp_browser.py` directly on the Heroku Dyno.
"""

import os
import asyncio
import logging
import subprocess
import shlex
import signal
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7205135297:AAEKFDTNZBj0c1I23Ri_a_PjCuWn_KUiYyY')
ALLOWED_CHAT_ID = int(os.environ.get('TELEGRAM_CHAT_ID', '664193835'))

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state to track current process for cancellation
CURRENT_PROCESS = None
IS_STOPPED = False

def get_main_keyboard():
    """Return main menu keyboard"""
    keyboard = [
        [KeyboardButton("🛑 إيقاف الكل")],
        [KeyboardButton("❓ المساعدة")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def post_init(application: Application):
    """Set up bot commands menu"""
    await application.bot.set_my_commands([
        BotCommand("start", "🏠 القائمة الرئيسية"),
        BotCommand("stop", "🛑 إيقاف العمليات"),
        BotCommand("help", "❓ المساعدة")
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("❌ غير مصرح لك باستخدام هذا البوت")
        return
    
    await update.message.reply_text(
        "🤖 **بوت FB OTP (الوضع المحلي)**\n\n"
        "الآن البوت يعمل مباشرة على السيرفر! 🚀\n"
        "لا حاجة لـ GitHub بعد الآن.\n\n"
        "📱 **للبدء:**\n"
        "• أرسل ملف `.txt` يحتوي على الأرقام\n"
        "• أو أرسل الأرقام مباشرة (رقم في كل سطر)\n\n"
        "سيقوم البوت بمعالجة الأرقام واحداً تلو الآخر وإرسال النتائج هنا.",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def stop_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop current execution"""
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
        
    global IS_STOPPED, CURRENT_PROCESS
    IS_STOPPED = True
    
    msg = await update.message.reply_text("🛑 جاري إيقاف العمليات...")
    
    if CURRENT_PROCESS:
        try:
            # Send SIGTERM
            CURRENT_PROCESS.terminate()
            # Wait a bit then kill if needed
            try:
                CURRENT_PROCESS.wait(timeout=5)
            except subprocess.TimeoutExpired:
                CURRENT_PROCESS.kill()
            
            await msg.edit_text("✅ تم إيقاف العملية الحالية والجدول.")
        except Exception as e:
            await msg.edit_text(f"⚠️ خطأ أثناء الإيقاف: {e}")
            logger.error(f"Error stopping process: {e}")
    else:
        await msg.edit_text("✅ تم تفعيل وضع الإيقاف (لا توجد عمليات جارية حالياً).")

async def run_otp_script(phone_number, context, chat_id, status_msg):
    """Run the local Python script for a single number"""
    global CURRENT_PROCESS
    
    cmd = f"python fb_otp_browser.py {phone_number}"
    
    try:
        # Update status
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"🔄 جاري معالجة: `{phone_number}`...\n⏳ انتظر قليلاً (قد يستغرق 1-2 دقيقة)"
        )
        
        # Start Process
        CURRENT_PROCESS = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for completion
        stdout, stderr = await asyncio.to_thread(CURRENT_PROCESS.communicate)
        
        return_code = CURRENT_PROCESS.returncode
        CURRENT_PROCESS = None
        
        if return_code == 0:
            # Success check usually happens via the script sending the photo.
            # We can log the output just in case
            logger.info(f"Script finished for {phone_number}. Output:\n{stdout}")
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"✅ تمت المعالجة: `{phone_number}`\n(راجع الصورة أعلاه إذا تم العثور عليها)"
            )
            return True
        else:
            logger.error(f"Script failed for {phone_number}. Err:\n{stderr}\nOutput:\n{stdout}")
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"❌ خطأ في السكريبت للرقم `{phone_number}`\nError log check required."
            )
            return False

            
    except Exception as e:
        logger.error(f"Exception running script: {e}")
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_msg.message_id,
            text=f"❌ حدث خطأ غير متوقع: {e}"
        )
        return False

async def process_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE, numbers):
    """Queue processor for numbers"""
    global IS_STOPPED
    IS_STOPPED = False
    
    total = len(numbers)
    chat_id = update.effective_chat.id
    
    main_msg = await update.message.reply_text(
        f"📋 **بدء القائمة**\n🔢 العدد: {total}\n🚀 الحالة: جاري التحضير...",
        parse_mode='Markdown'
    )
    
    for i, phone in enumerate(numbers):
        if IS_STOPPED:
            await context.bot.send_message(chat_id, "🛑 تم إيقاف القائمة بناءً على طلبك.")
            break
            
        progress_msg = await context.bot.send_message(
            chat_id, 
            f"⏳ ({i+1}/{total}) بدء: `{phone}`", 
            parse_mode='Markdown'
        )
        
        # Run execution
        success = await run_otp_script(phone, context, chat_id, progress_msg)
        
        # Update main status periodically
        if i % 5 == 0:
             await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=main_msg.message_id,
                text=f"📋 **حالة القائمة**\n🔢 المتبقي: {total - (i + 1)}\n✅ المكتمل: {i + 1}",
                parse_mode='Markdown'
            )
            
        # Small delay between runs to let systems breathe
        await asyncio.sleep(2)
        
    if not IS_STOPPED:
        await context.bot.send_message(chat_id, "🎉 **تم الانتهاء من القائمة بالكامل!**")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file upload"""
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    
    document = update.message.document
    if not document.file_name.endswith('.txt'):
        await update.message.reply_text("❌ يرجى إرسال ملف .txt فقط")
        return
    
    file = await context.bot.get_file(document.file_id)
    file_content = await file.download_as_bytearray()
    numbers_text = file_content.decode('utf-8')
    
    numbers = [line.strip() for line in numbers_text.split('\n') if line.strip() and not line.startswith('#')]
    
    if not numbers:
        await update.message.reply_text("❌ الملف فارغ")
        return
        
    await process_numbers(update, context, numbers)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct text input"""
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
        
    text = update.message.text
    if text.startswith('/') or text in ["🛑 إيقاف الكل", "❓ المساعدة"]:
        return
        
    numbers = [line.strip() for line in text.split('\n') if line.strip()]
    if not numbers:
        return
        
    await process_numbers(update, context, numbers)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_text(
        "❓ **المساعدة**\n"
        "فقط أرسل الأرقام أو ملف `.txt` وسيتم تشغيلها فوراً.\n"
        "للإيقاف اضغط على '🛑 إيقاف الكل'.",
        parse_mode='Markdown'
    )

def main():
    """Start the bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop_all))
    application.add_handler(CommandHandler("help", help_command))
    
    # Message Handlers
    application.add_handler(MessageHandler(filters.Regex("^🛑 إيقاف الكل$"), stop_all))
    application.add_handler(MessageHandler(filters.Regex("^❓ المساعدة$"), help_command))
    application.add_handler(MessageHandler(filters.Document.MimeType("text/plain"), handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start
    application.run_polling()

if __name__ == '__main__':
    main()
