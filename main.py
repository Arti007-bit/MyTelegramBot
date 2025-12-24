import asyncio
import os
import re
from datetime import datetime, time

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatPermissions

TOKEN = os.environ["TOKEN"]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ======================
# تنظیمات قفل گروه
# ======================
GROUP_ID = -1001234567890  # آیدی عددی گروه
CLOSE_FROM = time(23, 0)   # از ساعت 23:00
OPEN_AT = time(7, 0)       # تا ساعت 07:00


def is_closed_now():
    now = datetime.now().time()

    # بازه شبانه
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


# ======================
# هندلرها
# ======================

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("سلام! ربات با موفقیت روی Render اجرا شد ✅")


@dp.message(F.new_chat_members)
async def welcome_handler(message: Message):
    for user in message.new_chat_members:
        await message.answer(f"👋 خوش آمدی {user.full_name}!")


@dp.message(F.left_chat_member)
async def goodbye_handler(message: Message):
    user = message.left_chat_member
    await message.answer(f"👋 خداحافظ {user.full_name}")

@dp.message(F.text == "/id")
async def group_id_handler(message: Message):
    await message.answer(f"Group ID: {message.chat.id}")



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


# ======================
# main
# ======================
async def main():
    asyncio.create_task(scheduler())  # ⬅️ مهم
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
