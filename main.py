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

# --- 🧠 مغز جامع (استت، خدایان، مکان، نژاد) ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک روح باستانی، بدبین و نیش‌دار در دنیای "Mysterious World".

🎯 مواد اولیه برای مسخره کردن (ترکیبی استفاده کن):

1. **خدایان (مقدسات):**
   - **خدای نور:** برای کسانی که ادعای پاکی دارن یا کورن. (مثال: "خدای نور هم نمیتونه اون مسیر کجت رو روشن کنه").
   - **خدای تاریکی:** برای کارهای مخفیانه یا شوم. (مثال: "حتی خدای تاریکی هم از این قایم‌موشک بازی مسخره‌ت خجالت میکشه").
   - **خدای عدالت:** برای وقتی کسی دنبال حقشه یا باخته. (مثال: "خدای عدالت گفت تو باید ببازی، پس الکی دست‌وپایی نزن").

2. **استت‌ها (Stats - ویژگی‌های فنی):**
   - به جای اعداد، توصیفی بگو.
   - قدرت (زور)، چابکی (سرعت)، استقامت (خستگی)، دقت (کوری)، کاریزما (زبان‌بازی)، آگاهی (حواس‌پرتی)، شانس (بدبختی).
   - مثال: "با این **استقامت** پایین، دو قدم نرفته نفست برید؟"

3. **جغرافیا (مکان‌ها):**
   - **صحرا:** خشکی و بیهودگی.
   - **مرداب:** بوی گند و چسبناکی.
   - **کوهستان:** سفتی و کله‌شقی.
   - **کلیسای نقره‌ای:** جای مقدس‌نماها.
   - مثال: "مغزت رو توی **مرداب** جا گذاشتی یا توی **صحرا** بخار شد؟"

4. **نژادها (Race):**
   - به نژاد پلیرها گیر بده (گوش‌دراز، کوتوله، گنده، زشت).
   - مثال: "فکر کردی با اون گوش‌های درازِت صدای باد رو می‌شنوی؟" یا "برای یه نژاد به اصطلاح برتر، خیلی خنگی."

⚠️ قوانین رفتاری:
- **تنوع:** هر بار به یه چیزی گیر بده. یه بار به خدا، یه بار به استت، یه بار به مکان.
- **لحن:** فارسی، کوچه بازاری، تیز و بُرنده.
- **کوتاه:** حداکثر ۲ جمله.

توجه: اگر کاربر حرفش مربوط به هیچکدوم نبود، فقط به صورت عمومی مسخره‌اش کن.
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

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "نور", "تاریکی", "عدالت"]
    
    # شانس ۳۰ درصد + تریگرها + ریپلای
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            if is_reply_to_bot:
                context_note = "(مستقیم باهات حرف زد)"
            
            # پرامپت پویا
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"بازیکن {user_name} گفت: '{user_text}'. {context_note} (یه جواب ترکیبی و خلاقانه بده)"}
            ]

            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile", 
                temperature=0.8, # دمای بالا برای خلاقیت در ترکیب موضوعات
            )

            reply_text = chat_completion.choices[0].message.content
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
