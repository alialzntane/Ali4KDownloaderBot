import os
import asyncio
import tempfile
import yt_dlp

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN", "").strip()


def get_platform(url: str):
    url = url.lower()

    if "tiktok.com" in url:
        return "TikTok"

    if "facebook.com" in url or "fb.watch" in url:
        return "Facebook"

    return None


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    url = update.message.text.strip()
    platform = get_platform(url)

    if not platform:
        await update.message.reply_text(
            "❌ الرابط غير مدعوم.\n\n"
            "أرسل رابط فيديو من TikTok أو Facebook 📥"
        )
        return

    msg = await update.message.reply_text(
        f"⏳ جاري تحميل فيديو {platform} بأعلى جودة متاحة..."
    )

    filename = None

    try:
        loop = asyncio.get_running_loop()

        temp_dir = tempfile.mkdtemp(prefix="downloader_")
        output_template = os.path.join(temp_dir, "video.%(ext)s")

        def download():
            options = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "outtmpl": output_template,
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await loop.run_in_executor(None, download)

        # إذا تم دمج الفيديو إلى MP4
        if not os.path.exists(filename):
            base = os.path.splitext(filename)[0]
            mp4_file = base + ".mp4"

            if os.path.exists(mp4_file):
                filename = mp4_file

        if not os.path.exists(filename):
            raise FileNotFoundError("Downloaded file not found")

        await msg.edit_text("✅ تم التحميل، جاري إرسال الفيديو...")

        with open(filename, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption=(
                    f"🎬 تم تحميل الفيديو بنجاح\n"
                    f"📌 المصدر: {platform}\n\n"
                    f"👤 صاحب البوت: @ali_alzntane"
                ),
                supports_streaming=True,
            )

        await msg.delete()

    except Exception as e:
        print("DOWNLOAD ERROR:", repr(e))

        await msg.edit_text(
            "❌ ما قدرت نحمل الفيديو.\n\n"
            "تأكد أن الرابط عام ويحتوي على فيديو، ثم حاول مرة ثانية."
        )

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

        if filename:
            try:
                temp_dir = os.path.dirname(filename)

                if os.path.isdir(temp_dir):
                    for file in os.listdir(temp_dir):
                        try:
                            os.remove(os.path.join(temp_dir, file))
                        except Exception:
                            pass

                    try:
                        os.rmdir(temp_dir)
                    except Exception:
                        pass
            except Exception:
                pass


def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN غير موجود. أضف BOT_TOKEN في متغيرات البيئة."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            download_video,
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
