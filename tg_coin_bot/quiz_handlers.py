from collections.abc import Awaitable, Callable
import html
import json
import random
from pathlib import Path
from typing import Optional, cast

from aiogram import Dispatcher, F
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

from db_backend import db_session, is_mysql, row_to_dict
from activities_handlers import answer_karma_activities_screen

GetUserByTelegramId = Callable[[int], Awaitable[Optional[dict]]]
GrantActivityOnce = Callable[
    [int, str, Optional[int]],
    Awaitable[tuple[bool, str, Optional[dict]]],
]
MainNavMarkup = Callable[[], ReplyKeyboardMarkup]


class QuizPlay(StatesGroup):
    in_progress = State()

_BASE_DIR = Path(__file__).resolve().parent
QUIZ_FINISH_PHOTO_LEGEND_PATH = _BASE_DIR / "img" / "legend.jpg"
QUIZ_FINISH_PHOTO_VAC_PATH = _BASE_DIR / "img" / "vac.jpg"
QUIZ_FINISH_PHOTO_TRIAL_PATH = _BASE_DIR / "img" / "3ma.jpg"


# Поле explain — текст подписи «Правильный ответ:» после ответа на вопрос.
QUIZ_QUESTIONS: list[dict[str, object]] = [
    {
        "q": "Как раньше назывался Совкомбанк?",
        "opts": ["Советский", "Стекбанк", "Костромской", "Буйкомбанк"],
        "ok": 3,
        "explain": "Совкомбанк вырос из Буйкомбанка — банка из города Буй Костромской области.",
    },
    {
        "q": "В каком году был основан Совкомбанк?",
        "opts": ["1990", "2003", "2010", "1985"],
        "ok": 0,
        "explain": "Банк был основан в 1990 году. То есть он старше многих участников студенческого мероприятия.",
    },
    {
        "q": "Как называется карта рассрочки Совкомбанка?",
        "opts": ["Халва", "Карамель", "Сгущёнка", "Пломбир"],
        "ok": 0,
        "explain": "«Халва» — карта рассрочки Совкомбанка. Да, звучит как десерт, но работает как финансовый продукт.",
    },
    {
        "q": "Сколько сотрудников было у банка в 2002 году, когда он ещё был Буйкомбанком?",
        "opts": ["17", "170", "1700", "17 000"],
        "ok": 0,
        "explain": "В 2002 году у банка был один филиал, 17 сотрудников и капитал 2 млн рублей. Очень мощный пример роста из «маленькой команды» в большой банк.",
    },
    {
        "q": "Что коллекционирует первый заместитель председателя правления Сергей Хотимский?",
        "opts": ["Трости", "Монеты", "Машины", "Пластинки"],
        "ok": 0,
        "explain": "Не самый очевидный предмет для коллекции, поэтому ответ легко перепутать с монетами или машинами. Но правильный вариант — трости.",
    },
    {
        "q": "В скольких городах есть офисы Совкомбанка?",
        "opts": ["500+", "800+", "1000+", "300"],
        "ok": 2,
        "explain": "У Совкомбанка большая сеть офисов: банк представлен не только в крупных городах, но и во многих регионах России. Правильный ответ — больше 1000 городов.",
    },
    {
        "q": "Сколько руководителей построили свою карьеру в Совкомбанке?",
        "opts": ["70%", "50%", "68%", "83%"],
        "ok": 0,
        "explain": "В Совкомбанке много руководителей выросли внутри компании. Это значит, что сотрудники могут строить карьеру и двигаться дальше внутри банка.",
    },
    {
        "q": "Как называется внутренняя валюта Совкомбанка?",
        "opts": ["Денежка", "Карма", "Халва", "Совкоин"],
        "ok": 1,
        "explain": "Карма — внутренняя валюта Совкомбанка. Карму можно потратить не только на мерч, но и на более необычные лоты — например, ужин с топ-менеджером.",
    },
    {
        "q": "Как называется приложение для общения сотрудников Совкомбанка?",
        "opts": ["МОПСС", "ОПСС", "ДРОПС", "ПУПС"],
        "ok": 0,
        "explain": "МОПСС — Мобильное Объединяющее Приложение Сотрудников Совкомбанка. Через него можно общаться, следить за новостями банка, участвовать в корпоративной жизни и быть в курсе внутренних событий.",
    },
    {
        "q": "Как называется карьерный фест от Совкомбанка?",
        "opts": ["Лига Справедливости", "Лига студентов", "Лига Приключений", "Лига Достижений"],
        "ok": 2,
        "explain": "Лига Приключений — тот самый карьерный фест, на котором мы с вами сегодня встретились.",
    },
    {
        "q": "Какой экономический закон описывают фразой: «плохие деньги вытесняют хорошие»?",
        "opts": ["Грешем", "Парето", "Кейнс", "Нэш"],
        "ok": 0,
        "explain": "Закон Грешема: если в обращении есть «хорошие» и «плохие» деньги, люди стараются сохранить хорошие, а тратить плохие.",
    },
    {
        "q": "Как называется международная система обмена банковскими сообщениями?",
        "opts": ["SWIFT", "SEPA", "IBAN", "Basel"],
        "ok": 0,
        "explain": "SWIFT — это не платёжная система в прямом смысле, а сеть для передачи финансовых сообщений между банками.",
    },
    {
        "q": "Как называется номер, по которому банк можно узнать в международных переводах?",
        "opts": ["BIC", "PIN", "CVV", "OTP"],
        "ok": 0,
        "explain": "BIC помогает идентифицировать банк в международных операциях.",
    },
    {
        "q": "В Италии есть банки, где в качестве ценности можно хранить не только золото и валюту, но и продукт, который буквально созревает годами. Что это?",
        "opts": ["Пармезан", "Виноград", "Макароны"],
        "ok": 0,
        "explain": "В Италии сыр пармезан может использоваться как ценный актив и залог.",
    },
    {
        "q": "Современные банки выросли из торговых домов, менял и лавок, где хранили деньги и оформляли расчёты. Какой город часто называют родиной банковского дела?",
        "opts": ["Венеция", "Греция", "Швеция"],
        "ok": 0,
        "explain": "Итальянские торговые города, включая Венецию, сыграли огромную роль в развитии банковского дела.",
    },
    {
        "q": "Слово «salary» часто связывают с продуктом, который в древности был настолько ценным, что им могли рассчитываться. Что это?",
        "opts": ["Соль", "Сахар", "Перец", "Мёд"],
        "ok": 0,
        "explain": "Соль была важным товаром: её использовали для хранения еды, торговли и расчётов. Поэтому она часто всплывает в историях про деньги.",
    },
    {
        "q": "В 2010 году программист купил две пиццы за криптовалюту. Сегодня эту историю вспоминают как легенду. Что это была за криптовалюта?",
        "opts": ["Биткоин", "Эфир", "Догикоин", "Тонкоин"],
        "ok": 0,
        "explain": "Покупка двух пицц за биткоины стала одним из самых известных примеров раннего использования криптовалюты.",
    },
    {
        "q": "В каком государстве появились первые бумажные деньги?",
        "opts": ["Китай", "Рим", "Египет", "Греция"],
        "ok": 0,
        "explain": "Бумажные деньги появились в Китае: там торговцы начали использовать бумажные расписки вместо тяжёлых монет.",
    },
    {
        "q": "Какая валюта получила название от меры веса?",
        "opts": ["Фунт", "Евро", "Йена", "Рубль"],
        "ok": 0,
        "explain": "Фунт изначально связан с мерой веса. Деньги и вес раньше часто были рядом: стоимость монет зависела от количества металла.",
    },
    {
        "q": "Что раньше буквально «рубили», и от этого, по одной из версий, появилось название русской валюты?",
        "opts": ["Серебро", "Золото", "Медь", "Железо"],
        "ok": 0,
        "explain": "Есть версия, что «рубль» связан с отрубленным куском серебра. Деньги тогда могли быть не купюрой, а частью металлического слитка.",
    },
]


def quiz_feedback_with_answer_html(header: str, explain_plain: str) -> str:
    """Вердикт + пояснение без blockquote (как в макете)."""
    body = html.escape(explain_plain.strip("\n").strip())
    return f"{header}\n\n<b>Правильный ответ:</b>\n{body}"


def quiz_answer_keyboard(q_index: int) -> InlineKeyboardMarkup:
    q = QUIZ_QUESTIONS[q_index]
    opts = cast(list[str], q["opts"])
    buttons: list[list[InlineKeyboardButton]] = []
    for i, label in enumerate(opts):
        short = label[:60] + ("…" if len(label) > 60 else "")
        buttons.append(
            [InlineKeyboardButton(text=short, callback_data=f"quiz:{q_index}:{i}")]
        )
    buttons.append(
        [InlineKeyboardButton(text="Сделать паузу", callback_data="quiz:exit")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


QUIZ_INTRO_MEGAPHONE_CUSTOM_EMOJI_ID = "5413326863768516253"
QUIZ_INTRO_MEGAPHONE_HTML = (
    f'<tg-emoji emoji-id="{QUIZ_INTRO_MEGAPHONE_CUSTOM_EMOJI_ID}">📣</tg-emoji>'
)

QUIZ_CORRECT_CUSTOM_EMOJI_ID = "5413543639357881985"
QUIZ_CORRECT_HTML = f'<tg-emoji emoji-id="{QUIZ_CORRECT_CUSTOM_EMOJI_ID}">⚡️</tg-emoji>'

QUIZ_WRONG_CUSTOM_EMOJI_ID = "5413529560455082973"
QUIZ_WRONG_HTML = f'<tg-emoji emoji-id="{QUIZ_WRONG_CUSTOM_EMOJI_ID}">⛔️</tg-emoji>'

# Кастомный ❓ в заголовке «Вопрос n из m» (web: data-doc-id → Bot API emoji-id).
QUIZ_QUESTION_HEAD_CUSTOM_EMOJI_ID = "5413328482971187475"
QUIZ_QUESTION_HEAD_HTML = (
    f'<tg-emoji emoji-id="{QUIZ_QUESTION_HEAD_CUSTOM_EMOJI_ID}">❓</tg-emoji>'
)


def quiz_question_message_html(*, display_num: int, total: int, q_text: str) -> str:
    return (
        f"{QUIZ_QUESTION_HEAD_HTML} <b>Вопрос {display_num} из {total}</b>\n\n"
        f"{html.escape(q_text)}"
    )


def quiz_completion_summary_html(*, correct_cnt: int, total: int) -> str:
    """Итог квиза по числу правильных ответов (до 5, 6–15, от 16)."""
    if correct_cnt <= 5:
        title = "Ты — Кнопипопи на испытательном сроке"
        body = (
            "Кнопипопи пока осваивается в офисе.\n\n"
            "Но ничего страшного — главное, что ты попробовал! "
            "Можно вернуться к активностям и заработать ещё карму"
        )
    elif correct_cnt <= 15:
        title = "Ты — Кнопипопи в отпуске"
        body = (
            "Кнопипопи уже почти отключил уведомления.\n\n"
            "Ты прошёл большую часть пути и неплохо справился. "
            "Ещё немного — и будет почти экспертный уровень."
        )
    else:
        title = "Кнопипопи — легенда офиса"
        body = (
            "Кнопипопи официально в офисном топе!\n\n"
            "Ты отлично справился и не оставил квизу шансов. Забираешь заслуженную карму!"
        )

    return (
        f"<b>Квиз завершён!</b> 🎉\n"
        f"Твой результат: {correct_cnt} из {total}.\n\n"
        f"<b>{html.escape(title)}</b>\n\n"
        f"{html.escape(body)}"
    )


def quiz_completion_photo_path(*, correct_cnt: int) -> Path:
    if correct_cnt <= 5:
        return QUIZ_FINISH_PHOTO_TRIAL_PATH
    if correct_cnt <= 15:
        return QUIZ_FINISH_PHOTO_VAC_PATH
    return QUIZ_FINISH_PHOTO_LEGEND_PATH


BANK_QUIZ_INTRO_HTML = (
    f"{QUIZ_INTRO_MEGAPHONE_HTML} Добро пожаловать в квиз о банке! Ты готов?\n\n"
    "<i>Можно ответить на все 20 вопросов сразу — или вернуться к квизу позже "
    ".\n\n"
    "За каждый правильный ответ сразу начисляем +10 баллов кармы.</i>"
)

BANK_QUIZ_START_INLINE_KB = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Стартуем!", callback_data="quiz:start")]
    ]
)

BANK_QUIZ_CONTINUE_INLINE_KB = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Продолжить", callback_data="quiz:start")]
    ]
)

BANK_QUIZ_ALREADY_DONE_HTML = (
    f"{QUIZ_INTRO_MEGAPHONE_HTML} Ты уже прошёл квиз!\n\n"
    "Баллы кармы за вопросы начисляются один раз :)"
)

BANK_QUIZ_BACK_TO_MENU_INLINE_KB = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад к активностям", callback_data="quiz:menu")]
    ]
)


async def _quiz_load_progress(user_id: int) -> Optional[dict]:
    async with db_session() as db:
        cur = await db.execute(
            "SELECT * FROM quiz_progress WHERE user_id = ?",
            (user_id,),
        )
        row = await cur.fetchone()
        return row_to_dict(row) if row else None


def _quiz_saved_is_resumable(saved: dict) -> bool:
    try:
        order = json.loads(str(saved.get("order_json") or "[]"))
    except Exception:
        return False
    if not isinstance(order, list) or not order:
        return False
    pos = int(saved.get("pos") or 0)
    return 0 <= pos < len(order)


async def _quiz_is_completed(user_id: int) -> bool:
    async with db_session() as db:
        cur = await db.execute(
            "SELECT 1 AS ok FROM quiz_completion WHERE user_id = ? LIMIT 1",
            (user_id,),
        )
        row = await cur.fetchone()
        return row is not None


async def _quiz_mark_completed(user_id: int) -> None:
    if is_mysql():
        async with db_session() as db:
            await db.execute(
                "INSERT IGNORE INTO quiz_completion (user_id) VALUES (?)",
                (user_id,),
            )
            await db.commit()
        return
    async with db_session() as db:
        await db.execute(
            "INSERT OR IGNORE INTO quiz_completion (user_id) VALUES (?)",
            (user_id,),
        )
        await db.commit()


async def _quiz_save_progress(user_id: int, *, order: list[int], pos: int, correct_cnt: int) -> None:
    order_json = json.dumps(order, ensure_ascii=False)
    if is_mysql():
        async with db_session() as db:
            await db.execute(
                """
                INSERT INTO quiz_progress (user_id, order_json, pos, correct_cnt)
                VALUES (?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                    order_json = VALUES(order_json),
                    pos = VALUES(pos),
                    correct_cnt = VALUES(correct_cnt)
                """,
                (user_id, order_json, int(pos), int(correct_cnt)),
            )
            await db.commit()
        return

    async with db_session() as db:
        await db.execute(
            """
            INSERT INTO quiz_progress (user_id, order_json, pos, correct_cnt)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                order_json = excluded.order_json,
                pos = excluded.pos,
                correct_cnt = excluded.correct_cnt,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, order_json, int(pos), int(correct_cnt)),
        )
        await db.commit()


async def _quiz_clear_progress(user_id: int) -> None:
    async with db_session() as db:
        await db.execute("DELETE FROM quiz_progress WHERE user_id = ?", (user_id,))
        await db.commit()


async def _quiz_mark_awarded_if_new(user_id: int, q_index: int) -> bool:
    """
    Возвращает True, если это первый раз (user_id, q_index) и мы пометили как награждённый.
    False — если уже был (карму повторно не даём).
    """
    async with db_session() as db:
        try:
            await db.execute(
                "INSERT INTO quiz_awards (user_id, q_index, awarded) VALUES (?, ?, 1)",
                (user_id, int(q_index)),
            )
            await db.commit()
            return True
        except Exception:
            # SQLite: sqlite3.IntegrityError; MySQL: IntegrityError.
            # Награда уже выдавалась за этот вопрос.
            return False


async def _send_bank_quiz_intro_if_registered(
    target: Message,
    *,
    get_user_by_telegram_id: GetUserByTelegramId,
    telegram_id: int,
    main_nav_markup: MainNavMarkup,
) -> bool:
    """Отправляет экран квиза в чат. False — пользователь не зарегистрирован."""
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        return False
    uid = int(user["id"])
    if await _quiz_is_completed(uid):
        await target.answer(
            BANK_QUIZ_ALREADY_DONE_HTML,
            parse_mode="HTML",
            reply_markup=BANK_QUIZ_BACK_TO_MENU_INLINE_KB,
        )
        return True
    saved = await _quiz_load_progress(uid)
    if saved and _quiz_saved_is_resumable(saved):
        try:
            order = cast(list[int], json.loads(str(saved.get("order_json") or "[]")))
        except Exception:
            order = []
        pos = int(saved.get("pos") or 0)
        total = len(order) if order else 0
        at_q = pos + 1 if total else 0
        resume_html = (
            f"{QUIZ_INTRO_MEGAPHONE_HTML} У тебя есть незавершённый квиз\n\n"
            f"Ты остановился на вопросе {at_q} из {total}.\n\n"
            "Нажми «Продолжить», чтобы вернуться к квизу."
        )
        await target.answer(
            resume_html,
            parse_mode="HTML",
            reply_markup=BANK_QUIZ_CONTINUE_INLINE_KB,
        )
        return True
    await target.answer(
        BANK_QUIZ_INTRO_HTML,
        parse_mode="HTML",
        reply_markup=BANK_QUIZ_START_INLINE_KB,
    )
    return True


async def answer_bank_quiz_intro_message(
    message: Message,
    *,
    get_user_by_telegram_id: GetUserByTelegramId,
    main_nav_markup: MainNavMarkup,
) -> None:
    from_user = message.from_user
    if from_user is None:
        return
    if not await _send_bank_quiz_intro_if_registered(
        message,
        get_user_by_telegram_id=get_user_by_telegram_id,
        telegram_id=from_user.id,
        main_nav_markup=main_nav_markup,
    ):
        await message.answer("Сначала нажми /start и зарегистрируйся.")


def register_quiz_handlers(
    dp: Dispatcher,
    main_nav_markup: MainNavMarkup,
    get_user_by_telegram_id: GetUserByTelegramId,
    grant_activity_once: GrantActivityOnce,
    activity_quiz_reward: str,
) -> None:
    @dp.callback_query(F.data == "quiz:menu")
    async def quiz_back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if not isinstance(cb_msg, Message):
            await callback.answer()
            return
        if callback.from_user is None:
            await callback.answer()
            return
        await answer_karma_activities_screen(
            cb_msg,
            state=state,
            get_user_by_telegram_id=get_user_by_telegram_id,
            from_user_id=callback.from_user.id,
        )
        await callback.answer()

    @dp.callback_query(F.data == "quiz:open")
    async def quiz_open_from_karma_menu(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.from_user is None:
            await callback.answer()
            return
        cb_msg = callback.message
        if not isinstance(cb_msg, Message):
            await callback.answer()
            return
        if not await _send_bank_quiz_intro_if_registered(
            cb_msg,
            get_user_by_telegram_id=get_user_by_telegram_id,
            telegram_id=callback.from_user.id,
            main_nav_markup=main_nav_markup,
        ):
            await callback.answer("Сначала /start", show_alert=True)
            return
        await callback.answer()

    @dp.callback_query(F.data == "quiz:start")
    async def quiz_start(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.from_user is None:
            await callback.answer()
            return
        cb_msg = callback.message
        if not isinstance(cb_msg, Message):
            await callback.answer()
            return
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Сначала /start", show_alert=True)
            return

        if await _quiz_is_completed(int(user["id"])):
            await callback.answer(
                "Ты уже прошёл(ла) квиз целиком.",
                show_alert=True,
            )
            return

        # Если уже есть сохранённый прогресс — продолжаем.
        saved = await _quiz_load_progress(user["id"])
        order: list[int]
        pos: int
        correct_cnt: int
        if saved:
            try:
                order = cast(list[int], json.loads(str(saved.get("order_json") or "[]")))
            except Exception:
                order = []
            pos = int(saved.get("pos") or 0)
            correct_cnt = int(saved.get("correct_cnt") or 0)
        else:
            order = []
            pos = 0
            correct_cnt = 0

        if not order or pos < 0 or pos >= len(order):
            # Новый запуск: случайные вопросы без повторов по тексту (даже если в списке есть дубликаты).
            seen_q: set[str] = set()
            unique_indices: list[int] = []
            for i, q in enumerate(QUIZ_QUESTIONS):
                q_text = str(q.get("q", ""))
                if q_text in seen_q:
                    continue
                seen_q.add(q_text)
                unique_indices.append(i)

            total = min(20, len(unique_indices))
            random.shuffle(unique_indices)
            order = unique_indices[:total]
            pos = 0
            correct_cnt = 0
            await _quiz_save_progress(user["id"], order=order, pos=pos, correct_cnt=correct_cnt)

        await state.set_state(QuizPlay.in_progress)
        cur_q = order[pos]
        await state.update_data(
            order=order,
            pos=pos,
            q_index=cur_q,
            correct_cnt=correct_cnt,
            user_db_id=user["id"],
        )

        q0 = QUIZ_QUESTIONS[cur_q]
        q_text = str(q0["q"])
        total = len(order)
        display_num = pos + 1
        await cb_msg.answer(
            quiz_question_message_html(
                display_num=display_num, total=total, q_text=q_text
            ),
            parse_mode="HTML",
            reply_markup=quiz_answer_keyboard(cur_q),
        )
        await callback.answer()

    @dp.callback_query(F.data == "quiz:exit", QuizPlay.in_progress)
    async def quiz_exit(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        data = await state.get_data()
        order = cast(list[int], data.get("order") or [])
        pos = int(data.get("pos") or 0)
        correct_cnt = int(data.get("correct_cnt") or 0)
        total = len(order)
        # Прогресс сохраняем в БД, чтобы продолжить после выхода в меню.
        user_db_id = data.get("user_db_id")
        if isinstance(user_db_id, int):
            await _quiz_save_progress(user_db_id, order=order, pos=pos, correct_cnt=correct_cnt)
        await state.clear()
        if isinstance(cb_msg, Message):
            await cb_msg.answer(
                "Квиз остановлен.\n"
                f"Ты прошёл {pos}/{total} вопросов, "
                f"правильных ответов: {correct_cnt}.\n\n"
                "К квизу можно вернуться позже — карма за правильные ответы уже сохранена.",
                parse_mode="HTML",
                reply_markup=main_nav_markup(),
            )
        await callback.answer()

    @dp.callback_query(F.data.startswith("quiz:"), QuizPlay.in_progress)
    async def quiz_answer(callback: CallbackQuery, state: FSMContext) -> None:
        cb_msg = callback.message
        if not isinstance(cb_msg, Message) or callback.data is None:
            await callback.answer()
            return
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer()
            return
        try:
            q_index_cb = int(parts[1])
            ans_index = int(parts[2])
        except ValueError:
            await callback.answer()
            return

        data = await state.get_data()
        cur = data.get("q_index")
        if cur is None or q_index_cb != cur:
            await callback.answer("Это уже не тот вопрос.", show_alert=True)
            return

        if callback.from_user is None:
            await callback.answer()
            return

        q = QUIZ_QUESTIONS[q_index_cb]
        ok_idx = int(cast(int, q["ok"]))
        correct = ans_index == ok_idx
        explain_plain = str(q.get("explain", "Спасибо за ответ!"))

        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer()
            return

        if correct:
            first_time_for_question = await _quiz_mark_awarded_if_new(user["id"], q_index_cb)
            if first_time_for_question:
                grant_ok, _gmsg, result = await grant_activity_once(
                    user["id"],
                    activity_quiz_reward,
                    None,
                )
                if grant_ok and result:
                    u = result["user"]
                    header = (
                        f"{QUIZ_CORRECT_HTML} Верно! Начислено {result['points']} баллов кармы. "
                        f"Баланс: {u['balance']}."
                    )
                else:
                    header = (
                        f"{QUIZ_CORRECT_HTML} Верно! Лимит наград за квиз уже исчерпан — "
                        "новые баллы не начислялись."
                    )
            else:
                header = f"{QUIZ_CORRECT_HTML} Верно! За этот вопрос карма уже начислялась ранее."
        else:
            header = f"{QUIZ_WRONG_HTML} Неверно"

        feedback_html = quiz_feedback_with_answer_html(header, explain_plain)
        order = cast(list[int], data.get("order") or [])
        pos = int(data.get("pos") or 0)
        correct_cnt = int(data.get("correct_cnt") or 0) + (1 if correct else 0)
        total = len(order)

        next_pos = pos + 1
        if next_pos >= total:
            user_db_id = data.get("user_db_id")
            if isinstance(user_db_id, int):
                await _quiz_clear_progress(user_db_id)
                await _quiz_mark_completed(user_db_id)
            await state.clear()
            await cb_msg.answer(feedback_html, parse_mode="HTML")
            await cb_msg.answer_photo(
                FSInputFile(str(quiz_completion_photo_path(correct_cnt=correct_cnt))),
            )
            await cb_msg.answer(
                quiz_completion_summary_html(correct_cnt=correct_cnt, total=total),
                parse_mode="HTML",
                reply_markup=main_nav_markup(),
            )
        else:
            next_q_idx = order[next_pos]
            await state.update_data(
                pos=next_pos,
                q_index=next_q_idx,
                correct_cnt=correct_cnt,
            )
            user_db_id = data.get("user_db_id")
            if isinstance(user_db_id, int):
                await _quiz_save_progress(
                    user_db_id, order=order, pos=next_pos, correct_cnt=correct_cnt
                )
            next_q = QUIZ_QUESTIONS[next_q_idx]
            next_text = str(next_q["q"])
            await cb_msg.answer(
                f"{feedback_html}\n\n"
                f"{quiz_question_message_html(display_num=next_pos + 1, total=total, q_text=next_text)}",
                parse_mode="HTML",
                reply_markup=quiz_answer_keyboard(next_q_idx),
            )

        await callback.answer()
