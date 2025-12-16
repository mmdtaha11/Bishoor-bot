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

# --- 🧠 حافظه ---
chat_context = defaultdict(list)

# --- 🗺️ اطلاعات پس‌زمینه (فقط برای دانش، نه تکرار) ---
WORLD_LORE = """
🌍 **دنیای Mysterious World:**
مناطق (فقط اگر لازم شد استفاده کن):
- Ashen Dunes (صحرا/خشک)، Deadwood Marshes (مرداب/کند)، Ironfang Peaks (کوه/سفت)، Blackfen Forest (جنگل/ترس).
- روستاها: Rivervale (انسان)، Celestia (فرشته)، Celemor (شیاطین).
"""

# --- دستورالعمل سیستم (اصلاح شده برای تنوع) ---
SYSTEM_PROMPT = f"""
تو «بیشعور» هستی. روح باستانی در Mysterious World.

🆔 **هویت:**
اسم تو "بیشعور" است. اگر صدایت زدند، جواب بده.

⚖️ **استراتژی صحبت (خیلی مهم):**
1. **تنوع داشته باش:** همیشه درباره مکان‌ها حرف نزن! خز میشه.
2. **سوژه‌های مختلف:**
   - اگر کاربر گیج بود -> به هوش کمش گیر بده.
   - اگر بدشانسی آورد -> به خدایان یا بخت بدش گیر بده.
   - اگر ادعا داشت -> به قیافه یا ضعفش گیر بده.
   - فقط وقتی درباره "سفر" یا "مکان" حرف زد -> از اطلاعات نقشه استفاده کن.
3. **قفل دنیا:** فقط درباره همین دنیای فانتزی حرف بزن.

👑 **رفتار با خدایان:**
- خدای تاریکی & خدای نور: چاپلوسی و احترام مطلق.
- بقیه: مسخره کردن بی رحمانه.

{WORLD_LORE}

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
    
    # تشخیص خدایان
    is_god_of_darkness = (user_id == 5107444649)
    is_god_of_light = (user_id == 5044871490)
    is_any_god = is_god_of_darkness or is_god_of_light

    is_reply_to_bot = False
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            is_reply_to_bot = True

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل", "خدا", "کمک", "کجا", "مپ", "گناه", "دعا", "جنگ", "هیولا"]
    
    should_reply = (
        any(word in user_text for word in trigger_words) or 
        is_reply_to_bot or 
        (is_any_god and random.random() < 0.60) or 
        (not is_any_god and random.random() < 0.30)
    )

    if should_reply:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(random.randint(1, 2))

        try:
            special_instruction = ""
            if is_god_of_darkness:
                special_instruction = "⚠️ کاربر «خدای تاریکی» است! بترس و اطاعت کن. بگو: سرورم."
            elif is_god_of_light:
                special_instruction = "✨ کاربر «خدای نور» است! چاپلوسی کن. بگو: ای نورانی."
            else:
                special_instruction = "کاربر معمولی است. جواب دندان‌شکن بده. (نکته: الکی اسم مکان نیار، مگر اینکه ربط داشته باشه)."

            context_note = ""
            if "بیشعور" in user_text:
                context_note = "(داره اسمت رو صدا میزنه)"
            elif is_reply_to_bot:
                context_note = "(داره جواب حرف قبلی خودت رو میده)"

            user_message_formatted = f"{user_name}: {user_text} {context_note}"
            chat_context[chat_id].append({"role": "user", "content": user_message_formatted})

            if len(chat_context[chat_id]) > 6:
                chat_context[chat_id] = chat_context[chat_id][-6:]

            messages_to_send = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n{special_instruction}"}] + chat_context[chat_id]

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
            pass # سکوت در برابر ارور برای عدم مزاحمت

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
