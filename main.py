import asyncio
import re

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import BaseFilter
from config import BOT_TOKEN

# --------------------
# تنظیمات
# --------------------
LINK_REGEX = re.compile(
    r"(https?://\S+|www\.\S+)",
    re.IGNORECASE
)

# --------------------
# Bot / Dispatcher / Router
# --------------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --------------------
# حذف لینک‌ها
# --------------------
@router.message()
async def delete_links(message: types.Message):
    text = message.text or ""
    caption = message.caption or ""

    # حذف لینک در متن یا کپشن
    if LINK_REGEX.search(text) or LINK_REGEX.search(caption):
        await message.delete()
        return

    # حذف لینک در entity ها
    for entity in message.entities or []:
        if entity.type in ("url", "text_link"):
            await message.delete()
            return

    for entity in message.caption_entities or []:
        if entity.type in ("url", "text_link"):
            await message.delete()
            return

# --------------------
# Chat Member Updates (Join/Leave)
# --------------------
@router.chat_member()
async def member_update(chat_member_update: types.ChatMemberUpdated):
    chat_id = chat_member_update.chat.id
    user_name = chat_member_update.new_chat_member.user.full_name

    # وقتی کسی به گروه اضافه شد
    if chat_member_update.new_chat_member.status == "member":
        await bot.send_message(chat_id, f"سلام {user_name} خوش اومدی به گروه!")

    # وقتی کسی گروه را ترک کرد یا بن شد
    elif chat_member_update.new_chat_member.status in ("left", "kicked"):
        await bot.send_message(chat_id, f"{user_name} از گروه رفت!")

# --------------------
# main
# --------------------
async def main():
    dp.include_router(router)
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
