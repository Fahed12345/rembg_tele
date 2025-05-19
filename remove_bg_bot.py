import logging
import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from io import BytesIO
from PIL import Image
from rembg import remove

# تكوين التسجيل مع حفظ السجلات في ملف
# تعديل مسار ملف السجل ليكون نسبيًا
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot_log.txt", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# استبدل هذا بالتوكن الخاص بك من BotFather
TOKEN = "8032466337:AAH65Ej-9Kwl7T7DIviIFV2Sxm_AUDKQAEI"

# مجلد لحفظ الصور المؤقتة
TEMP_FOLDER = "temp_images"
os.makedirs(TEMP_FOLDER, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة عند تنفيذ الأمر /start."""
    await update.message.reply_text(
        'مرحباً! أنا بوت إزالة خلفية الصور. فقط أرسل لي صورة وسأقوم بإزالة خلفيتها.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال رسالة عند تنفيذ الأمر /help."""
    await update.message.reply_text('أرسل لي صورة وسأقوم بإزالة خلفيتها وإعادتها إليك.')

async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إزالة خلفية الصورة المرسلة."""
    # التحقق من وجود صورة
    if not update.message.photo:
        await update.message.reply_text("الرجاء إرسال صورة.")
        return

    # إرسال رسالة انتظار
    wait_message = await update.message.reply_text("جاري معالجة الصورة، يرجى الانتظار...")
    
    try:
        # الحصول على أكبر نسخة من الصورة (أعلى دقة)
        photo = update.message.photo[-1]
        logger.info(f"Processing photo with file_id: {photo.file_id}")
        
        # تنزيل الصورة
        photo_file = await context.bot.get_file(photo.file_id)
        logger.info(f"Got file info: {photo_file.file_path}")
        photo_bytes = await photo_file.download_as_bytearray()
        logger.info(f"Downloaded photo, size: {len(photo_bytes)} bytes")
        
        # إزالة الخلفية
        logger.info("Opening image with PIL")
        input_image = Image.open(BytesIO(photo_bytes))
        logger.info(f"Image opened, size: {input_image.size}, mode: {input_image.mode}")
        
        logger.info("Removing background with rembg")
        output_image = remove(input_image)
        logger.info("Background removed successfully")
        
        # حفظ الصورة في ذاكرة مؤقتة
        output_buffer = BytesIO()
        logger.info("Saving processed image to buffer")
        output_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        logger.info(f"Image saved to buffer, size: {output_buffer.getbuffer().nbytes} bytes")
        
        # إرسال الصورة بدون خلفية
        logger.info("Sending processed image back to user")
        await update.message.reply_photo(
            photo=output_buffer,
            caption="تمت إزالة الخلفية بنجاح!"
        )
        logger.info("Processed image sent successfully")
        
        # حذف رسالة الانتظار
        await wait_message.delete()
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        # تسجيل تفاصيل الخطأ
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        await wait_message.edit_text("حدث خطأ أثناء معالجة الصورة. الرجاء المحاولة مرة أخرى.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """التعامل مع الرسائل النصية."""
    await update.message.reply_text(
        "أرسل لي صورة وسأقوم بإزالة خلفيتها. استخدم /help للحصول على المساعدة."
    )

# Add an error handler function
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the developer."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Log the stack trace
    import traceback
    traceback.print_exception(None, context.error, context.error.__traceback__)

def main() -> None:
    """بدء تشغيل البوت."""
    # تسجيل بدء تشغيل البوت
    logger.info("Starting bot...")
    
    # تعديل التوكن ليتطابق مع السجلات
    token = os.environ.get("BOT_TOKEN", "8032466337:AAH65Ej-9Kwl7T7DIviIFV2Sxm_AUDKQAEI")
    
    # إنشاء التطبيق مع إعدادات محسنة
    application = Application.builder().token(token).connect_timeout(
        60.0
    ).pool_timeout(60.0).read_timeout(60.0).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # إضافة معالج الصور
    application.add_handler(MessageHandler(filters.PHOTO, remove_background))
    
    # إضافة معالج النصوص
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # إضافة معالج الأخطاء
    application.add_error_handler(error_handler)

    # استخدام polling للتشغيل المستمر مع إعدادات محسنة
    logger.info("Bot is running...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,  # تجاهل التحديثات المعلقة عند بدء التشغيل
        poll_interval=1.0,  # فترة الاستطلاع بالثواني
        timeout=30  # مهلة الاتصال بالثواني
    )

if __name__ == '__main__':
    main()
