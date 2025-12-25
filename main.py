import os
import re
import asyncio
from datetime import datetime, time, timedelta
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatPermissions

TOKEN = os.environ["TOKEN"]

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") + WEBHOOK_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# تنظیمات قفل گروه (به وقت تهران)
# =========================
GROUP_ID = -1003545437254

CLOSE_FROM = time(19, 15)
OPEN_AT   = time(19, 19)


def is_closed_now():
    # تبدیل UTC به تهران (UTC + 3:30)
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

        await asyncio.sleep(60)  # هر ۱ دقیقه


# =========================
# handlers
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("ربات آنلاین است ✅")


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
# webhook server
# =========================

async def handle_webhook(request):
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response(text="OK")


async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(scheduler())  # قفل ساعتی
    print("Webhook set:", WEBHOOK_URL)


async def on_shutdown(app):
    await bot.delete_webhook()


def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, port=int(os.environ.get("PORT", 10000)))


if __name__ == "__main__":
    main()
