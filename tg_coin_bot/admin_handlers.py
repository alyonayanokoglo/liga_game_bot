from collections.abc import Awaitable, Callable
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

RESET_ADMIN_PANEL = "🔄 Сброс админ-панели"
MANUAL_ACCRUAL = "✍️ Ручное начисление"

IsAdmin = Callable[[int], bool]
GetUserByBadgeId = Callable[[str], Awaitable[Optional[dict]]]
GetActivitiesForAdmin = Callable[[], Awaitable[list[dict]]]
AddPoints = Callable[[int, int, int], Awaitable[tuple[bool, str, Optional[dict]]]]
ManualAddPoints = Callable[[int, int, int], Awaitable[tuple[bool, str, Optional[dict]]]]
DeductKarma = Callable[[int, int, int], Awaitable[tuple[bool, str, Optional[dict]]]]


class AdminAccrual(StatesGroup):
    waiting_for_badge_id = State()


class AdminDebit(StatesGroup):
    waiting_for_badge_id = State()
    waiting_for_amount = State()


class AdminManualAccrual(StatesGroup):
    waiting_for_badge_id = State()
    waiting_for_amount = State()


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Начислить карму")],
            [KeyboardButton(text="➖ Списать карму")],
            [KeyboardButton(text=MANUAL_ACCRUAL)],
            [KeyboardButton(text=RESET_ADMIN_PANEL)],
        ],
        resize_keyboard=True,
    )


def activities_keyboard(activities: list[dict], user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for activity in activities:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{activity['title']} · +{activity['points']}",
                    callback_data=f"accrue:{user_id}:{activity['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def register_admin_handlers(
    dp: Dispatcher,
    bot: Bot,
    is_admin: IsAdmin,
    get_user_by_badge_id: GetUserByBadgeId,
    get_activities_for_admin: GetActivitiesForAdmin,
    add_points: AddPoints,
    manual_add_points: ManualAddPoints,
    deduct_karma: DeductKarma,
) -> None:
    @dp.message(Command("admin"))
    async def admin(message: Message) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer(
                "У тебя нет доступа к админ-меню.\n\n"
                f"Твой Telegram ID: {from_user.id}"
            )
            return

        await message.answer(
            "Админ-меню.",
            reply_markup=admin_menu(),
        )

    # Раньше хендлеров по состоянию: выход из сценария начисления/списания без смены на меню игрока.
    @dp.message(F.text == RESET_ADMIN_PANEL)
    async def admin_panel_reset(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            return

        await state.clear()
        await message.answer(
            "Сброс: прерван сценарий (ввод ID / суммы). Админ-панель та же — кнопки ниже.",
            reply_markup=admin_menu(),
        )

    @dp.message(F.text == "➕ Начислить карму")
    async def admin_add_points_start(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            return

        await state.set_state(AdminAccrual.waiting_for_badge_id)
        await message.answer("Введи ID участника с браслета (только цифры).")

    @dp.message(F.text == "➖ Списать карму")
    async def admin_debit_start(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            return

        await state.set_state(AdminDebit.waiting_for_badge_id)
        await message.answer(
            "Списание кармы (например, покупка в магазине мерча).\n\n"
            "Введи ID участника с браслета (только цифры)."
        )

    @dp.message(F.text == MANUAL_ACCRUAL)
    async def admin_manual_accrual_start(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            return

        await state.set_state(AdminManualAccrual.waiting_for_badge_id)
        await message.answer(
            "Ручное начисление кармы.\n\n"
            "Введи ID участника с браслета (только цифры)."
        )

    @dp.message(AdminManualAccrual.waiting_for_badge_id)
    async def admin_manual_accrual_badge_id(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            await state.clear()
            return

        text = message.text
        if text is None:
            await message.answer("Введи ID текстом.")
            return
        badge_id = text.strip()
        user = await get_user_by_badge_id(badge_id)

        if not user:
            await message.answer(
                "Участник с таким ID не найден.\n\n"
                "Проверь ID и введи ещё раз."
            )
            return

        await state.update_data(manual_user_id=user["id"])
        await state.set_state(AdminManualAccrual.waiting_for_amount)
        await message.answer(
            "Участник найден:\n\n"
            f"Имя: {user['name']}\n"
            f"ID браслета: {user['badge_id']}\n"
            f"Текущий баланс: {user['balance']} баллов кармы\n\n"
            "Сколько баллов начислить? (целое число, например: 50)"
        )

    @dp.message(AdminManualAccrual.waiting_for_amount)
    async def admin_manual_accrual_amount(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            await state.clear()
            return

        text = (message.text or "").strip()
        if not text.isdigit():
            await message.answer("Нужно целое число баллов, например: 50")
            return

        points = int(text)
        data = await state.get_data()
        user_id = data.get("manual_user_id")
        if not isinstance(user_id, int):
            await state.clear()
            await message.answer("Сессия устарела. Нажми «Ручное начисление» снова.")
            return

        ok, msg, result = await manual_add_points(user_id, points, from_user.id)

        await state.clear()

        if not ok or result is None:
            await message.answer(f"⚠️ {msg}", reply_markup=admin_menu())
            return

        user = result["user"]
        added = result["points"]

        await message.answer(
            "✅ Карма начислена.\n\n"
            f"Участник: {user['name']}\n"
            f"ID браслета: {user['badge_id']}\n"
            f"Начислено: {added}\n"
            f"Новый баланс: {user['balance']}",
            reply_markup=admin_menu(),
        )

        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=(
                    f"Тебе начислено {added} баллов кармы (ручное начисление админом).\n\n"
                    f"Текущий баланс: {user['balance']}."
                ),
            )
        except Exception:
            await message.answer(
                "Карма начислена, но не получилось отправить уведомление участнику."
            )

    @dp.message(AdminDebit.waiting_for_badge_id)
    async def admin_debit_badge_id(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            await state.clear()
            return

        text = message.text
        if text is None:
            await message.answer("Введи ID текстом.")
            return
        badge_id = text.strip()
        user = await get_user_by_badge_id(badge_id)

        if not user:
            await message.answer(
                "Участник с таким ID не найден.\n\n"
                "Проверь ID и введи ещё раз."
            )
            return

        await state.update_data(debit_user_id=user["id"])
        await state.set_state(AdminDebit.waiting_for_amount)
        await message.answer(
            "Участник найден:\n\n"
            f"Имя: {user['name']}\n"
            f"ID браслета: {user['badge_id']}\n"
            f"Текущий баланс: {user['balance']} баллов кармы\n\n"
            "Сколько баллов списать? (целое число, например: 50)"
        )

    @dp.message(AdminDebit.waiting_for_amount)
    async def admin_debit_amount(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            await state.clear()
            return

        text = (message.text or "").strip()
        if not text.isdigit():
            await message.answer("Нужно целое число баллов, например: 50")
            return

        points = int(text)
        data = await state.get_data()
        user_id = data.get("debit_user_id")
        if not isinstance(user_id, int):
            await state.clear()
            await message.answer("Сессия устарела. Нажми «➖ Списать карму» снова.")
            return

        ok, msg, result = await deduct_karma(user_id, points, from_user.id)

        await state.clear()

        if not ok or result is None:
            await message.answer(f"⚠️ {msg}", reply_markup=admin_menu())
            return

        user = result["user"]
        spent = result["points"]

        await message.answer(
            "✅ Карма списана.\n\n"
            f"Участник: {user['name']}\n"
            f"ID браслета: {user['badge_id']}\n"
            f"Списано: {spent}\n"
            f"Новый баланс: {user['balance']}",
            reply_markup=admin_menu(),
        )

        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=(
                    f"С твоего баланса списано {spent} баллов кармы "
                    f"(оформление в магазине мерча).\n\n"
                    f"Текущий баланс: {user['balance']}."
                ),
            )
        except Exception:
            await message.answer(
                "Списание выполнено, но не получилось отправить уведомление участнику."
            )

    @dp.message(AdminAccrual.waiting_for_badge_id)
    async def admin_add_points_badge_id(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return

        if not is_admin(from_user.id):
            await message.answer("У тебя нет доступа к этой команде.")
            await state.clear()
            return

        text = message.text
        if text is None:
            await message.answer("Введи ID текстом.")
            return
        badge_id = text.strip()
        user = await get_user_by_badge_id(badge_id)

        if not user:
            await message.answer(
                "Участник с таким ID не найден.\n\n"
                "Проверь ID и введи ещё раз."
            )
            return

        activities = await get_activities_for_admin()
        await state.clear()

        if not activities:
            await message.answer(
                "Участник найден, но сейчас нет активностей, которые можно начислить "
                "через админку.",
                reply_markup=admin_menu(),
            )
            return

        await message.answer(
            "Участник найден:\n\n"
            f"Имя: {user['name']}\n"
            f"ID браслета: {user['badge_id']}\n"
            f"Баланс: {user['balance']} баллов кармы\n\n"
            "Выбери активность для начисления.\n\n"
            "Если лекцию не удалось засчитать промокодом — «<b>Лекция (админ)</b>»: "
            "400 баллов, не больше <b>четырёх</b> начислений одному человеку; "
            "это отдельно от лекций с промокодом.\n\n"
            "Выбери кнопку ниже:",
            reply_markup=activities_keyboard(activities, user["id"]),
            parse_mode="HTML",
        )

    @dp.callback_query(F.data.startswith("accrue:"))
    async def accrue_callback(callback: CallbackQuery) -> None:
        cb_message = callback.message
        if not isinstance(cb_message, Message):
            await callback.answer("Сообщение недоступно.", show_alert=True)
            return

        payload = callback.data
        if payload is None:
            await callback.answer("Некорректные данные кнопки.", show_alert=True)
            return

        admin_user = callback.from_user
        if admin_user is None or not is_admin(admin_user.id):
            await callback.answer("Нет доступа", show_alert=True)
            return

        _, user_id_raw, activity_id_raw = payload.split(":")
        user_id = int(user_id_raw)
        activity_id = int(activity_id_raw)

        success, message_text, result = await add_points(user_id, activity_id, admin_user.id)

        if not success:
            await cb_message.answer(f"⚠️ {message_text}")
            await callback.answer()
            return

        if result is None:
            await cb_message.answer("Внутренняя ошибка при начислении.")
            await callback.answer()
            return

        user = result["user"]
        activity = result["activity"]
        points = result["points"]

        await cb_message.answer(
            "✅ Карма начислена.\n\n"
            f"Участник: {user['name']}\n"
            f"ID браслета: {user['badge_id']}\n"
            f"Активность: {activity['title']}\n"
            f"Начислено: {points}\n"
            f"Новый баланс: {user['balance']}"
        )

        try:
            await bot.send_message(
                chat_id=user["telegram_id"],
                text=(
                    f"Тебе начислено {points} баллов кармы "
                    f"за «{activity['title']}».\n\n"
                    f"Текущий баланс: {user['balance']}."
                ),
            )
        except Exception:
            await cb_message.answer(
                "Карма начислена, но не получилось отправить уведомление участнику."
            )

        await callback.answer()
