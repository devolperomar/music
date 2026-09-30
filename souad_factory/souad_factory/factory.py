import json, os, sys, subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, FACTORY_TOKEN, FACTORY_OWNER, SOURCE_NAME

DB = "db.json"
procs = {}

def load():
    return json.load(open(DB, encoding="utf-8")) if os.path.exists(DB) else {}

def save(d):
    json.dump(d, open(DB, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def run_bot(bot_id, cfg):
    env = os.environ.copy()
    env.update({
        "API_ID": str(API_ID), "API_HASH": API_HASH,
        "BOT_TOKEN": cfg["token"], "SESSION": cfg["session"],
        "OWNER_ID": str(cfg["owner"]), "SOURCE_NAME": SOURCE_NAME,
    })
    old = procs.get(bot_id)
    if old and old.poll() is None:
        old.terminate()
    procs[bot_id] = subprocess.Popen([sys.executable, "music_bot.py"], env=env)

app = Client("factory", api_id=API_ID, api_hash=API_HASH, bot_token=FACTORY_TOKEN)
steps = {}

@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    await m.reply(f"اهلاً بك في مصنع {SOURCE_NAME} 🎧\nارسل /create لانشاء بوت موسيقى جديد.")

@app.on_message(filters.command("create") & filters.private)
async def create(_, m: Message):
    steps[m.from_user.id] = {"step": "token", "data": {}}
    await m.reply("1️⃣ ارسل توكن البوت (من @BotFather):")

@app.on_message(filters.private & filters.text & ~filters.command(["start", "create", "bots", "stop"]))
async def wizard(_, m: Message):
    uid = m.from_user.id
    if uid not in steps:
        return
    s = steps[uid]; t = m.text.strip()

    if s["step"] == "token":
        if ":" not in t:
            return await m.reply("التوكن غير صحيح، ارسله مرة اخرى.")
        s["data"]["token"] = t; s["step"] = "session"
        try: await m.delete()
        except Exception: pass
        await m.reply("2️⃣ ارسل كود جلسة Pyrogram للحساب المساعد:")
    elif s["step"] == "session":
        s["data"]["session"] = t; s["step"] = "owner"
        try: await m.delete()
        except Exception: pass
        await m.reply("3️⃣ ارسل ايدي مطور البوت (رقم):")
    elif s["step"] == "owner":
        if not t.isdigit():
            return await m.reply("ارسل رقم صحيح.")
        cfg = s["data"]; cfg["owner"] = int(t)
        bot_id = cfg["token"].split(":")[0]
        db = load(); db[bot_id] = cfg; save(db)
        try:
            run_bot(bot_id, cfg)
            await m.reply(f"✅ تم انشاء وتشغيل البوت ({SOURCE_NAME})!\nضيفه ومعاه الحساب المساعد في المجموعة واكتب: تشغيل اسم الاغنية")
        except Exception as e:
            await m.reply(f"❌ خطأ: {e}")
        del steps[uid]

@app.on_message(filters.command("bots") & filters.user(FACTORY_OWNER))
async def list_bots(_, m: Message):
    db = load()
    await m.reply("\n".join(f"{k} | مطور: {v['owner']}" for k, v in db.items()) or "لا يوجد بوتات")

@app.on_message(filters.command("stop") & filters.user(FACTORY_OWNER))
async def stop(_, m: Message):
    if len(m.command) < 2:
        return await m.reply("/stop bot_id")
    p = procs.pop(m.command[1], None)
    if p:
        p.terminate(); await m.reply("تم الايقاف")

for bid, cfg in load().items():
    run_bot(bid, cfg)

app.run()
