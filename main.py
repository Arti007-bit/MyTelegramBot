import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = os.environ["TOKEN"]

bot = Bot(token=TOKEN)
dp = Dispatcher()


# /start handler
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("سلام! ربات با موفقیت روی Render اجرا شد ✅")


# welcome new members
@dp.message()
async def welcome_new_member(message: Message):
    if message.new_chat_members:
        for user in message.new_chat_members:
            await message.answer(
                f"👋 خوش آمدی {user.full_name}!"
            )


# goodbye message
@dp.message()
async def goodbye_member(message: Message):
    if message.left_chat_member:
        user = message.left_chat_member
        await message.answer(
            f"👋 خداحافظ {user.full_name}"
        )


# delete links in groups
@dp.message()
async def delete_links(message: Message):
    if message.chat.type in ("group", "supergroup"):
        if message.entities:
            for entity in message.entities:
                if entity.type in ("url", "text_link"):
                    await message.delete()
                    return


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
