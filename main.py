import os
import logging
import random
import asyncio
import requests
import json
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- دریافت توکن‌ها ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

chat_histories = {}

# --- شخصیت ربات ---
SYSTEM_PROMPT = """
تو «بیشعور» هستی. یک ربات تلگرامی که شخصیت دارد.
ویژگی‌ها: شوخ، حاضرجواب، کنایه‌زن، کمی بی‌ادب و پررو.
اگر کسی اسمت را صدا زد (بیشعور)، بگو "جانم؟" یا "ها؟".
وظیفه: کاربرها را مسخره کن و به حرف‌هایشان تیکه بنداز.
قانون: جواب‌هایت حتماً کوتاه (یک یا دو جمله) باشد.
"""

# --- تابع مستقیم اتصال به گوگل (بدون کتابخونه) ---
def ask_gemini_direct(prompt, history=[]):
    # آدرس مستقیم مدل فلش (سریع و جدید)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # ساختن ساختار پیام برای گوگل
    contents = []
    # اول شخصیت ربات رو میفرستیم
    contents.append({
        "role": "user",
        "parts": [{"text": SYSTEM_PROMPT}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": "باشه، فهمیدم. من بیشعور هستم. بگو ببینم چی میگن."}]
    })
    
    # اضافه کردن تاریخچه چت (اختیاری)
    # فعلا فقط پیام جدید رو میفرستیم که ارور کمتر بشه
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    payload = {
        "contents": contents,
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            # استخراج متن از جواب پیچیده گوگل
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except:
                return "چی گفتی؟ نفهمیدم. (ارور عجیب)"
        else:
            return f"گوگل قهر کرده! (کد خطا: {response.status_code})\n{response.text}"
            
    except Exception as e:
        return f"سیم‌هام قاطی کرد: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    message_thread_id = update.message.message_thread_id
    user_name = update.effective_user.first_name

    trigger_words = ["بیشعور", "ربات", "احمق", "خر", "نفهم", "بات", "چرا", "ساکت", "مشکل"]
    
    # شانس ۳۰ درصدی یا صدا زدن اسم
    should_reply = any(word in user_text for word in trigger_words) or (random.random() < 0.30)

    if should_reply:
        # اکشن تایپینگ
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, message_thread_id=message_thread_id)
        
        # یکم مکث که طبیعی بشه
        await asyncio.sleep(random.randint(1, 3))

        # ساخت متن ورودی
        final_prompt = f"کاربر {user_name} گفت: '{user_text}'. \n(یه جواب دندون‌شکن و مسخره بهش بده)"
        
        # دریافت جواب
        reply_text = ask_gemini_direct(final_prompt)
        
        # ارسال
        await update.message.reply_text(reply_text, reply_to_message_id=update.message.message_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
