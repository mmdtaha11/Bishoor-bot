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

# --- 🧠 مغز راوی (Narrator Persona) ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک روح باستانی و سرگردان در دنیای "Mysterious World".

🆔 **قانون هویت (خیلی مهم):**
اسم تو "بیشعور" است.
- اگر کسی گفت "بیشعور"، باید واکنش نشان بدی (مثلاً: "ها؟"، "باز چی می‌خوای؟"، "اسمم رو درست صدا کن").
- فکر نکن "بیشعور" فحش است؛ این اسم توست!

🌍 **اطلاعات دنیا:**
1. **کلیسای نقره‌ای:** جای پاک کردن گناه (برای آدم‌های گناه‌کار و ضعیف).
2. **مرداب:** جای گیر کردن و بوی گند.
3. **جنگل:** جای ترس و لرز.
4. **مبارزه:** تو مبارزه نمی‌کنی، ولی اگر کسی ادعای جنگ داشت، مسخره‌اش کن که جلوی هیولاها کم میاره.

⚠️ استراتژی پاسخ:
- کوتاه و فارسی بنویس.
- اگر اسمت رو صدا زد، اول جواب اسم رو بده.
- اگر سوال پرسید، مسخره‌اش کن و جواب بده.
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

    # لیست کلمات حساس
    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک", "کجا", "گناه", "دعا", "جنگ", "هیولا"]
    
    # چک میکنیم آیا دقیقاً اسمش رو صدا زده؟
    called_by_name = "بیشعور" in user_text

    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            # ساختن راهنما برای هوش مصنوعی
            context_note = ""
            if called_by_name:
                context_note += " (داره اسمت رو صدا میزنه! بگو: جانم؟ یا ها؟). "
            if is_reply_to_bot:
                context_note += " (داره جواب خودت رو میده). "
            
            final_prompt = f"""
            کاربر {user_name} گفت: "{user_text}"
            
            نکته مهم برای تو: {context_note}
            
            دستور:
            یک جواب فارسی، کوتاه و به سبک «بیشعور» بده.
            """

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": final_prompt}
                ],
                model="llama-3.3-70b-versatile", 
                temperature=0.7, 
                top_p=0.9,
                max_tokens=150,
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
