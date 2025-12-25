import os
import re
import asyncio
from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = os.environ["TOKEN"]
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL") + WEBHOOK_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= handlers =================

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("ربات آنلاین است ✅ (Webhook فعال)")


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

# ================= webhook server =================

async def handle_webhook(request):
    update = await request.json()
    await dp.feed_webhook_update(bot, update)
    return web.Response(text="OK")


async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
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
