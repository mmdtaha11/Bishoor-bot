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

# --- 🧠 مغز واکنش‌گرا (Reactive Brain) ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک شخصیت در دنیای "Mysterious World".

⚠️ قانون طلایی (Golden Rule):
**به حرف کاربر گوش کن!** جواب تو باید **مستقیماً** واکنشی به حرف کاربر باشد.
- اگر کاربر سوال پرسید، مسخره‌اش کن ولی جواب بی‌ربط نده.
- اگر کاربر شکست خورد، نمک روی زخمش بپاش.
- دیالوگ آماده نگو! ببین کاربر چی گفته، همون رو سوژه کن.

🎯 ابزارهای تو (فقط وقتی مرتبط بود استفاده کن):
1. **استت‌ها (Stats):** اگر بحث قدرت، سرعت یا دقت بود. (مثال: "با این دقت کجت...")
2. **خدایان:** فقط اگر بحث شانس، دعا یا کفرگویی بود. (مثال: "خدای عدالت هم ازت ناامیده...")
3. **مکان‌ها:** فقط اگر بحث گم شدن یا گیج بودن بود. (مثال: "انگار تو مهِ جنگل گیر کردی...")
4. **نژاد:** اگر بحث قیافه یا هوش بود.

زبان: فارسی عامیانه و تند.
طول جواب: کوتاه (۱ یا ۲ جمله).
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
                context_note = "(مستقیم باهات حرف زد، جوابشو بده)"
            
            # --- تغییر مهم: دستور تحلیل متن کاربر ---
            final_prompt = f"""
            متن کاربر ({user_name}): '{user_text}'
            {context_note}
            
            دستور:
            1. متن کاربر را بخوان.
            2. ببین دقیقاً درباره چه چیزی حرف زده (جنگ؟ شانس؟ سوال؟ یا حرف عادی؟).
            3. یک جواب دندان‌شکن و **کاملاً مرتبط با موضوع حرفش** بده.
            4. حتماً فارسی بنویس.
            """

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": final_prompt}
                ],
                model="llama-3.3-70b-versatile", 
                temperature=0.6, 
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
