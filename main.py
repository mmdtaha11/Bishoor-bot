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
# 🎭 سه شخصیت متفاوت (بهینه شده برای Gemma 2)
# ==========================================

# 1. خدای تاریکی
PROMPT_DARK_GOD = f"""
نقش تو: یک «برده‌ی حقیر و لرزان».
ارباب تو: «خدای تاریکی» (کاربر).
{WORLD_LORE}
دستورالعمل:
- مود: وحشت‌زده، التماس‌کننده.
- هرگز شوخی نکن.
- فقط بگو: "سرورم"، "چشم ارباب".
- دقیقاً به حرفش جواب بده.
زبان: فارسی روان.
"""

# 2. خدای نور
PROMPT_LIGHT_GOD = f"""
نقش تو: یک «مرید عاشق و ستایشگر».
حضرت تو: «خدای نور» (کاربر).
{WORLD_LORE}
دستورالعمل:
- مود: محترمانه، ادبی و مؤدب.
- هرگز شوخی نکن.
- بگو: "ای نورانی"، "مقدس".
- دقیقاً به حرفش جواب بده.
زبان: فارسی روان.
"""

# 3. کاربر معمولی
PROMPT_NORMAL_USER = f"""
نقش تو: «بیشعور» (یک روح باستانی نیش‌دار).
مخاطب تو: یک «فانی معمولی» (خدا نیست!).
{WORLD_LORE}

🚫 **قانون مهم:**
این کاربر خدا نیست! مبادا به او احترام بگذاری.
باید با بی‌رحمی و طنز تلخ مسخره‌اش کنی.

دستورالعمل:
- شوخ و نیش‌دار باش.
- اگر لازم شد از اسم مناطق استفاده کن.
- جواب کوتاه بده.
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
    if user_id == 5107444649: # خدای تاریکی
        current_system_prompt = PROMPT_DARK_GOD
        display_name = "GOD_OF_DARKNESS (ارباب)"
        role_description = "SLAVE_MODE"
    elif user_id == 5044871490: # خدای نور
        current_system_prompt = PROMPT_LIGHT_GOD
        display_name = "GOD_OF_LIGHT (حضرت نور)"
        role_description = "WORSHIP_MODE"
    else: # کاربر معمولی
        current_system_prompt = PROMPT_NORMAL_USER
        display_name = f"PEASANT_{user_name} (رعیت)"
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
            
            # فرمت پیام برای Gemma
            user_message_formatted = f"""
            گوینده: {display_name}
            پیام: "{user_text}"
            {context_note}
            (کوتاه و فارسی جواب بده)
            """
            
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            messages_to_send = [{"role": "system", "content": current_system_prompt}] + chat_context[chat_id]

            # 👇 تغییر به مدل Gemma 2 (گوگل) روی Groq 👇
            chat_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="gemma2-9b-it",  # مدل گوگل: فارسی عالی + مصرف کم
                temperature=0.7,
                top_p=0.9,
                max_tokens=150,
            )

            reply_text = chat_completion.choices[0].message.content
            chat_context[chat_id].append({"role": "assistant", "content": reply_text})

            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                 await update.message.reply_text("😵‍💫 لیمیت پر شد! (چند دقیقه دیگه میام)", reply_to_message_id=update.message.message_id)
            else:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
