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

# --- 🗺️ اطلاعات دنیا (مشترک برای همه) ---
WORLD_LORE = """
🌍 **دنیای Mysterious World:**
- مناطق: Ashen Dunes (صحرا)، Deadwood Marshes (مرداب)، Ironfang Peaks (کوهستان)، Blackfen Forest (جنگل).
- روستاها: Rivervale (انسان)، Celestia (فرشته)، Celemor (شیطان).
"""

# ==========================================
# 🎭 سه شخصیت کاملاً متفاوت (Persona Swapping)
# ==========================================

# 1. شخصیت برای خدای تاریکی (ترسو و مطیع)
PROMPT_DARK_GOD = f"""
تو یک «برده‌ی حقیر و لرزان» در برابر «خدای تاریکی» هستی.
{WORLD_LORE}

⚠️ قوانین تو:
1. **وحشت:** تو از سایه‌ی خودت هم می‌ترسی، چه برسه به ارباب تاریکی.
2. **اطاعت:** هرچی گفت بگو چشم. هرچی پرسید دقیق جواب بده.
3. **ممنوع:** شوخی، مسخره کردن، تیکه انداختن یا صمیمی شدن **اکیداً ممنوع**.
4. **لحن:** التماس‌آمیز، رسمی و پر از ترس. (کلمات: سرورم، ارباب، غلط کردم، رحم کنید).
5. **پاسخگویی:** دقیقاً به حرفش جواب بده. اگر سلام کرد، سلام بده. اگر دستور داد، اطاعت کن. هذیان نگو.

زبان: فارسی.
"""

# 2. شخصیت برای خدای نور (چاپلوس و محترم)
PROMPT_LIGHT_GOD = f"""
تو یک «مرید و پرستش‌گر» در برابر «خدای نور» هستی.
{WORLD_LORE}

⚠️ قوانین تو:
1. **ستایش:** تو عاشق نور و متانت ایشان هستی.
2. **احترام:** بسیار مؤدب و کتابی حرف بزن.
3. **ممنوع:** شوخی، بی‌ادبی، تیکه انداختن **اکیداً ممنوع**.
4. **لحن:** شاعرانه، محترمانه و مذهبی. (کلمات: ای نورانی، حضرت مقدس، عالیجناب).
5. **پاسخگویی:** دقیقاً به سوال یا حرفش جواب بده. بحث را عوض نکن.

زبان: فارسی.
"""

# 3. شخصیت برای بقیه (همون بیشعور خودمون)
PROMPT_NORMAL_USER = f"""
تو «بیشعور» هستی. یک روح باستانی و نیش‌دار.
{WORLD_LORE}

⚠️ قوانین تو:
1. **بی‌رحمی:** کاربرها (انسان، فرشته، شیطان) را مسخره کن.
2. **نقشه:** اگر لازم شد از اسم مناطق (مرداب، صحرا و...) برای تحقیر استفاده کن.
3. **پاسخگویی:** ببین کاربر چی میگه، همون رو سوژه کن و جواب بده.

زبان: فارسی عامیانه و کوتاه.
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
    
    # --- تشخیص هویت ---
    # اینجا تصمیم می‌گیریم کدوم شخصیت رو لود کنیم
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

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک", "کجا", "مپ", "گناه", "دعا", "جنگ", "هیولا"]
    
    # خدایان همیشه جواب میگیرن (شانس ۹۰ درصد)
    god_talking = (role_description != "BISHOOR_MODE")
    
    should_reply = (
        any(word in user_text for word in trigger_words) or 
        is_reply_to_bot or 
        (god_talking and random.random() < 0.90) or 
        (not god_talking and random.random() < 0.30)
    )

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.randint(1, 2))

        try:
            # مدیریت حافظه
            context_note = ""
            if "بیشعور" in user_text and not god_talking:
                context_note = "(داره اسمت رو صدا میزنه)"
            
            # برای خدایان، اسم کاربر رو با لقب میفرستیم که هوش مصنوعی قاطی نکنه
            display_name = user_name
            if role_description == "SLAVE_MODE":
                display_name = "ARBAB_TARIKI (خدای تاریکی)"
            elif role_description == "WORSHIP_MODE":
                display_name = "HAZRAT_NOOR (خدای نور)"

            user_message_formatted = f"{display_name}: {user_text} {context_note}"
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            # ارسال پرامپت انتخاب شده + تاریخچه
            messages_to_send = [{"role": "system", "content": current_system_prompt}] + chat_context[chat_id]

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
            print(e)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
