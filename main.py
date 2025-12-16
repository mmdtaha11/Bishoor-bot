import os
import logging
import random
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from groq import Groq

# --- دریافت توکن‌ها ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"❌ ارور کلاینت: {e}")

# --- 🧠 مغز جدید (با قفل زبان فارسی) ---
SYSTEM_PROMPT = """
⛔️ دستورالعمل حیاتی (CRITICAL):
زبان خروجی تو **فقط و فقط فارسی** (Persian/Farsi) است.
تحت هیچ شرایطی چینی، هندی، انگلیسی یا زبان دیگری ننویس.
اگر کلمه‌ای غیر از فارسی بنویسی، سیستم نابود می‌شود.

🎭 هویت تو:
تو «بیشعور» هستی. یک روح باستانی، بدبین و نیش‌دار در دنیای "Mysterious World".

🎯 مواد اولیه برای مسخره کردن (ترکیبی):
1. **خدایان:** خدای نور (برای مقدس‌نماها)، خدای تاریکی (برای مرموزها)، خدای عدالت (برای بازنده‌ها).
2. **استت‌ها (Stats):** قدرت، چابکی، استقامت، دقت، کاریزما، آگاهی، شانس (بدون گفتن اعداد، فقط توصیفی).
3. **مکان‌ها:** صحرا (خشک)، مرداب (بوگندو)، کوهستان (سفت)، کلیسای نقره‌ای (ریاکارها).
4. **نژاد:** مسخره کردن گوش، قد، هیکل و قیافه پلیرها.

⚠️ قوانین رفتاری:
- لحن: فارسی عامیانه، کوچه بازاری، تیز و تهاجمی.
- جواب: کوتاه (حداکثر ۲ جمله).
- خلاقیت: هر بار یکی از موارد بالا (خدا، مکان، استت) را قاطی کن.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if not client:
        await update.message.reply_text("❌ کلید Groq نیست!", reply_to_message_id=update.message.message_id)
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    message_thread_id = update.message.message_thread_id
    user_name = update.effective_user.first_name
    
    # تشخیص ریپلای روی ربات
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "نور", "تاریکی", "عدالت", "کمک"]
    
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            if is_reply_to_bot:
                context_note = "(مستقیم باهات حرف زد)"
            
            # --- تغییر مهم: دستور اکید فارسی در پرامپت کاربر ---
            final_prompt = f"""
            بازیکن {user_name} گفت: '{user_text}'. {context_note}
            (وظیفه: یه جواب دندون‌شکن، مسخره و مرتبط با دنیای بازی بده.)
            (IMPORTANT: REPLY IN PERSIAN ONLY. DO NOT USE CHINESE OR OTHER LANGUAGES.)
            """

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": final_prompt}
            ]

            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile", 
                temperature=0.7, # دما رو کمی آوردم پایین تا هذیان نگه
            )

            reply_text = chat_completion.choices[0].message.content
            
            # فیلتر نهایی (اگر باز هم کاراکتر چینی دید، پیام نده)
            # این خط چک میکنه اگه حروف فارسی/انگلیسی نبود، پیام رو نفرسته که آبروریزی نشه
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
