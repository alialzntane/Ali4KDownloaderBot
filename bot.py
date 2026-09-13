import os
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "tiktok.com" not in url:
        await update.message.reply_text("أرسل رابط TikTok صحيح 📥")
        return

    msg = await update.message.reply_text("⏳ جاري تحميل الفيديو بأعلى جودة متاحة...")

    try:
        loop = asyncio.get_running_loop()

        def download():
            options = {
                "format": "best[ext=mp4]/best",
                "outtmpl": "video.%(ext)s",
                "noplaylist": True,
                "quiet": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await loop.run_in_executor(None, download)

        await msg.edit_text("✅ تم التحميل، جاري الإرسال...")

        with open(filename, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption="🎬 تم التحميل\n\nصاحب البوت: @ali_alzntane"
            )

        os.remove(filename)

    except Exception as e:
        await msg.edit_text("❌ ما قدرت نحمل الفيديو. تأكد من الرابط وحاول مرة ثانية.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, download_video)
    )
    app.run_polling()

if __name__ == "__main__":
    main()
  
