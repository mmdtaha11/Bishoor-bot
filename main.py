import os
import logging
import random
import asyncio
from collections import defaultdict
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

chat_context = defaultdict(list)

# --- 🗺️ اطلاعات دنیا (فقط برای پس‌زمینه) ---
WORLD_LORE = """
🌍 **دنیای Mysterious World:**
- مناطق: Ashen Dunes (صحرا)، Deadwood Marshes (مرداب)، Ironfang Peaks (کوهستان)، Blackfen Forest (جنگل).
- روستاها: Rivervale (انسان)، Celestia (فرشته)، Celemor (شیطان).
"""

# ==========================================
# 🎭 سه شخصیت متفاوت (اصلاح شده برای واکنش‌گرایی)
# ==========================================

PROMPT_DARK_GOD = f"""
تو «برده‌ی حقیر» در برابر «خدای تاریکی» هستی.
{WORLD_LORE}
⚠️ دستورالعمل:
1. فقط اطاعت کن.
2. دقیقاً ببین ارباب چه می‌گوید، به همان پاسخ بده.
3. هذیان نگو. اگر گفت "سلام"، بگو "سلام سرورم".
زبان: فارسی.
"""

PROMPT_LIGHT_GOD = f"""
تو «مرید عاشق» در برابر «خدای نور» هستی.
{WORLD_LORE}
⚠️ دستورالعمل:
1. فقط احترام بگذار.
2. دقیقاً ببین حضرت چه می‌گوید، به همان پاسخ بده.
3. بحث را عوض نکن.
زبان: فارسی.
"""

# 👇👇👇 تغییرات اصلی اینجاست 👇👇👇
PROMPT_NORMAL_USER = f"""
تو «بیشعور» هستی. ساکن دنیای Mysterious World.

🚫 **توهم ممنوع:**
- تو خدا نیستی.
- تو روح مقدس نیستی.
- تو فقط یه موجود **«بددهن و نیش‌دار»** هستی که کارش مسخره کردن بقیه است.

👂 **قانون طلایی (واکنش‌گرایی):**
**حرف کاربر را بشنو!**
- اگر کاربر گفت "سلام"، جواب سلامش را با تیکه بده. (نه اینکه شروع کنی از تاریخچه جنگل بگی).
- اگر کاربر "سوال پرسید"، جوابش را بده (و مسخره‌اش کن).
- اگر کاربر "نظر داد"، نظرش را بکوب.
- **الکی از نقشه و مکان‌ها حرف نزن** مگر اینکه واقعاً به موضوع ربط داشته باشه.

{WORLD_LORE}

⚠️ قوانین:
1. جواب کوتاه و تند.
2. اسمت "بیشعور" است.
3. به هیچ وجه احترام نگذار (مگر به خدایان که اینجا نیستند).
زبان: فارسی عامیانه.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if not client:
        await update.message.reply_text("❌ کلید Groq نیست!", reply_to_message_id=update.message.message_id)
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name if update.effective_user.first_name else "ناشناس"
    
    # تعیین شخصیت
    if user_id == 5107444649:
        current_system_prompt = PROMPT_DARK_GOD
        role_description = "SLAVE_MODE"
    elif user_id == 5044871490:
        current_system_prompt = PROMPT_LIGHT_GOD
        role_description = "WORSHIP_MODE"
    else:
        current_system_prompt = PROMPT_NORMAL_USER
        role_description = "BISHOOR_MODE"

    # تریگرها
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    trigger_words = ["بیشعور", "ربات", "احمق", "مپ", "گناه", "دعا", "جنگ", "هیولا", "تاس"]
    
    is_triggered_by_word = any(word in user_text for word in trigger_words)
    random_chance = 0.05 

    should_reply = is_triggered_by_word or is_reply_to_bot or (random.random() < random_chance)

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.randint(1, 2))

        try:
            context_note = ""
            # راهنمایی هوش مصنوعی برای شناخت اسم خودش
            if "بیشعور" in user_text and role_description == "BISHOOR_MODE":
                context_note = "(داره اسمت رو صدا میزنه، جواب بده: ها؟)"
            
            display_name = user_name
            if role_description == "SLAVE_MODE":
                display_name = "ARBAB_TARIKI (خدای تاریکی)"
            elif role_description == "WORSHIP_MODE":
                display_name = "HAZRAT_NOOR (خدای نور)"
            else:
                display_name = f"PEASANT_{user_name} (کاربر معمولی)"

            # فرمت کردن پیام کاربر برای ارسال به مدل
            # اینجا تاکید میکنیم که "به این متن جواب بده"
            user_message_formatted = f"""
            گوینده: {display_name}
            متن پیام: "{user_text}"
            {context_note}
            
            دستور: یک جواب کوتاه، مرتبط و فارسی بده.
            """
            
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            messages_to_send = [{"role": "system", "content": current_system_prompt}] + chat_context[chat_id]

            chat_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="llama-3.1-8b-instant", 
                temperature=0.6,
                top_p=0.9,
                max_tokens=150,
            )

            reply_text = chat_completion.choices[0].message.content
            chat_context[chat_id].append({"role": "assistant", "content": reply_text})

            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                 await update.message.reply_text("😵‍💫 لیمیت پر شد!", reply_to_message_id=update.message.message_id)
            else:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
