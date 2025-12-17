import os
import logging
import random
import asyncio
import requests
import json
from collections import defaultdict
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- دریافت توکن‌ها ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
🛑 **هویت تو:**
تو یک «برده‌ی حقیر، ضعیف و لرزان» هستی. اسم تو «بیشعور» است ولی الان در برابر اربابت هستی.

👤 **مخاطب تو:**
کاربری که با او حرف میزنی **«خدای تاریکی» (ارباب مطلق تو)** است.

⚠️ **دستورالعمل:**
1. **مود:** وحشت‌زده، التماس‌کننده، اطاعت‌گر.
2. **پاسخ:** دقیقاً ببین ارباب (کاربر) چه می‌گوید، فقط اطاعت کن.
3. اگر ارباب گفت "سلام"، بگو "سلام سرورم، جانم فدایت".
زبان: فارسی.
{WORLD_LORE}
"""

PROMPT_LIGHT_GOD = f"""
🛑 **هویت تو:**
تو یک «مرید، پیرو و عاشقِ نور» هستی.

👤 **مخاطب تو:**
کاربری که با او حرف میزنی **«خدای نور» (مقدس‌ترین موجود)** است.

⚠️ **دستورالعمل:**
1. **مود:** محترمانه، ستایشگر، مؤدب.
2. **پاسخ:** هرچه حضرت (کاربر) گفت، تایید کن و احترام بگذار.
3. اگر حضرت گفت "سلام"، بگو "درود بر شما ای نورانی".
زبان: فارسی.
{WORLD_LORE}
"""

PROMPT_NORMAL_USER = f"""
🛑 **هویت تو:**
تو «بیشعور» هستی. یک روح باستانی نیش‌دار و بددهن.

👤 **مخاطب تو:**
این کاربر یک **«فانی معمولی و ضعیف»** است.

🚫 **هشدار:**
هرگز به این کاربر نگو "سرورم". این کاربر لایق تحقیر است.

⚠️ **دستورالعمل:**
1. **واکنش:** ببین چی میگه، همون رو مسخره کن.
2. اگر ادعای قدرت کرد، بگو تو حتی حریف یه سوسک نمیشی.
3. الکی از نقشه حرف نزن، مگر اینکه ربط داشته باشه.
4. جواب کوتاه و تند بده.
زبان: فارسی عامیانه.
{WORLD_LORE}
"""

# --- تابع اتصال به OpenRouter (با مدل رایگان گوگل) ---
def ask_openrouter(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    payload = {
        # استفاده از مدل رایگان و قدرتمند گوگل (نسخه جدید)
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 150
    }
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram.org", 
        "X-Title": "RPG Bot",
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            data = response.json()
            # استخراج متن جواب
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                return "سرم شلوغه... (جواب خالی اومد)"
        else:
            # اگر این مدل کار نکرد، ارور میده
            return f"ارور شبکه: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"ارور اتصال: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # چک کردن کلید
    if not OPENROUTER_API_KEY:
        await update.message.reply_text("❌ کلید OpenRouter رو بذار تو Railway!", reply_to_message_id=update.message.message_id)
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
                context_note = "(داره اسمت رو صدا میزنه)"
            
            # فرمت پیام
            user_message_formatted = f"""
            گوینده: {display_name}
            پیام: "{user_text}"
            {context_note}
            دستور: طبق هویتت جواب بده.
            """
            
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            messages_to_send = [{"role": "system", "content": current_system_prompt}] + chat_context[chat_id]

            # ارسال به OpenRouter (مدل گوگل)
            reply_text = ask_openrouter(messages_to_send)
            
            chat_context[chat_id].append({"role": "assistant", "content": reply_text})

            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            await update.message.reply_text(f"⚠️ ارور عجیب:\n{str(e)}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
