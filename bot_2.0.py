import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "BOT_TOKEN"
CHANNEL_ID = -1002499515385
ADMIN_ID = 8756799219

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

drafts: dict[int, dict] = {}
user_profiles: dict[int, dict] = {}


class RegState(StatesGroup):
    waiting_nickname = State()
    waiting_op = State()


class SearchState(StatesGroup):
    waiting_name = State()
    waiting_situation = State()
    waiting_clothes = State()
    waiting_location = State()
    waiting_photo = State()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def is_registered(user_id: int) -> bool:
    return user_id in user_profiles


def valid_op(text: str) -> bool:
    return bool(re.fullmatch(r"[1-4]", text.strip()))


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await message.answer(
            "👑 <b>Добро пожаловать, Админ!</b>\n"
            "─────────────\n\n"
            "🛠 <b>Твои возможности:</b>\n\n"
            "📢 <b>Обычный пост</b> — просто отправь сообщение\n"
            "   <i>Появится превью с кнопками</i>\n\n"
            "🔍 <b>/search</b> — заявка на поиск человека\n"
            "   <i>Заполняется в 5 шагов</i>\n\n"
            "👤 <b>/profile</b> — твой профиль\n\n"
            "─────────────\n"
            "💡 Все заявки от юзеров приходят тебе на модерацию",
            parse_mode="HTML",
        )
        return

    if is_registered(message.from_user.id):
        nick = user_profiles[message.from_user.id]['nickname']
        op = user_profiles[message.from_user.id]['op']
        await message.answer(
            f"👋 <b>С возвращением, {nick}!</b>\n"
            "─────────────\n\n"
            f"📝 Кличка: <b>{nick}</b>\n"
            f"💬 ОП: <b>{op}</b>\n\n"
            "─────────────\n"
            "🛠 <b>Что ты можешь:</b>\n\n"
            "📢 <b>Отправить пост</b> — просто напиши сообщение\n"
            "   <i>Оно уйдёт на модерацию админу</i>\n\n"
            "🔍 <b>/search</b> — объявление о поиске человека\n\n"
            "👤 <b>/profile</b> — изменить кличку или ОП\n\n"
            "─────────────\n"
            "💡 Публикуй анонимно — никто не узнает, кто ты",
            parse_mode="HTML",
        )
        return

    await state.set_state(RegState.waiting_nickname)
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n"
        "─────────────\n\n"
        "Это бот анонимных публикаций канала\n"
        "<b>«Подслушано Никулина»</b> 🤫\n\n"
        "─────────────\n"
        "🎭 <b>Что нужно для старта?</b>\n\n"
        "Придумай себе:\n\n"
        "1️⃣ <b>Кличку</b> — под ней будут выходить посты\n"
        "2️⃣ <b>ОП</b> — число от 1 до 4\n\n"
        "─────────────\n"
        "📝 <b>Шаг 1/2:</b> введи свою кличку\n\n"
        "<i>Например: Тень, Аноним, Ночной гость</i>",
        parse_mode="HTML",
    )


@dp.message(RegState.waiting_nickname)
async def reg_nickname(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 32:
        await message.answer("Кличка должна быть текстом до 32 символов. Попробуй ещё раз:")
        return
    await state.update_data(nickname=message.text.strip())
    await state.set_state(RegState.waiting_op)
    await message.answer("Шаг 2/2: введи свой ОП — число от 1 до 4:")


@dp.message(RegState.waiting_op)
async def reg_op(message: types.Message, state: FSMContext):
    if not message.text or not valid_op(message.text):
        await message.answer("ОП должен быть числом от 1 до 4. Попробуй ещё раз:")
        return

    data = await state.get_data()
    user_profiles[message.from_user.id] = {
        "nickname": data["nickname"],
        "op": message.text.strip(),
    }
    await state.clear()
    await message.answer(
        f"✅ <b>Готово!</b>\n\n"
        f"📝 Кличка: <b>{user_profiles[message.from_user.id]['nickname']}</b>\n"
        f"💬 ОП: <b>{user_profiles[message.from_user.id]['op']}</b>\n\n"
        "─────────────\n"
        "Теперь можешь:\n\n"
        "📢 Отправить сообщение — уйдёт на модерацию\n"
        "🔍 /search — объявление о поиске человека\n"
        "👤 /profile — изменить профиль",
        parse_mode="HTML",
    )


@dp.message(Command("profile"))
async def cmd_profile(message: types.Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await message.answer("У админа нет профиля.")
        return
    if not is_registered(message.from_user.id):
        await message.answer("Ты ещё не зарегистрирован. Напиши /start")
        return

    p = user_profiles[message.from_user.id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить кличку", callback_data="edit:nick")],
        [InlineKeyboardButton(text="✏️ Изменить ОП", callback_data="edit:op")],
    ])
    await message.answer(
        f"👤 <b>Твой профиль</b>\n"
        "─────────────\n"
        f"📝 Кличка: <b>{p['nickname']}</b>\n"
        f"💬 ОП: <b>{p['op']}</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )


@dp.callback_query(F.data.startswith("edit:"))
async def edit_profile(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":")[1]
    if field == "nick":
        await state.set_state(RegState.waiting_nickname)
        await callback.message.answer("Введи новую кличку:")
    else:
        await state.set_state(RegState.waiting_op)
        await callback.message.answer("Введи новый ОП — число от 1 до 4:")
    await callback.answer()


@dp.message(Command("search"))
async def cmd_search(message: types.Message, state: FSMContext):
    if is_admin(message.from_user.id):
        await message.answer("Админ и так видит заявки.")
        return
    if not is_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйся: /start")
        return

    await state.set_state(SearchState.waiting_name)
    await message.answer(
        "🔍 <b>Создание объявления о поиске человека</b>\n\n"
        "<b>Шаг 1/5:</b> Имя или кого ищем\n"
        "<i>Например: Иван, девушка со стоянки, парень в кепке</i>",
        parse_mode="HTML",
    )


@dp.message(SearchState.waiting_name)
async def search_name(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 100:
        await message.answer("Напиши текстом до 100 символов:")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(SearchState.waiting_situation)
    await message.answer("<b>Шаг 2/5:</b> Опиши ситуацию (что случилось, где, когда):", parse_mode="HTML")


@dp.message(SearchState.waiting_situation)
async def search_situation(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 1000:
        await message.answer("Опиши текстом до 1000 символов:")
        return
    await state.update_data(situation=message.text.strip())
    await state.set_state(SearchState.waiting_clothes)
    await message.answer("<b>Шаг 3/5:</b> Во что был(а) одет(а)? (цвет, вещи, приметы):", parse_mode="HTML")


@dp.message(SearchState.waiting_clothes)
async def search_clothes(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 500:
        await message.answer("Опиши текстом до 500 символов:")
        return
    await state.update_data(clothes=message.text.strip())
    await state.set_state(SearchState.waiting_location)
    await message.answer("<b>Шаг 4/5:</b> Где видели в последний раз? (район, адрес, метро):", parse_mode="HTML")


@dp.message(SearchState.waiting_location)
async def search_location(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 300:
        await message.answer("Опиши текстом до 300 символов:")
        return
    await state.update_data(location=message.text.strip())
    await state.set_state(SearchState.waiting_photo)
    await message.answer("<b>Шаг 5/5:</b> Пришли фото (если есть) или напиши «нет»:", parse_mode="HTML")


@dp.message(SearchState.waiting_photo, F.photo)
async def search_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await finalize_search(message, state)


@dp.message(SearchState.waiting_photo)
async def search_photo_skip(message: types.Message, state: FSMContext):
    if message.text and message.text.strip().lower() in ("нет", "no", "-"):
        await state.update_data(photo=None)
        await finalize_search(message, state)
    else:
        await message.answer("Пришли фото или напиши «нет»:")


async def finalize_search(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    profile = user_profiles.get(message.from_user.id, {"nickname": "Аноним", "op": "?"})
    user_id = message.from_user.id

    text = (
        f"🔍 ПОИСК ЧЕЛОВЕКА\n"
        f"─────────────\n"
        f"👤 Кого ищем: {data['name']}\n\n"
        f"📖 Ситуация:\n{data['situation']}\n\n"
        f"👕 Одет(а):\n{data['clothes']}\n\n"
        f"📍 Где видели:\n{data['location']}\n"
        f"─────────────\n"
        f"📝 От: {profile['nickname']} | ОП: {profile['op']}\n"
        f"🆔 ID: {user_id}"
    )

    await bot.send_message(chat_id=ADMIN_ID, text="☝️ Новая заявка на поиск человека:")

    if data.get("photo"):
        sent = await bot.send_photo(chat_id=ADMIN_ID, photo=data["photo"], caption=text)
    else:
        sent = await bot.send_message(chat_id=ADMIN_ID, text=text)

    drafts[sent.message_id] = {
        "type": "search",
        "data": data,
        "author": profile,
        "user_id": user_id,
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish:{sent.message_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cancel:{sent.message_id}"),
        ]
    ])
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="Публикуем объявление?",
        reply_to_message_id=sent.message_id,
        reply_markup=kb,
    )

    await message.answer("✅ Заявка отправлена на модерацию.")


@dp.message(F.chat.type == "private", ~F.text.startswith("/"))
async def handle_post(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if current is not None:
        return

    user_id = message.from_user.id

    if is_admin(user_id):
        preview = await message.copy_to(chat_id=message.chat.id)
        drafts[preview.message_id] = {"type": "plain", "message": message, "author": None}
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish:{preview.message_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel:{preview.message_id}"),
            ]
        ])
        await bot.send_message(
            chat_id=message.chat.id,
            text="📝 Предпросмотр выше (от админа). Опубликовать?",
            reply_to_message_id=preview.message_id,
            reply_markup=kb,
        )
        return

    if not is_registered(user_id):
        await message.answer("Сначала зарегистрируйся: /start")
        return

    profile = user_profiles[user_id]
    author_block = (
        f"📝 Пост от: {profile['nickname']}\n"
        f"💬 ОП: {profile['op']}\n"
        f"🆔 ID: {user_id}"
    )

    await bot.send_message(chat_id=ADMIN_ID, text=author_block)
    forwarded = await message.forward(chat_id=ADMIN_ID)

    drafts[forwarded.message_id] = {
        "type": "plain",
        "message": message,
        "author": profile,
        "user_id": user_id,
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish:{forwarded.message_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"cancel:{forwarded.message_id}"),
        ]
    ])
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="☝️ Пост на модерацию. Публикуем?",
        reply_to_message_id=forwarded.message_id,
        reply_markup=kb,
    )

    await message.answer("✅ Отправлено на модерацию.")


@dp.callback_query(F.data.startswith("publish:"))
async def publish_post(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    preview_id = int(callback.data.split(":")[1])
    draft = drafts.get(preview_id)

    if not draft:
        await callback.answer("⚠️ Черновик не найден", show_alert=True)
        return

    try:
        if draft.get("type") == "search":
            d = draft["data"]
            author = draft["author"]

            text = (
                f"🔍 ПОИСК ЧЕЛОВЕКА\n"
                f"─────────────\n"
                f"👤 Кого ищем: {d['name']}\n\n"
                f"📖 Ситуация:\n{d['situation']}\n\n"
                f"👕 Одет(а):\n{d['clothes']}\n\n"
                f"📍 Где видели:\n{d['location']}\n"
                f"─────────────\n"
                f"📝 {author['nickname']} | 💬 ОП: {author['op']}"
            )

            if d.get("photo"):
                await bot.send_photo(chat_id=CHANNEL_ID, photo=d["photo"], caption=text)
            else:
                await bot.send_message(chat_id=CHANNEL_ID, text=text)

        else:
            original: types.Message = draft["message"]
            author = draft.get("author")

            if author:
                footer = (
                    f"\n\n─────────────\n"
                    f"📝 {author['nickname']} | 💬 ОП: {author['op']}"
                )
            else:
                footer = ""

            if original.text:
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=original.text + footer,
                )
            elif original.caption is not None:
                await original.copy_to(
                    chat_id=CHANNEL_ID,
                    caption=original.caption + footer,
                )
            elif original.photo:
                await original.copy_to(
                    chat_id=CHANNEL_ID,
                    caption=footer.strip() if footer else None,
                )
            else:
                await original.copy_to(chat_id=CHANNEL_ID)
                if footer:
                    await bot.send_message(chat_id=CHANNEL_ID, text=footer.strip())

        drafts.pop(preview_id, None)
        await callback.message.edit_text("✅ Опубликовано в канале!")
        await callback.answer("Опубликовано!")

        if draft.get("user_id"):
            try:
                await bot.send_message(chat_id=draft["user_id"], text="✅ Твой пост опубликован в канале!")
            except Exception:
                pass

    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)


@dp.callback_query(F.data.startswith("cancel:"))
async def cancel_post(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    preview_id = int(callback.data.split(":")[1])
    draft = drafts.pop(preview_id, None)

    await callback.message.edit_text("❌ Публикация отклонена.")
    await callback.answer("Отклонено")

    if draft and draft.get("user_id"):
        try:
            await bot.send_message(chat_id=draft["user_id"], text="❌ Твой пост отклонён модератором.")
        except Exception:
            pass


async def main():
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
