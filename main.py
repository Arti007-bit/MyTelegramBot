import os
import re
from datetime import datetime, time, timedelta
from aiohttp import web
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ChatPermissions

# =========================
# Bot config
# =========================
TOKEN = os.environ["TOKEN"]
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") + WEBHOOK_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher()

GROUP_ID = -1003545437254

CLOSE_FROM = time(23, 0)
OPEN_AT = time(7, 0)

# =========================
# Scheduler helpers
# =========================
def is_closed_now():
    now = (datetime.utcnow() + timedelta(hours=3, minutes=30)).time()
    if CLOSE_FROM < OPEN_AT:
        return CLOSE_FROM <= now < OPEN_AT
    else:
        return now >= CLOSE_FROM or now < OPEN_AT

async def lock_group():
    try:
        await bot.set_chat_permissions(
            chat_id=GROUP_ID,
            permissions=ChatPermissions(can_send_messages=False)
        )
        print("Group locked")
    except Exception as e:
        print("Lock error:", e)

async def unlock_group():
    try:
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
    except Exception as e:
        print("Unlock error:", e)

async def scheduler_task(app):
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

@dp.message(Command(commands=["پاکسازی", "purge"]))
async def purge_messages(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        await message.reply("⛔ فقط مدیران می‌توانند پاکسازی انجام دهند.")
        return

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.reply("❗️فرمت درست:\n/پاکسازی 50")
        return

    count = int(args[1])
    if count < 1:
        return
    if count > 100:
        count = 100

    messages_to_delete = []
    # از get_chat_history استفاده نمی‌کنیم، از get_updates به عنوان workaround
    # یا می‌توان به جای آن از delete_message جداگانه استفاده کرد
    # در اینجا ساده‌ترین روش:
    for i in range(message.message_id, message.message_id - count - 1, -1):
        messages_to_delete.append(i)

    try:
        await bot.delete_messages(chat_id=message.chat.id, message_ids=messages_to_delete)
    except Exception as e:
        print("Purge error:", e)

@dp.message(F.text == "سکوت")
async def mute_user_by_reply(message: Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    if not message.reply_to_message:
        await message.reply("❗️برای سکوت باید روی پیام کاربر ریپلای کنی.")
        return
    admin = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if admin.status not in ["administrator", "creator"]:
        await message.reply("⛔ فقط مدیران می‌توانند سکوت کنند.")
        return

    target_user = message.reply_to_message.from_user
    target_member = await bot.get_chat_member(message.chat.id, target_user.id)
    if target_member.status in ["administrator", "creator"]:
        await message.reply("⛔ نمی‌توان مدیر را ساکت کرد.")
        return

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await message.answer(f"🔇 {target_user.full_name} ساکت شد.")
    except Exception as e:
        await message.reply("❌ خطا در ساکت کردن کاربر.")
        print(e)

@dp.message(F.new_chat_members)
async def welcome_handler(message: Message):
    for user in message.new_chat_members:
        await message.answer(f"👋 خوش آمدی {user.full_name}!")

@dp.message(F.left_chat_member)
async def goodbye_handler(message: Message):
    user = message.left_chat_member
    await message.answer(f"👋 خداحافظ {user.full_name}")

@dp.message(F.chat.type.in_(["group", "supergroup"]))
async def delete_links(message: Message):
    text = message.text or message.caption
    if not text:
        return
    if re.search(r"(https?://|www\.)", text):
        try:
            await message.delete()
        except:
            pass

# =========================
# Webhook server
# =========================
async def handle_webhook(request):
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response(text="OK")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    # scheduler را به عنوان background task اضافه می‌کنیم
    app['scheduler'] = asyncio.create_task(scheduler_task(app))
    print("Webhook set:", WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    app['scheduler'].cancel()

def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    PORT = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    main()
