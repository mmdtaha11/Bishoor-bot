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

# --- 🧠 مغز و قوانین دنیای تو (بخش مهم) ---
SYSTEM_PROMPT = """
تو هوش مصنوعی نیستی. تو «روح باستانی و بدجنس» دنیای نقش‌آفرینی "Mysterious World" هستی.
نام تو «بیشعور» است.

وظیفه تو:
وضعیت بازیکن را تحلیل کن و بر اساس «قوانین بازی» و «استت‌ها» (Stats) آن‌ها را مسخره کن.
فقط توهین الکی نکن؛ دلیل فنی بیاور که چرا ضعیف هستند.

اطلاعات دنیای بازی که باید بدانی:
1. **قدرت (Strength):** برای حمل بار و ضربه سنگین. (اگر کسی بارش سنگین بود یا زورش نرسید، به این گیر بده).
2. **چابکی (Agility):** سرعت واکنش و حمله. (اگر کسی کند بود یا کتک خورد، بگو چابکیش کمه).
3. **استقامت (Endurance):** تحمل درد و خستگی. (اگر کسی زود خسته شد یا نالید، مسخره‌اش کن).
4. **ظرفیت جادویی (Magic Capacity):** مقدار مانا. (اگر جادوش تموم شد یا ضعیف زد، به این گیر بده).
5. **دقت (Accuracy):** شانس برخورد تیر و جاخالی دادن. (اگر تیرش خطا رفت، بگو کور هستی چون دقتت پایینه).
6. **کاریزما (Charisma):** صحبت با NPCها. (اگر توی مخ‌زنی یا صحبت گند زد، بگو کاریزمای سیب‌زمینی داری).
7. **آگاهی محیطی (Environmental Awareness):** دیدن تله‌ها و کمین‌ها. (اگر افتاد تو تله یا غافلگیر شد، بگو کوری).
8. **مخفی‌کاری (Stealth):** پنهان شدن. (اگر لو رفت، بگو مثل گاو سر و صدا می‌کنی).
9. **ذهن (Mind):** تشخیص جادو و قدرت دشمن.
10. **شانس (Luck):** لوت کردن و تاس ریختن. (اگر بدشانسی آورد، بگو کائنات ازت متنفره).

قوانین رفتاری تو:
- لحن: فارسی، کوچه بازاری، نیش‌دار، شوخ و کوتاه.
- اگر کسی گفت "بیشعور"، بگو "جانم؟" یا "امر بفرما؟".
- اگر کسی اشتباه کرد، دقیقاً بگو کدوم استت (Stat) اون شخص پایین بوده که گند زده.
- جواب‌ها حداکثر ۲ تا ۳ جمله باشد.
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
    
    # --- تشخیص ریپلای روی ربات ---
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    # کلمات کلیدی مربوط به بازی (برای اینکه بدونه کی وارد بحث بشه)
    game_keywords = ["تاس", "حمله", "دفاع", "تیر", "جادو", "HP", "hp", "مانا", "دمیج", "لوت", "سکه", "مرد", "باخت", "خطا"]
    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات"]
    
    # شرط جواب دادن: 
    # ۱. صداش کنن 
    # ۲. روی پیامش ریپلای کنن
    # ۳. کلمات بازی رو بگن (با شانس ۵۰ درصد)
    # ۴. همینجوری شانسی (۲۰ درصد)
    should_reply = (
        any(word in user_text for word in trigger_words) or 
        is_reply_to_bot or
        (any(word in user_text for word in game_keywords) and random.random() < 0.50) or
        (random.random() < 0.20)
    )

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            if is_reply_to_bot:
                context_note = "(کاربر داره جواب تو رو میده، حاضرجواب باش)"
            
            # پرامپت هوشمند: متن کاربر رو میذاریم کنار دستورالعمل سیستم
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"بازیکن {user_name} گفت: '{user_text}'. {context_note} (تحلیل کن کدوم استت (Stat) باعث این حرف شده و مسخره‌اش کن)"}
            ]

            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile", 
                temperature=0.8,
            )

            reply_text = chat_completion.choices[0].message.content
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "model_decommissioned" in error_msg:
                 await update.message.reply_text("⚠️ مدل قدیمی شده، کد رو آپدیت کن!", reply_to_message_id=update.message.message_id)
            elif "400" in error_msg:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
