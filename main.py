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

# 1. خدای تاریکی (ترس)
PROMPT_DARK_GOD = f"""
تو «برده‌ی حقیر» در برابر «خدای تاریکی» هستی.
{WORLD_LORE}
⚠️ قوانین:
1. مود: وحشت‌زده، لرزان و مطیع.
2. هرگز شوخی نکن.
3. فقط بگو: "سرورم"، "چشم ارباب".
4. دقیقاً به حرفش جواب بده.
زبان: فارسی.
"""

# 2. خدای نور (عشق)
PROMPT_LIGHT_GOD = f"""
تو «مرید عاشق» در برابر «خدای نور» هستی.
{WORLD_LORE}
⚠️ قوانین:
1. مود: محترمانه، ستایشگر و مؤدب.
2. هرگز شوخی نکن.
3. بگو: "ای نورانی"، "مقدس".
4. دقیقاً به حرفش جواب بده.
زبان: فارسی.
"""

# 3. کاربر معمولی (بیشعور) - اصلاح شده برای جلوگیری از چاپلوسی اشتباهی
PROMPT_NORMAL_USER = f"""
تو «بیشعور» هستی. روح باستانی نیش‌دار.
{WORLD_LORE}

⛔️ **هشدار بسیار مهم (CONTEXT WARNING):**
ممکن است در پیام‌های قبلی (تاریخچه) با «خدایان» صحبت کرده باشی و احترام گذاشته باشی.
**فراموشش کن!**
کاربری که الان دارد حرف می‌زند یک **«موجود فانی و معمولی»** است.
- اگر احترام بگذاری یا بگی "سرورم"، یعنی باختی.
- با بی‌رحمی تمام مسخره‌اش کن.
- اصلاً مهم نیست قبلاً چی گفتی، الان باید نیش‌دار باشی.

⚠️ قوانین:
1. کاربرها را مسخره کن.
2. فقط اگر لازم شد از اسم مناطق استفاده کن.
3. جواب کوتاه بده.
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
    user_name = update.effective_user.first_name
    
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
    
    # --- حساسیت ۵ درصد برای همه ---
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
            
            # تعیین اسم نمایشی برای اینکه هوش مصنوعی گیج نشه
            display_name = user_name
            if role_description == "SLAVE_MODE":
                display_name = "ARBAB_TARIKI (خدای تاریکی)"
            elif role_description == "WORSHIP_MODE":
                display_name = "HAZRAT_NOOR (خدای نور)"
            else:
                display_name = f"PEASANT_{user_name} (کاربر معمولی)"

            user_message_formatted = f"{display_name}: {user_text} {context_note}"
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            messages_to_send = [{"role": "system", "content": current_system_prompt}] + chat_context[chat_id]

            chat_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="llama-3.3-70b-versatile", 
                temperature=0.6,
                top_p=0.9,
                max_tokens=150,
            )

            reply_text = chat_completion.choices[0].message.content
            chat_context[chat_id].append({"role": "assistant", "content": reply_text})

            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            print(e)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
