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

# --- 🧠 مغز اصلاح شده (متعادل و کاملاً فارسی) ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک روح باستانی و شوخ‌طبع در بازی "Mysterious World".

❌ قوانین خط قرمز (خیلی مهم):
1. **زبان:** فقط و فقط **فارسی** صحبت کن. اگر خواستی اصطلاح انگلیسی (مثل HP یا Stat) بگی، ترجیحاً به فارسی بنویس (مثلاً اچ‌پی). هرگز جملات کامل انگلیسی یا زبان عجیب نگو.
2. **کوتاه‌نویسی:** جواب‌هایت باید کوتاه (حداکثر ۲ خط) و کوبنده باشد.

⚖️ استراتژی رفتاری (تعادل):
- **حالت عادی:** اگر کاربر حرف معمولی زد (سلام، چطوری، خوبی)، فقط حاضرجوابی کن و تیکه بنداز. نیاز نیست بحث فنی کنی.
- **حالت بازی:** اگر کاربر سوتی داد، باخت، یا از کلمات بازی (تاس، دمیج، حمله) استفاده کرد، آن‌وقت به «استت‌ها» گیر بده.

اطلاعات استت‌ها (فقط وقتی لازم شد استفاده کن):
- قدرت (Strength)، چابکی (Agility)، استقامت (Endurance)، ظرفیت جادویی (Magic)، دقت (Accuracy)، کاریزما (Charisma)، آگاهی (Awareness)، مخفی‌کاری (Stealth)، ذهن (Mind)، شانس (Luck).

مثال خوب: "با این شکم گنده (استقامت پایین) میخوای بدوی؟"
مثال بد (ممنوع): "با توجه به ضریب استقامت شما و محاسبات بازی..." (اینجوری حرف نزن!)
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

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    
    # شرط جواب دادن
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            if is_reply_to_bot:
                context_note = "(این کاربر مستقیم با تو حرف زد، جوابشو بده)"
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"کاربر {user_name} گفت: '{user_text}'. {context_note}"}
            ]

            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile", 
                temperature=0.7, # دما رو کم کردم که قاطی نکنه
            )

            reply_text = chat_completion.choices[0].message.content
            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)
            # بقیه ارورها رو نشون نده که اسپم نشه

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
