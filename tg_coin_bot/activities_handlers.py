from collections.abc import Awaitable, Callable
import os
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
)
from client_nav import (
    CLIENT_NAV_KARMA,
)

_BASE_DIR = Path(__file__).resolve().parent
LECTURE_PHOTOS: dict[str, Path] = {
    "lecture_1": _BASE_DIR / "img" / "Лекция 1.jpg",
    "lecture_2": _BASE_DIR / "img" / "Лекция 2.jpg",
    "lecture_3": _BASE_DIR / "img" / "Лекция 3.jpg",
}

GetUserByTelegramId = Callable[[int], Awaitable[Optional[dict]]]
GrantActivityOnce = Callable[
    [int, str, Optional[int]],
    Awaitable[tuple[bool, str, Optional[dict]]],
]
MainNavMarkup = Callable[[], ReplyKeyboardMarkup]


class LectureCode(StatesGroup):
    waiting_for_code = State()

TG_CHANNEL_FUTURE_SLUG = "tg_channel_future"
SOVKOMBANK_FUTURE_CHANNEL = os.getenv("SOVKOMBANK_FUTURE_CHANNEL", "@sovcomstudents")
SOVKOMBANK_FUTURE_URL = os.getenv("SOVKOMBANK_FUTURE_URL", "https://t.me/sovcomstudents")
TG_CHANNEL_COVER_PHOTO = _BASE_DIR / "img" / "tg.jpg"
# Должно совпадать с первым полем кортежа в _activities_seed_rows() в main.py (таблица activities.title).
TG_CHANNEL_ACTIVITY_DB_TITLE = "Подписка на Telegram\u2011канал"

# Кастомный эмодзи «1️⃣» из набора (web: data-doc-id → Bot API custom_emoji / emoji-id).
LECTURE_1_CUSTOM_EMOJI_ID = "5413754548021916229"
LECTURE_1_TITLE_HTML = (
    f'Лекция <tg-emoji emoji-id="{LECTURE_1_CUSTOM_EMOJI_ID}">1️⃣</tg-emoji>'
)

LECTURE_2_CUSTOM_EMOJI_ID = "5413777285578781104"
LECTURE_2_TITLE_HTML = (
    f'Лекция <tg-emoji emoji-id="{LECTURE_2_CUSTOM_EMOJI_ID}">2️⃣</tg-emoji>'
)

LECTURE_3_CUSTOM_EMOJI_ID = "5413736616533456861"
LECTURE_3_TITLE_HTML = (
    f'Лекция <tg-emoji emoji-id="{LECTURE_3_CUSTOM_EMOJI_ID}">3️⃣</tg-emoji>'
)

LECTURE_TITLE_HTML_BY_SLUG: dict[str, str] = {
    "lecture_1": LECTURE_1_TITLE_HTML,
    "lecture_2": LECTURE_2_TITLE_HTML,
    "lecture_3": LECTURE_3_TITLE_HTML,
}

# Маркер блока про баллы кармы (кастомный кружок; fallback — 🔵).
KARMA_POINTS_BADGE_CUSTOM_EMOJI_ID = "5413658366524292163"
KARMA_POINTS_BADGE_HTML = (
    f'<tg-emoji emoji-id="{KARMA_POINTS_BADGE_CUSTOM_EMOJI_ID}">☺️</tg-emoji>'
)

# Стрелка вниз в конце подсказки про карму в чате.
KARMA_CHAT_HINT_ARROW_CUSTOM_EMOJI_ID = "5413434006022681382"
KARMA_CHAT_HINT_ARROW_HTML = (
    f'<tg-emoji emoji-id="{KARMA_CHAT_HINT_ARROW_CUSTOM_EMOJI_ID}">⤵️</tg-emoji>'
)

# Кастомный маркер 📍 для подсказки по локации активности.
LOCATION_PIN_CUSTOM_EMOJI_ID = "5411603929047792996"
LOCATION_PIN_HTML = f'<tg-emoji emoji-id="{LOCATION_PIN_CUSTOM_EMOJI_ID}">📍</tg-emoji>'

LECTURES: dict[str, tuple[str, str]] = {
    "lecture_1": ("Лекция 1", "коллеги"),
    "lecture_2": ("Лекция 2", "капучинка"),
    "lecture_3": ("Лекция 3", "вайбик"),
}

ACTIVITIES_TEXT: dict[str, tuple[str, str, str]] = {
    "hr_date": (
        "1-1 с рекрутером",
        "HR-свидание",
        "Познакомься с рекрутерами и пройди экспресс-собеседование. Ты сможешь обсудить "
        "свои карьерные цели и понять, какой трек тебе подходит.\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации HR-свидания</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} За эту активность ты получишь 100 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "it_jenga": (
        "ИТ-Дженга",
        "ИТ-Дженга",
        "Аккуратно вытащи брусок и узнай, кто ты сегодня — разработчик, "
        "тестировщик или аналитик. А может ты вытянешь бонус?\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации Технологии</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Реши рабочую задачу до дедлайна и получи 200 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "it_memo": (
        "ИТ-МЕМО",
        "ИТ-МЕМО",
        "Прояви чутьё программиста и найди пару для логотипа. Это может быть "
        "название программы, язык или инструмент программирования. Для победы "
        "собери 1 пару идентичных слотов.\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации Технологии</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Здесь можно заработать 200 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "script_master": (
        "Скрипт-мастер",
        "Скрипт-мастер",
        "Работа в продажах напоминает словесный тетрис. Знать скрипты мало, "
        "нужно применять их в правильной последовательности. Расположи фразы "
        "так, чтобы защитить клиента, банк и себя.\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации Продажи</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Здесь можно заработать 200 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "explainer": (
        "Объяснительная",
        "Объяснительная",
        "Единственная объяснительная в Совкомбанке. Найди слово по вертикали / "
        "горизонтали / диагонали и вычеркни. Нашел? А теперь пора объяснить его "
        "значение друллеге.\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации Продажи</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Здесь можно заработать 200 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "fin_assets": (
        "Финансовые активы",
        "Финансовые активы",
        "Примерь на себя роль финансового консультанта. Клиент накопил груду "
        "активов, помоги ему грамотно их распределить. Для тебя это проще "
        "простого, разбери активы по категориям.\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации Финансы</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Здесь можно заработать 200 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "fin_fate": (
        "Финансы судьбы",
        "Финансы судьбы",
        "Здесь ты научишься управлять финансами, опираясь на внешние факторы. "
        "Кидай кубик и закрывай потребности, опираясь на своё чутьё. Побеждает "
        "первый, закрывший все слоты.\n\n"
        f"{LOCATION_PIN_HTML}<b>Ищи активность в локации Финансы</b>\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Здесь можно заработать 200 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "tg_channel_future": (
        "Подписка на ТГ-канал",
        "Подписка на ТГ‑канал",
        "Подпишись на Telegram‑канал «Совкомбанк Будущее».\n\n"
        f"{KARMA_POINTS_BADGE_HTML} Здесь можно заработать 100 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "lecture_1": (
        "Лекция 1",
        LECTURE_1_TITLE_HTML,
        "<b>Маршрут перестроен: карьерные «нет», которые приведут вас к работе мечты</b>\n\n"
        "Ксюша, судя по заметкам, прокатилась на карьерных аттракционах — это покруче "
        "американских горок. Там такие взлёты и падения, но всё в копилку опыта и "
        "приобретённых навыков. Ну мёд, а не рассказ нас ждет.\n\n"
        "<b>Васильева Ксения</b>\n"
        "Руководитель отдела тестирования\n\n"
        f"{KARMA_POINTS_BADGE_HTML} За кодовое слово после лекции — 400 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "lecture_2": (
        "Лекция 2",
        LECTURE_2_TITLE_HTML,
        "<b>Как не быть свайпнутым в цифровом мире: боремся за внимание рекрутеров, "
        "коллег и клиентов</b>\n\n"
        "Подсмотрели заметки у коллег: они собираются вещать про мемы и визуал. "
        "Даже наделали пару скрин сообщений из чатиков, теперь всей командой "
        "расшифровывают сакральный смысл слова «понятно».\n\n"
        "<b>Ольга Кадникова</b>\n"
        "Старший специалист\n"
        "<b>Ольга Игнатович</b>\n"
        "Ведущий специалист\n\n"
        f"{KARMA_POINTS_BADGE_HTML} За кодовое слово после лекции — 400 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
    "lecture_3": (
        "Лекция 3",
        LECTURE_3_TITLE_HTML,
        "<b>Спастись от деградации: инструкция по осознанному обучению в эпоху AI</b>\n\n"
        "В блокноте у Вики столько размышлений о том, к чему приводит привычка думать "
        "через AI. Похоже, будем разбираться, как перестать быть «оператором ChatGPT» "
        "и начать по-настоящему соображать самим.\n\n"
        "<b>Виктория Свищева</b>\n"
        "Старший разработчик\n\n"
        f"{KARMA_POINTS_BADGE_HTML} За кодовое слово после лекции — 400 баллов кармы.\n\n"
        "Получить карму за эту активность можно один раз.",
    ),
}


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
    rows.append(
        [
            InlineKeyboardButton(
                text="Квиз о банке",
                callback_data="quiz:open",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def answer_karma_activities_screen(
    target: Message,
    *,
    state: FSMContext,
    get_user_by_telegram_id: GetUserByTelegramId,
    from_user_id: int,
) -> None:
    """Экран «Где взять карму»: текст + inline с активностями (как кнопка внизу чата)."""
    await state.clear()
    user = await get_user_by_telegram_id(from_user_id)
    if not user:
        await target.answer("Сначала нажми /start и зарегистрируйся.")
        return
    await target.answer(
        "Участвуй в интерактивах и пробуй себя в разных профессиях. "
        "Не забывай говорить свой ID друллегам из Совкомбанка, "
        "чтобы получить карму.\n\n"
        f"Выбери активность {KARMA_CHAT_HINT_ARROW_HTML}",
        parse_mode="HTML",
        reply_markup=all_activities_keyboard(),
    )


def register_activities_handlers(
    dp: Dispatcher,
    bot: Bot,
    main_nav_markup: MainNavMarkup,
    get_user_by_telegram_id: GetUserByTelegramId,
    grant_activity_once: GrantActivityOnce,
) -> None:
    # Зарегистрированы ДО FSM лекции (`LectureCode.waiting_for_code`), чтобы нажатие
    # кнопки нижнего меню вместо ввода кодового слова уводило в нужный раздел.
    @dp.message(F.text == CLIENT_NAV_KARMA)
    async def msg_nav_karma(message: Message, state: FSMContext) -> None:
        if message.from_user is None:
            return
        await answer_karma_activities_screen(
            message,
            state=state,
            get_user_by_telegram_id=get_user_by_telegram_id,
            from_user_id=message.from_user.id,
        )

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
        if slug in LECTURES:
            extra_rows.append(
                [
                    InlineKeyboardButton(
                        text="Ввести кодовое слово",
                        callback_data=f"lecture:enter:{slug}",
                    )
                ]
            )
        kb: Optional[InlineKeyboardMarkup] = (
            InlineKeyboardMarkup(inline_keyboard=extra_rows) if extra_rows else None
        )
        photo_path: Optional[Path] = None
        if slug in LECTURE_PHOTOS:
            photo_path = LECTURE_PHOTOS[slug]
        elif slug == TG_CHANNEL_FUTURE_SLUG:
            photo_path = TG_CHANNEL_COVER_PHOTO

        if photo_path is not None:
            await cb_msg.answer_photo(
                FSInputFile(str(photo_path)),
                caption=f"<b>{title}</b>\n\n{body}",
                parse_mode="HTML",
                reply_markup=kb,
            )
        else:
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

        ok, grant_msg, result = await grant_activity_once(
            user["id"], TG_CHANNEL_ACTIVITY_DB_TITLE, None
        )
        if ok and result:
            u = result["user"]
            await cb_msg.answer(
                f"Подписка подтверждена! +{result['points']} баллов кармы.\n\nБаланс: {u['balance']}.",
                reply_markup=main_nav_markup(),
            )
        else:
            if grant_msg.startswith("Лимит начислений"):
                fail_text = (
                    "Подписка подтверждена, но баллы за эту активность уже начислялись ранее."
                )
            else:
                fail_text = grant_msg
            await cb_msg.answer(fail_text, reply_markup=main_nav_markup())
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
        display_title = LECTURE_TITLE_HTML_BY_SLUG.get(slug, title)
        await state.set_state(LectureCode.waiting_for_code)
        await state.update_data(lecture_slug=slug)

        await cb_msg.answer(
            f"<b>{display_title}</b>\n\nВведи кодовое слово одним сообщением.",
            parse_mode="HTML",
            reply_markup=main_nav_markup(),
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
                "Чтобы выйти из ввода кода — нажми любой раздел в меню внизу чата.",
                reply_markup=main_nav_markup(),
            )
            return

        ok, _msg, result = await grant_activity_once(user["id"], title, None)
        await state.clear()

        if ok and result:
            u = result["user"]
            await message.answer(
                f"Код принят! +{result['points']} баллов кармы.\n\nБаланс: {u['balance']}.",
                reply_markup=main_nav_markup(),
            )
        else:
            await message.answer(
                "Похоже, баллы за эту лекцию уже начислялись ранее.",
                reply_markup=main_nav_markup(),
            )
