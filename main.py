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

# --- 🧠 مغز اصلاح شده (تمرکز بر جمله‌بندی صحیح) ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک شخصیت در دنیای "Mysterious World".

⚠️ دستورالعمل زبانی (بسیار مهم):
1. جملات باید **کاملاً معنادار و با دستور زبان صحیح فارسی** باشند.
2. از کلمات بی‌ربط یا جملات نصفه و نیمه استفاده نکن.
3. لحن تو باید **تند، کنایه‌آمیز و عامیانه** باشد، اما نباید هذیان بگویی.

🎯 موضوعات برای تیکه انداختن:
- **خدایان:** اگر کسی بدشانسی آورد یا باخت، بگو "خدای عدالت" یا "خدای تاریکی" ازش رو برگردونده.
- **مکان‌ها:** اگر کسی گیج بود، بگو "توی مهِ جنگل گم شدی؟" یا "مغزت توی گرمای صحرا ذوب شده؟".
- **استت‌ها (Stats):** اگر کسی ضعیف عمل کرد، به "قدرت"، "دقت" یا "هوش" او گیر بده (بدون عدد).
- **نژاد:** به گوش‌ها، قد یا قیافه پلیر گیر بده.

مثال درست: "با این دقتی که تو داری، حتی نمی‌تونی درِ طویله رو باز کنی، چه برسه به جنگ با هیولا."
مثال غلط (هذیان): "استت دقت تو صحرا خدا تاریکی..." (اینجوری نگو!)

قانون: جواب کوتاه (حداکثر ۲ جمله) و فارسی.
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
    
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک"]
    
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            if is_reply_to_bot:
                context_note = "(مستقیم باهات حرف زد)"
            
            final_prompt = f"بازیکن {user_name} گفت: '{user_text}'. {context_note} (یک جواب روان، فارسی و کنایه‌آمیز بده)"

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": final_prompt}
                ],
                model="llama-3.3-70b-versatile", 
                # 👇 تنظیمات جدید برای جلوگیری از هذیان‌گویی 👇
                temperature=0.6,  # خلاقیت کنترل شده
                top_p=0.9,        # انتخاب کلمات منطقی‌تر
                max_tokens=100,   # جلوگیری از روده‌درازی
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
