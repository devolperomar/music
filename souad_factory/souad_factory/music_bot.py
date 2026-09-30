import os, asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import yt_dlp

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION = os.environ["SESSION"]
OWNER_ID = int(os.environ["OWNER_ID"])
SOURCE_NAME = os.environ.get("SOURCE_NAME", "سواد")

bot = Client(f"bot_{BOT_TOKEN.split(':')[0]}", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
assistant = Client(f"asst_{BOT_TOKEN.split(':')[0]}", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
calls = PyTgCalls(assistant)

YDL = {"format": "bestaudio/best", "quiet": True, "noplaylist": True, "default_search": "ytsearch1"}
if os.path.exists("cookies.txt"):
    YDL["cookiefile"] = "cookies.txt"

def search(query):
    with yt_dlp.YoutubeDL(YDL) as y:
        info = y.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        return info["title"], info["url"]

@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply(f"🎧 بوت {SOURCE_NAME}\nاكتب داخل المجموعة: تشغيل + اسم الاغنية")

@bot.on_message(filters.group & filters.regex(r"^(تشغيل|play)\s+(.+)"))
async def play(_, m: Message):
    query = m.matches[0].group(2)
    msg = await m.reply("🔎 جاري البحث...")
    try:
        try:
            await assistant.get_chat_member(m.chat.id, "me")
        except Exception:
            link = await bot.export_chat_invite_link(m.chat.id)
            await assistant.join_chat(link)
        title, url = await asyncio.get_event_loop().run_in_executor(None, search, query)
        await calls.play(m.chat.id, MediaStream(url))
        await msg.edit(f"▶️ يتم التشغيل:\n{title}\n\n— {SOURCE_NAME}")
    except Exception as e:
        await msg.edit(f"❌ خطأ: {e}")

@bot.on_message(filters.group & filters.regex(r"^(ايقاف|stop)$"))
async def stop(_, m: Message):
    await calls.leave_call(m.chat.id); await m.reply("⏹ تم الايقاف")

@bot.on_message(filters.group & filters.regex(r"^(وقف مؤقت|pause)$"))
async def pause(_, m: Message):
    await calls.pause_stream(m.chat.id); await m.reply("⏸")

@bot.on_message(filters.group & filters.regex(r"^(استكمال|resume)$"))
async def resume(_, m: Message):
    await calls.resume_stream(m.chat.id); await m.reply("▶️")

async def main():
    await bot.start(); await assistant.start(); await calls.start()
    await idle()

asyncio.get_event_loop().run_until_complete(main())
