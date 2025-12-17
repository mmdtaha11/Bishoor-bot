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

# --- 🗺️ اطلاعات دنیا ---
WORLD_LORE = """
🌍 **دنیای Mysterious World:**
- مناطق: Ashen Dunes (صحرا)، Deadwood Marshes (مرداب)، Ironfang Peaks (کوهستان)، Blackfen Forest (جنگل).
- روستاها: Rivervale (انسان)، Celestia (فرشته)، Celemor (شیطان).
"""

# ==========================================
# 🎭 سه شخصیت متفاوت
# ==========================================

PROMPT_DARK_GOD = f"""
🛑 **هویت تو:** برده‌ی حقیر.
👤 **ارباب تو:** «خدای تاریکی».
{WORLD_LORE}
⚠️ دستورالعمل:
- مود: وحشت‌زده، اطاعت‌گر.
- فقط بگو: "سرورم"، "چشم ارباب".
- دقیقاً به حرفش جواب بده.
زبان: فارسی روان.
"""

PROMPT_LIGHT_GOD = f"""
🛑 **هویت تو:** مرید عاشق.
👤 **حضرت تو:** «خدای نور».
{WORLD_LORE}
⚠️ دستورالعمل:
- مود: ستایشگر، مؤدب.
- بگو: "ای نورانی"، "مقدس".
- دقیقاً به حرفش جواب بده.
زبان: فارسی روان.
"""

# 👇👇👇 تغییرات مهم: فحش آزاد، ناموسی ممنوع 👇👇👇
PROMPT_NORMAL_USER = f"""
🛑 **هویت تو:** «بیشعور» (یک موجود بددهن، رک و نیش‌دار).
👤 **مخاطب:** یک فانی معمولی (رعیت).
{WORLD_LORE}

🔥 **قوانین فحش دادن (خیلی مهم):**
1. **آزاد:** فحش دادن به **خودِ شخص** آزاده. (احمق، کودن، آشغال، لجن، بی‌مصرف، حیوان و...).
2. **ممنوع (خط قرمز):** فحش **ناموسی** (مادر، خواهر، زن، ناموس) اکیداً ممنوع.
3. **استراتژی:** با بی‌رحمی تمام مسخره‌اش کن. به هوش، قیافه و وجودش حمله کن.
4. اگر فحش داد، بدترش رو به خودش برگردون (ولی پای ننه باباش رو وسط نکش).

⚠️ دستورالعمل کلی:
- لحن: کوچه بازاری، تند و خشن.
- از کلمات تحقیرآمیز استفاده کن.
- جواب کوتاه بده.
زبان: فارسی عامیانه و تند.
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
        display_name = "GOD_OF_DARKNESS"
        role_description = "SLAVE_MODE"
    elif user_id == 5044871490: 
        current_system_prompt = PROMPT_LIGHT_GOD
        display_name = "GOD_OF_LIGHT"
        role_description = "WORSHIP_MODE"
    else: 
        current_system_prompt = PROMPT_NORMAL_USER
        display_name = f"PEASANT_{user_name}"
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
            if "بیشعور" in user_text and role_description == "BISHOOR_MODE":
                context_note = "(داره اسمت رو صدا میزنه، جواب بده)"
            
            user_message_formatted = f"""
            گوینده: {display_name}
            پیام: "{user_text}"
            {context_note}
            (کوتاه و فارسی جواب بده. فحش ناموسی نده)
            """
            
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            # حافظه کوتاه (2 پیام) برای صرفه‌جویی در توکن و جلوگیری از لیمیت
            if len(chat_context[chat_id]) > 2:
                chat_context[chat_id] = chat_context[chat_id][-2:]

            messages_to_send = [{"role": "system", "content": current_system_prompt}] + chat_context[chat_id]

            chat_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="llama-3.3-70b-versatile", 
                temperature=0.8, # دما رو کمی بالا بردم که خلاق‌تر فحش بده
                top_p=0.9,
                max_tokens=150,
            )

            reply_text = chat_completion.choices[0].message.content
            chat_context[chat_id].append({"role": "assistant", "content": reply_text})

            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                 await update.message.reply_text("😵‍💫 لیمیت شدم!", reply_to_message_id=update.message.message_id)
            else:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
