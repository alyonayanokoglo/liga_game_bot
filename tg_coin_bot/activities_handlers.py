from collections.abc import Awaitable, Callable
import os
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)

GetUserByTelegramId = Callable[[int], Awaitable[Optional[dict]]]
GrantActivityOnce = Callable[
    [int, str, Optional[int]],
    Awaitable[tuple[bool, str, Optional[dict]]],
]
MainReplyMenu = Callable[[], ReplyKeyboardMarkup]


class LectureCode(StatesGroup):
    waiting_for_code = State()

TG_CHANNEL_FUTURE_SLUG = "tg_channel_future"
SOVKOMBANK_FUTURE_CHANNEL = os.getenv("SOVKOMBANK_FUTURE_CHANNEL", "@sovcomstudents")
SOVKOMBANK_FUTURE_URL = os.getenv("SOVKOMBANK_FUTURE_URL", "https://t.me/sovcomstudents")

VK_COMMUNITY_SLUG = "vk_community"
SOVKOM_VK_URL = os.getenv("SOVKOM_VK_URL", "https://vk.com/sovcombankfuture")


LECTURES: dict[str, tuple[str, str]] = {
    "lecture_1": ("Лекция 1", "коллеги"),
    "lecture_2": ("Лекция 2", "капучинка"),
    "lecture_3": ("Лекция 3", "вайбик"),
}

ACTIVITIES_TEXT: dict[str, tuple[str, str, str]] = {
    "hr_date": (
        "Кнопка 1-1 c рекрутером",
        "1-1 c рекрутером",
        "Экспресс-собеседование, на котором ты наметишь свой уникальный карьерный "
        "трек. Участие по предварительной записи! Проверь свободные слоты и не "
        "пропусти свое время.\n\n"
        "🔵 За эту активность ты получишь 100 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "it_jenga": (
        "Кнопка ИТ‑Дженга",
        "ИТ‑Дженга",
        "Аккуратно вытащи брусок и узнай, кто ты сегодня — разработчик, "
        "тестировщик или аналитик. А может ты вытянешь бонус?\n\n"
        "🔵 Реши рабочую задачу до дедлайна и получи 200 баллов кармы\n\n"
        "Начисление — один раз.",
    ),
    "it_memo": (
        "ИТ‑МЕМО",
        "ИТ‑МЕМО",
        "Прояви чутьё программиста и найди пару для логотипа. Это может быть "
        "название программы, язык или инструмент программирования. Для победы "
        "собери 1 пару идентичных слотов.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "script_master": (
        "Кнопка Скрипт-мастер",
        "Скрипт-мастер",
        "Работа в продажах напоминает словесный тетрис. Знать скрипты мало, "
        "нужно применять их в правильной последовательности. Расположи фразы "
        "так, чтобы защитить клиента, банк и себя.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "explainer": (
        "Кнопка Объяснительная",
        "Объяснительная",
        "Единственная объяснительная в Совкомбанке. Найди слово по вертикали / "
        "горизонтали / диагонали и вычеркни. Нашел? А теперь пора объяснить его "
        "значение друллеге.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "fin_assets": (
        "Кнопка Финансовые активы",
        "Финансовые активы",
        "Примерь на себя роль финансового консультанта. Клиент накопил груду "
        "активов, помоги ему грамотно их распределить. Для тебя это проще "
        "простого, разбери активы по категориям.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "fin_fate": (
        "Кнопка Финансы судьбы",
        "Финансы судьбы",
        "Здесь ты научишься управлять финансами, опираясь на внешние факторы. "
        "Кидай кубик и закрывай потребности, опираясь на своё чутьё. Побеждает "
        "первый, закрывший все слоты.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "tg_channel_future": (
        "Кнопка Подписка на TG‑канал",
        "Подписка на Telegram‑канал",
        "Подпишись на Telegram‑канал «Совкомбанк Будущее».\n\n"
        "🔵 Здесь можно заработать 100 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "vk_community": (
        "Кнопка Подписка на VK",
        "Подписка на VK‑сообщество",
        "Подпишись на VK‑сообщество Совкомбанка.\n\n"
        "🔵 Здесь можно заработать 100 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "lecture_1": (
        "Кнопка Лекторий",
        "Лекторий",
        "Слышал про постоянные созвоны и встречи с коллегами? У нас они проходят "
        "в пространстве для дискуссий. Посети экспертные лекции и выскажи свое "
        "мнение в жарких обсуждениях.\n\n"
        "🔵 За активность здесь ты получишь 400 баллов кармы.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "lecture_2": (
        "Кнопка Лекторий",
        "Лекторий",
        "Слышал про постоянные созвоны и встречи с коллегами? У нас они проходят "
        "в пространстве для дискуссий. Посети экспертные лекции и выскажи свое "
        "мнение в жарких обсуждениях.\n\n"
        "🔵 За активность здесь ты получишь 400 баллов кармы.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
    "lecture_3": (
        "Кнопка Лекторий",
        "Лекторий",
        "Слышал про постоянные созвоны и встречи с коллегами? У нас они проходят "
        "в пространстве для дискуссий. Посети экспертные лекции и выскажи свое "
        "мнение в жарких обсуждениях.\n\n"
        "🔵 За активность здесь ты получишь 400 баллов кармы.\n\n"
        "🔵 Здесь можно заработать 200 баллов кармы.\n\n"
        "Начисление — один раз.",
    ),
}


def activity_nav_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Меню", callback_data="nav:menu"),
                InlineKeyboardButton(
                    text="Все активности", callback_data="nav:all_act"
                ),
            ]
        ]
    )


def all_activities_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, slug in enumerate(ACTIVITIES_TEXT.keys()):
        label = ACTIVITIES_TEXT[slug][0]
        row.append(InlineKeyboardButton(text=label, callback_data=f"act:{slug}"))
        if len(row) == 2 or i == len(ACTIVITIES_TEXT) - 1:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Меню", callback_data="nav:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def register_activities_handlers(
    dp: Dispatcher,
    bot: Bot,
    main_reply_menu: MainReplyMenu,
    get_user_by_telegram_id: GetUserByTelegramId,
    grant_activity_once: GrantActivityOnce,
) -> None:
    @dp.callback_query(F.data.startswith("nav:"))
    async def nav_callbacks(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if not isinstance(cb_msg, Message):
            await callback.answer()
            return
        if callback.data == "nav:menu":
            await state.clear()
            await cb_msg.answer(
                "Главное меню.",
                reply_markup=main_reply_menu(),
            )
        elif callback.data == "nav:all_act":
            await cb_msg.answer(
                "Выбери активность:",
                reply_markup=all_activities_keyboard(),
            )
        await callback.answer()

    @dp.callback_query(F.data.startswith("act:"))
    async def activity_detail(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if not isinstance(cb_msg, Message) or callback.data is None:
            await callback.answer()
            return
        slug = callback.data.split(":", 1)[1]
        if slug not in ACTIVITIES_TEXT:
            await callback.answer("Неизвестная активность.", show_alert=True)
            return
        _btn, title, body = ACTIVITIES_TEXT[slug]

        extra_rows: list[list[InlineKeyboardButton]] = []
        if slug == TG_CHANNEL_FUTURE_SLUG:
            extra_rows.append(
                [
                    InlineKeyboardButton(
                        text="Открыть канал",
                        url=SOVKOMBANK_FUTURE_URL,
                    ),
                    InlineKeyboardButton(
                        text="Проверить подписку",
                        callback_data=f"tgsub:check:{slug}",
                    ),
                ]
            )
        if slug == VK_COMMUNITY_SLUG:
            extra_rows.append(
                [
                    InlineKeyboardButton(
                        text="Открыть VK",
                        url=SOVKOM_VK_URL,
                    ),
                    InlineKeyboardButton(
                        text="Забрать баллы",
                        callback_data=f"vksub:claim:{slug}",
                    ),
                ]
            )
        if slug in LECTURES:
            extra_rows.append(
                [
                    InlineKeyboardButton(
                        text="Ввести кодовое слово",
                        callback_data=f"lecture:enter:{slug}",
                    )
                ]
            )
        kb = InlineKeyboardMarkup(
            inline_keyboard=extra_rows + activity_nav_keyboard().inline_keyboard
        )
        await cb_msg.answer(
            f"<b>{title}</b>\n\n{body}",
            parse_mode="HTML",
            reply_markup=kb,
        )
        await callback.answer()

    @dp.callback_query(F.data.startswith("tgsub:check:"))
    async def tgsub_check(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if callback.from_user is None or not isinstance(cb_msg, Message) or callback.data is None:
            await callback.answer()
            return

        slug = callback.data.split(":", 2)[2]
        if slug != TG_CHANNEL_FUTURE_SLUG or slug not in ACTIVITIES_TEXT:
            await callback.answer("Неизвестная активность.", show_alert=True)
            return

        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Сначала /start", show_alert=True)
            return

        try:
            member = await bot.get_chat_member(
                chat_id=SOVKOMBANK_FUTURE_CHANNEL,
                user_id=callback.from_user.id,
            )
            status = getattr(member, "status", None)
        except Exception:
            await callback.answer(
                "Не получилось проверить подписку. Убедись, что бот добавлен в канал админом.",
                show_alert=True,
            )
            return

        if status not in {"member", "administrator", "creator"}:
            await callback.answer("Похоже, ты ещё не подписан. Подпишись и нажми «Проверить подписку».", show_alert=True)
            return

        _btn, title, _body = ACTIVITIES_TEXT[slug]
        ok, _msg, result = await grant_activity_once(user["id"], title, None)
        if ok and result:
            u = result["user"]
            await cb_msg.answer(
                f"Подписка подтверждена! +{result['points']} баллов кармы.\n\nБаланс: {u['balance']}.",
                reply_markup=main_reply_menu(),
            )
        else:
            await cb_msg.answer(
                "Подписка подтверждена, но баллы за эту активность уже начислялись ранее.",
                reply_markup=main_reply_menu(),
            )
        await callback.answer()

    @dp.callback_query(F.data.startswith("vksub:claim:"))
    async def vksub_claim(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if callback.from_user is None or not isinstance(cb_msg, Message) or callback.data is None:
            await callback.answer()
            return

        slug = callback.data.split(":", 2)[2]
        if slug != VK_COMMUNITY_SLUG or slug not in ACTIVITIES_TEXT:
            await callback.answer("Неизвестная активность.", show_alert=True)
            return

        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Сначала /start", show_alert=True)
            return

        _btn, title, _body = ACTIVITIES_TEXT[slug]
        ok, _msg, result = await grant_activity_once(user["id"], title, None)
        if ok and result:
            u = result["user"]
            await cb_msg.answer(
                f"Готово! +{result['points']} баллов кармы.\n\nБаланс: {u['balance']}.",
                reply_markup=main_reply_menu(),
            )
        else:
            await cb_msg.answer(
                "Похоже, баллы за эту активность уже начислялись ранее.",
                reply_markup=main_reply_menu(),
            )
        await callback.answer()

    @dp.callback_query(F.data.startswith("lecture:enter:"))
    async def lecture_enter(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if not isinstance(cb_msg, Message) or callback.data is None:
            await callback.answer()
            return
        if callback.from_user is None:
            await callback.answer()
            return
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Сначала /start", show_alert=True)
            return

        slug = callback.data.split(":", 2)[2]
        if slug not in LECTURES:
            await callback.answer("Неизвестная лекция.", show_alert=True)
            return
        title, _code = LECTURES[slug]
        await state.set_state(LectureCode.waiting_for_code)
        await state.update_data(lecture_slug=slug)

        await cb_msg.answer(
            f"<b>{title}</b>\n\nВведи кодовое слово одним сообщением.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Меню", callback_data="nav:menu")]]
            ),
        )
        await callback.answer()

    @dp.message(LectureCode.waiting_for_code)
    async def lecture_code_message(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            await message.answer("Сначала нажми /start и зарегистрируйся.")
            await state.clear()
            return

        text = (message.text or "").strip()
        data = await state.get_data()
        slug = data.get("lecture_slug")
        if not isinstance(slug, str) or slug not in LECTURES:
            await message.answer("Не получилось определить лекцию. Попробуй ещё раз из списка активностей.")
            await state.clear()
            return
        title, expected = LECTURES[slug]

        if text.casefold() != expected.casefold():
            await message.answer(
                "Кодовое слово не подходит. Проверь написание и попробуй ещё раз.\n\n"
                "Если передумал — нажми «Меню».",
                reply_markup=main_reply_menu(),
            )
            return

        ok, _msg, result = await grant_activity_once(user["id"], title, None)
        await state.clear()

        if ok and result:
            u = result["user"]
            await message.answer(
                f"Код принят! +{result['points']} баллов кармы.\n\nБаланс: {u['balance']}.",
                reply_markup=main_reply_menu(),
            )
        else:
            await message.answer(
                "Похоже, баллы за эту лекцию уже начислялись ранее.",
                reply_markup=main_reply_menu(),
            )

    @dp.message(F.text == "Где взять карму")
    async def where_karma(message: Message) -> None:
        from_user = message.from_user
        if from_user is None:
            return
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            await message.answer("Сначала нажми /start и зарегистрируйся.")
            return

        await message.answer(
            "Участвуй в интерактивах и пробуй себя в разных профессиях. "
            "Не забывай говорить свой ID друллегам из Совкомбанка, "
            "чтобы получить карму. Я всё посчитаю за тебя.\n\n"
            "Ещё ты можешь заработать карму прямо в этом чате.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Узнать о всех активностях",
                            callback_data="nav:all_act",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Пройти «Квиз о банке»",
                            callback_data="quiz:intro",
                        )
                    ],
                    [InlineKeyboardButton(text="Меню", callback_data="nav:menu")],
                ]
            ),
        )

    @dp.message(F.text == "Все активности")
    async def all_activities_reply(message: Message) -> None:
        from_user = message.from_user
        if from_user is None:
            return
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            await message.answer("Сначала нажми /start и зарегистрируйся.")
            return
        await message.answer(
            "Выбери активность:",
            reply_markup=all_activities_keyboard(),
        )
