import os
import re
import asyncio
from datetime import datetime, time, timedelta
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ChatPermissions

# =========================
# Bot config
# =========================

TOKEN = "8413366358:AAHs2Pw-fmOrNhmXiSSijbkEIHF5ACx8TUk"

WEBHOOK_PATH = "/webhook"
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# Group lock settings (Tehran time)
# =========================

GROUP_ID = -1003545437254

CLOSE_FROM = time(23, 0)
OPEN_AT    = time(7, 0)

def is_closed_now():
    now = (datetime.utcnow() + timedelta(hours=3, minutes=30)).time()
    if CLOSE_FROM < OPEN_AT:
        return CLOSE_FROM <= now < OPEN_AT
    else:
        return now >= CLOSE_FROM or now < OPEN_AT

async def lock_group():
    await bot.set_chat_permissions(
        chat_id=GROUP_ID,
        permissions=ChatPermissions(can_send_messages=False)
    )
    print("Group locked")

async def unlock_group():
    await bot.set_chat_permissions(
        chat_id=GROUP_ID,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    print("Group unlocked")

async def scheduler():
    locked = False
    while True:
        try:
            if is_closed_now() and not locked:
                await lock_group()
                locked = True
            elif not is_closed_now() and locked:
                await unlock_group()
                locked = False
        except Exception as e:
            print("Scheduler error:", e)

        await asyncio.sleep(60)

# =========================
# Handlers
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("ربات آنلاین است ✅")

# ---- تست دریافت پیام در گروه
@dp.message(Command("test"))
async def test_handler(message: Message):
    await message.reply("✅ پیام گروه دریافت شد")

# ---- باز کردن دستی گروه
@dp.message(Command("باز"))
async def manual_unlock(message: Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return

    await unlock_group()
    await message.reply("🔓 گروه باز شد")

# ---- قفل دستی گروه
@dp.message(Command("قفل"))
async def manual_lock(message: Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        return

    await lock_group()
    await message.reply("🔒 گروه قفل شد")

# ---- سکوت با ریپلای
@dp.message(F.text == "سکوت")
async def mute_user(message: Message):
    if not message.reply_to_message:
        return

    admin = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if admin.status not in ["administrator", "creator"]:
        return

    target = message.reply_to_message.from_user
    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=target.id,
        permissions=ChatPermissions(can_send_messages=False)
    )
    await message.reply(f"🔇 {target.full_name} ساکت شد")

# ---- حذف لینک
@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def delete_links(message: Message):
    text = message.text or message.caption
    if text and re.search(r"(https?://|www\.)", text):
        await message.delete()

# =========================
# خوش آمد و خداحافظی
# =========================

@dp.message()
async def welcome_and_farewell(message: Message):
    # اعضای جدید
    if message.new_chat_members:
        for user in message.new_chat_members:
            username = f"@{user.username}" if user.username else user.full_name
            await message.reply(f"خوش آمدی {username} 🌟")
    
    # کاربری که خارج شد
    if message.left_chat_member:
        user = message.left_chat_member
        username = f"@{user.username}" if user.username else user.full_name
        await message.reply(f"خداحافظ {username} 👋")

# =========================
# Webhook server (FIXED)
# =========================

async def handle_webhook(request):
    update = await request.json()
    # 🔴 FIX اصلی: غیرمسدودکننده
    asyncio.create_task(dp.feed_webhook_update(bot, update))
    return web.Response(text="OK")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(scheduler())
    print("Webhook set:", WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    print("Bot session closed")

def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    main()
