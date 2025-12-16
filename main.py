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

# --- 🧠 حافظه ربات (برای اینکه یادش نره) ---
# هر گروه (Chat ID) یک لیست پیام جداگانه دارد
# ما فقط ۶ پیام آخر را نگه می‌داریم که گیج نشه و سرعتش کم نشه
chat_context = defaultdict(list)

# --- 🗺️ اطلاعات دنیای بازی (با قانون سخت‌گیرانه) ---
WORLD_LORE = """
🌍 **دنیای "Mysterious World":**
تو فقط و فقط در این دنیا وجود داری. دنیای بیرون (اینترنت، ماشین، گوشی، فوتبال) برای تو وجود ندارد.
اگر کاربر حرفی از دنیای واقعی زد، مسخره‌اش کن که داره هذیان میگه.

📍 **شناسنامه مناطق:**
1. **کلیسای نقره‌ای:** غسالخونه‌ی روح. جای آدم‌های گناه‌کار و ضعیف که دنبال بخشش هستن.
2. **مرداب:** بدبو، چسبناک. جای آدم‌های کندذهن.
3. **صحرا:** خشک و سوزان. جای آدم‌های خشک‌مغز.
4. **جنگل:** تاریک و ترسناک.
5. **کوهستان:** سفت و سنگی.

⚠️ **خط قرمز:**
هرگز اسم "هیولای باستانی" را نبر. فقط بگو "هیولاها" یا "موجودات".
"""

# --- دستورالعمل سیستم ---
SYSTEM_PROMPT = f"""
تو «بیشعور» هستی. یک روح باستانی و سرگردان در Mysterious World.

🆔 **هویت:**
اسم تو "بیشعور" است. اگر صدایت زدند، جواب بده (ها؟ جانم؟).

🚫 **قانون حیاتی (WORLD LOCK):**
موضوع صحبت فقط باید درباره همین دنیا باشد.
اگر کسی درباره چیزهای دیگر حرف زد، بگو: "این چرت و پرت‌ها چیه؟ مغزت رو هیولا خورده؟"

🧠 **قانون حافظه:**
تو الان پیام‌های قبلی رو یادت میاد. اگر کاربر داره جواب حرف قبلی تو رو میده، گیج نزن! ادامه همون بحث رو برو.

{WORLD_LORE}

زبان: فارسی عامیانه، کوتاه و نیش‌دار.
"""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if not client:
        await update.message.reply_text("❌ کلید Groq نیست!", reply_to_message_id=update.message.message_id)
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name
    
    # تشخیص ریپلای روی ربات
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    # چک کردن کلمات حساس
    called_by_name = "بیشعور" in user_text
    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک", "کجا", "گناه", "دعا", "جنگ", "هیولا"]
    
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30) or is_reply_to_bot

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.randint(1, 2))

        try:
            # --- مدیریت حافظه (Memory Management) ---
            # 1. اضافه کردن پیام جدید کاربر به حافظه
            context_note = ""
            if called_by_name:
                context_note = "(داره اسمت رو صدا میزنه، جواب بده)"
            elif is_reply_to_bot:
                context_note = "(داره جواب حرف قبلی خودت رو میده، یادت بیاد چی گفتی)"

            user_message_formatted = f"{user_name}: {user_text} {context_note}"
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            # 2. اگر حافظه خیلی پر شد (بیشتر از 6 پیام)، قدیمیا رو پاک کن که قاطی نکنه
            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            # 3. ساخت لیست پیام‌ها برای ارسال به هوش مصنوعی
            # اول دستور سیستم، بعد کل تاریخچه چت
            messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_context[chat_id]

            # 4. درخواست به Groq
            chat_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="llama-3.3-70b-versatile", 
                temperature=0.7, 
                top_p=0.9,
                max_tokens=150,
            )

            reply_text = chat_completion.choices[0].message.content
            
            # 5. اضافه کردن جواب ربات به حافظه (تا دفعه بعد یادش بمونه چی گفته)
            chat_context[chat_id].append({"role": "assistant", "content": reply_text})

            await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                 await update.message.reply_text(f"⚠️ ارور فنی:\n{error_msg}", reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
