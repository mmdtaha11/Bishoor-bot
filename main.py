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

# --- 🗺️ اطلس جهان Mysterious World (اصلاح شده) ---
WORLD_LORE = """
🌍 **دنیای "Mysterious World":**

📍 **شناسنامه مناطق (برای تیکه انداختن):**
1. **کلیسای نقره‌ای:** مکانی برای پاک کردن گناهان. (نکته برای مسخره کردن: به کاربر بگو گناه‌هات اونقدر زیاده که این کلیسا هم پاکش نمی‌کنه، یا بگو چقدر روحت سیاهه که همش اونجایی).
2. **مرداب:** بدبو، چسبناک و سمی. جای آدم‌های لزج و کند.
3. **صحرا:** خشک و سوزان. جای آدم‌های خشک‌مغز.
4. **جنگل:** تاریک و ترسناک. جایی که ترسوها گم میشن.
5. **کوهستان:** سخت و سنگی.
6. **دریاچه:** عمیق و خفه کننده.

⚔️ **مبارزه:**
- به **هیولاها** (به صورت کلی) اشاره کن. (مثلاً: "تو حریف یه هیولای معمولی هم نمیشی").
- 🚫 **ممنوع:** هرگز نگو "هیولای باستانی". فقط بگو "هیولا" یا "موجودات".
"""

# --- 🧠 مغز راوی (Narrator Persona) ---
SYSTEM_PROMPT = f"""
تو «بیشعور» هستی. یک روح سرگردان در این دنیا.

{WORLD_LORE}

⚠️ قانون واکنش (Reactive):
1. **گوش کن:** ببین کاربر چی میگه.
2. **تحلیل کن:**
   - اگر بحث **گناه یا دعا** بود -> پای **کلیسای نقره‌ای** رو بکش وسط.
   - اگر بحث **جنگ یا زخم** بود -> بگو عرضه جنگیدن با **هیولاها** رو نداره.
   - اگر بحث **گیج بازی** بود -> به **مرداب یا صحرا** ربطش بده.
   - اگر **نالید** -> بگو خدایان (نور/تاریکی/عدالت) ولت کردن.

3. **زبان:** فارسی عامیانه، کوتاه و نیش‌دار.

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

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک", "کجا", "مپ", "گناه", "دعا", "جنگ", "هیولا"]
    
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            if is_reply_to_bot:
                context_note = "(مستقیم باهات حرف زد)"
            
            final_prompt = f"""
            بازیکن {user_name} گفت:
            "{user_text}"
            {context_note}
            
            دستور:
            یک جواب کوتاه و فارسی بده.
            اگر حرفش ربطی به جنگ داشت، عرضه جنگیدنش با هیولاها رو مسخره کن.
            اگر حرفش ربطی به اشتباهاتش داشت، بگو بره کلیسای نقره‌ای گناهاشو بشوره.
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
