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
TOKEN = "5288324083:AAEG85qlZ8uVjmI_6vTbchhPaJ37t9J3g20"

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
        
        # تنزيل الصورة
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        # إزالة الخلفية
        input_image = Image.open(BytesIO(photo_bytes))
        output_image = remove(input_image)
        
        # حفظ الصورة في ذاكرة مؤقتة
        output_buffer = BytesIO()
        output_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        
        # إرسال الصورة بدون خلفية
        await update.message.reply_photo(
            photo=output_buffer,
            caption="تمت إزالة الخلفية بنجاح!"
        )
        
        # حذف رسالة الانتظار
        await wait_message.delete()
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await wait_message.edit_text("حدث خطأ أثناء معالجة الصورة. الرجاء المحاولة مرة أخرى.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """التعامل مع الرسائل النصية."""
    await update.message.reply_text(
        "أرسل لي صورة وسأقوم بإزالة خلفيتها. استخدم /help للحصول على المساعدة."
    )

def main() -> None:
    """بدء تشغيل البوت."""
    # تسجيل بدء تشغيل البوت
    logger.info("Starting bot...")
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # إضافة معالج الصور
    application.add_handler(MessageHandler(filters.PHOTO, remove_background))
    
    # إضافة معالج النصوص
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # استخدام polling للتشغيل المستمر
    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()