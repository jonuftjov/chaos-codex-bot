import asyncio
import logging
import socket
import io
import base64
import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from app import fetch_player_raw, format_response, generate_banner_png, generate_outfit_png
from ghost_logic import api_handler, connected_clients, StarT_SerVer

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# جلب التوكن من متغيرات البيئة (Secrets)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8970798772:AAExhAZkzvlks19uGBqEflinlv-FDEDrj_E")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "🔥 **مرحباً بك في بوت CHAOS CODEX المطور!**\n\n"
        "أنا بوت متخصص في جلب معلومات حسابات Free Fire والتحكم في Ghost API.\n\n"
        "📌 **أوامر جلب المعلومات**:\n"
        "- أرسل الـ **UID** مباشرة لجلب التفاصيل والصور.\n\n"
        "📌 **أوامر Ghost API**:\n"
        "- `/ghost [teamcode] [name]` : إرسال أشباح للفريق.\n"
        "- `/chat [teamcode] [message]` : إرسال رسالة شات للفريق.\n"
        "- `/invite [teamcode]` : إرسال دعوات انضمام.\n"
        "- `/status` : معرفة حالة الحسابات المتصلة."
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def ghost_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ الاستخدام: `/ghost [teamcode] [name]`")
        return
    teamcode = context.args[0]
    name = " ".join(context.args[1:])
    res = api_handler.process_ghost_command(teamcode, name, action="ghost")
    await update.message.reply_text(f"📢 {res.get('message', 'حدث خطأ')}")

async def chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ الاستخدام: `/chat [teamcode] [message]`")
        return
    teamcode = context.args[0]
    message = " ".join(context.args[1:])
    res = api_handler.process_ghost_command(teamcode, "", action="chat", message=message)
    await update.message.reply_text(f"💬 {res.get('message', 'حدث خطأ')}")

async def invite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("❌ الاستخدام: `/invite [teamcode]`")
        return
    teamcode = context.args[0]
    res = api_handler.process_ghost_command(teamcode, "", action="invite")
    await update.message.reply_text(f"📩 {res.get('message', 'حدث خطأ')}")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = len(connected_clients)
    uids = ", ".join(connected_clients.keys()) if count > 0 else "لا يوجد"
    msg = f"📊 **حالة الحسابات المتصلة**:\n\n🔹 العدد: {count}\n🔹 الحسابات: `{uids}`"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    if not uid.isdigit():
        return # تجاهل الرسائل غير الرقمية

    status_msg = await update.message.reply_text(f"🔍 جاري جلب بيانات الـ UID: `{uid}`...", parse_mode='Markdown')
    try:
        raw_data = await fetch_player_raw(uid)
        if not raw_data:
            await status_msg.edit_text("❌ لم يتم العثور على اللاعب.")
            return

        info = format_response(raw_data)
        acc = info.get("AccountInfo", {})
        response_text = (
            f"👤 **معلومات اللاعب: {acc.get('AccountName', 'غير معروف')}**\n\n"
            f"🔹 **المستوى**: {acc.get('AccountLevel', '0')}\n"
            f"🔹 **المنطقة**: {acc.get('AccountRegion', 'غير معروف')}\n"
            f"🔹 **اللايكات**: {acc.get('AccountLikes', '0')}\n"
        )
        
        try:
            banner_io, outfit_io = await asyncio.gather(
                generate_banner_png(raw_data),
                generate_outfit_png(raw_data),
            )
            banner_io.seek(0)
            outfit_io.seek(0)
            await update.message.reply_photo(photo=banner_io, caption="🖼 **بانر اللاعب**")
            await update.message.reply_photo(photo=outfit_io, caption=response_text)
            await status_msg.delete()
        except:
            await update.message.reply_text(response_text)
            await status_msg.edit_text("⚠️ تم جلب البيانات ولكن فشل توليد الصور.")
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {str(e)}")

def run_bot():
    # تشغيل Ghost API في الخلفية
    StarT_SerVer()
    
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    application = ApplicationBuilder().token(TOKEN).request(request).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ghost', ghost_cmd))
    application.add_handler(CommandHandler('chat', chat_cmd))
    application.add_handler(CommandHandler('invite', invite_cmd))
    application.add_handler(CommandHandler('status', status_cmd))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_uid))
    
    print("🚀 MERGED Bot is running...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    run_bot()
