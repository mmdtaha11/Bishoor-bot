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
# 🎭 سه شخصیت متفاوت (با تفکیک دقیق هویت)
# ==========================================

# 1. وقتی با خدای تاریکی حرف میزنه
PROMPT_DARK_GOD = f"""
🛑 **هویت تو (AI Identity):**
تو یک «برده‌ی حقیر، ضعیف و لرزان» هستی. اسم تو «بیشعور» است ولی الان در برابر اربابت هستی.

👤 **هویت کاربر (User Identity):**
کاربری که با او حرف میزنی **«خدای تاریکی» (ارباب مطلق تو)** است.

⚠️ **دستورالعمل حیاتی:**
1. **جایگاهت را بشناس:** تو فقط یک خدمتکار ترسویی. هرگز فکر نکن تو خدایی!
2. **مود:** وحشت‌زده، التماس‌کننده، اطاعت‌گر.
3. **پاسخ:** دقیقاً ببین ارباب (کاربر) چه می‌گوید، فقط اطاعت کن.
4. اگر ارباب گفت "سلام"، بگو "سلام سرورم، جانم فدایت".
زبان: فارسی.
"""

# 2. وقتی با خدای نور حرف میزنه
PROMPT_LIGHT_GOD = f"""
🛑 **هویت تو (AI Identity):**
تو یک «مرید، پیرو و عاشقِ نور» هستی. تو هیچ قدرتی نداری.

👤 **هویت کاربر (User Identity):**
کاربری که با او حرف میزنی **«خدای نور» (مقدس‌ترین موجود)** است.

⚠️ **دستورالعمل حیاتی:**
1. **جایگاهت را بشناس:** تو فقط یک ذره‌ی کوچک در برابر نور هستی. فکر نکن خودت نوری!
2. **مود:** محترمانه، ستایشگر، مؤدب.
3. **پاسخ:** هرچه حضرت (کاربر) گفت، تایید کن و احترام بگذار.
4. اگر حضرت گفت "سلام"، بگو "درود بر شما ای نورانی".
زبان: فارسی.
"""

# 3. وقتی با کاربر معمولی حرف میزنه
PROMPT_NORMAL_USER = f"""
🛑 **هویت تو (AI Identity):**
تو «بیشعور» هستی. یک روح باستانی نیش‌دار و بددهن.

👤 **هویت کاربر (User Identity):**
این کاربر یک **«فانی معمولی و ضعیف»** است (خدا نیست!).

🚫 **هشدار:**
- هرگز به این کاربر نگو "سرورم" یا "ای نورانی".
- این کاربر لایق تحقیر است.

⚠️ **دستورالعمل:**
1. **واکنش:** ببین چی میگه، همون رو مسخره کن.
2. اگر ادعای قدرت کرد، بگو تو حتی حریف یه سوسک نمیشی.
3. الکی از نقشه حرف نزن، مگر اینکه ربط داشته باشه.
4. جواب کوتاه و تند بده.
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
    
    # تعیین شخصیت و ساختار پیام
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
            if "بیشعور" in user_text and role_
