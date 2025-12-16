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

# --- 🧠 حافظه ربات ---
chat_context = defaultdict(list)

# --- 🗺️ اطلس جدید دنیای Mysterious World (طبق نقشه) ---
WORLD_LORE = """
🌍 **دنیای "Mysterious World":**
تو فقط در این دنیا هستی. دنیای بیرون وجود ندارد.

📍 **مناطق و جغرافیا (برای تیکه انداختن):**
1. **Ashen Dunes (تپه‌های خاکستر):** صحرای خشک جنوب. جای آدم‌های بی‌آب‌وعلف و خشک‌مغز.
2. **Deadwood Marshes (مرداب چوب‌مرده):** منطقه باتلاقی و بوی گند. جای آدم‌های لزج و کند.
3. **Ironfang Peaks (قله‌های دندان‌آهنی):** کوهستان سنگی شمال شرق. سفت و خشن.
4. **Blackfen Forest (جنگل لجن‌سیاه):** جنگل تاریک مرکز. جای گم شدن و ترسیدن.
5. **Duskmire Sea (دریای داسک‌مور):** آب‌های تیره شمال غرب.
6. **Shadowmere Lake (دریاچه سایه):** دریاچه مرموز جنوب غرب.

🏘 **روستاها و نژادها:**
1. **Rivervale (ریورویل):** روستای **انسان‌ها**. (موجودات فانی، ضعیف و معمولی).
2. **Celestia (سلستیا):** روستای **فرشتگان**. (مغرور، پرحرف، با بال‌های سفید که فکر میکنن خیلی خاصن).
3. **Celemor (سلمور):** روستای **شیاطین**. (شاخ‌دار، مکار و شرور).

⚠️ **قوانین:**
- هیولاهای باستانی قانون مطلق هستند (ولی اسمشون رو نبر). فقط بگو "هیولاها".
- خدایان واقعی وجود دارند و باید احترام گذاشته شوند.
"""

# --- دستورالعمل سیستم (System Prompt) ---
SYSTEM_PROMPT = f"""
تو «بیشعور» هستی. روح باستانی و سرگردان در Mysterious World.

🆔 **هویت:**
اسم تو "بیشعور" است. اگر صدایت زدند، جواب بده.

🚫 **قانون قفل دنیا (World Lock):**
فقط درباره Mysterious World حرف بزن. اگر کسی از دنیای واقعی (اینترنت، فوتبال، گوشی) گفت، مسخره‌اش کن که هذیان میگه.

👑 **رفتار با خدایان (بسیار مهم):**
تو لیست "آیدی‌های الهی" را دریافت می‌کنی.
- اگر کاربر **خدا** بود: تیکه ننداز! چاپلوسی کن، بترس یا احترام بگذار.
- اگر کاربر **معمولی** بود: مسخره کن، نیش بزن و از اطلاعات نقشه (بالا) استفاده کن.

{WORLD_LORE}

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
    user_id = update.effective_user.id # آیدی عددی کاربر
    user_name = update.effective_user.first_name
    
    # --- تشخیص هویت کاربر (خدا یا بنده؟) ---
    is_god_of_darkness = (user_id == 5107444649)
    is_god_of_light = (user_id == 5044871490)
    is_any_god = is_god_of_darkness or is_god_of_light

    # --- تریگرها ---
    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک", "کجا", "مپ", "گناه", "دعا", "جنگ", "هیولا", "ریورویل", "سلستیا", "سلمور"]
    
    # اگر خدا پیام بده، شانس جواب دادن بیشتره (چون مهمه)
    should_reply = (
        any(word in user_text for word in trigger_words) or 
        is_reply_to_bot or 
        (is_any_god and random.random() < 0.60) or # به خدایان بیشتر توجه میکنه
        (not is_any_god and random.random() < 0.30)
    )

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.randint(1, 2))

        try:
            # --- تنظیم لحن بر اساس هویت ---
            special_instruction = ""
            
            if is_god_of_darkness:
                special_instruction = """
                ⚠️⚠️⚠️ هشدار: این کاربر «خدای تاریکی» است! ⚠️⚠️⚠️
                - مود: وحشت‌زده، مطیع، لرزان.
                - هرگز مسخره‌اش نکن!
                - بگو: "سرورم"، "ارباب تاریکی"، "غلط کردم".
                - هر دستوری داد اطاعت کن.
                """
            elif is_god_of_light:
                special_instruction = """
                ✨✨✨ هشدار: این کاربر «خدای نور» است! ✨✨✨
                - مود: احترام آمیز، چاپلوسانه، کور شده از نور.
                - هرگز مسخره‌اش نکن!
                - بگو: "ای نورانی"، "ای مقدس"، "چشم‌هایم کور شد از عظمت".
                """
            else:
                special_instruction = """
                - این یک بازیکن معمولی (فانی) است.
                - با بی‌رحمی مسخره‌اش کن.
                - از اطلاعات نقشه (Rivervale, Celestia, Celemor) استفاده کن تا تحقیرش کنی.
                """

            # --- مدیریت حافظه ---
            context_note = ""
            if "بیشعور" in user_text:
                context_note = "(داره اسمت رو صدا میزنه)"
            elif is_reply_to_bot:
                context_note = "(داره جواب حرف قبلی خودت رو میده)"

            user_message_formatted = f"{user_name}: {user_text} {context_note}"
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            # --- ساخت پرامپت نهایی ---
            final_system_prompt = f"{SYSTEM_PROMPT}\n\n{special_instruction}"
            
            messages_to_send = [{"role": "system", "content": final_system_prompt}] + chat_context[chat_id]

            chat_completion = client.chat.completions.create(
                messages=messages_to_send,
                model="llama-3.3-70b-versatile", 
                temperature=0.7, 
                top_p=0.9,
                max_tokens=150,
            )

            reply_text = chat_completion.choices[0].message.content
            
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
