from collections.abc import Awaitable, Callable
import html
import random
from typing import Optional, cast

from aiogram import Dispatcher, F
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


class QuizPlay(StatesGroup):
    in_progress = State()


# Поле explain — текст в блоке-цитате после ответа (верно или неверно).
QUIZ_QUESTIONS: list[dict[str, object]] = [
    {
        "q": "Как раньше назывался Совкомбанк?",
        "opts": ["Советский", "Стекбанк", "Костромской", "Буйкомбанк"],
        "ok": 3,
        "explain": "– Совкомбанк вырос из Буйского коммерческого банка;\n– Название «Буйкомбанк» часто упоминают в истории бренда как исходную точку.",
    },
    {
        "q": "Что коллекционирует Первый заместитель председателя правления Сергей Хотимский?",
        "opts": ["Трости", "Монеты", "Машины"],
        "ok": 0,
        "explain": "– У Сергея Хотимского известна коллекция тростей;\n– Это один из узнаваемых фактов образа в профессиональных и медийных историях о нём.",
    },
    {
        "q": "Какая самая популярная сладость в Совкомбанке?",
        "opts": ["Мед", "Халва", "Печенье"],
        "ok": 1,
        "explain": "– Культ «халвы» в Совкомбанке давно закреплён мероприятиями и мягким маркетингом;\n– Для многих сотрудников это символ именно нашей атмосферы.",
    },
    {
        "q": "В скольких городах есть офис Совкомбанка?",
        "opts": ["500+", "800+", "1000+"],
        "ok": 2,
        "explain": "– Сеть присутствия банка — одна из крупнейших среди региональных игроков;\n– По публичным данным география исчисляется тысячами населённых пунктов.",
    },
    {
        "q": "У нас есть конкурс стартапов — Лига достижений. Где она не проходила?",
        "opts": ["Сочи", "Марокко", "Греция", "Турция"],
        "ok": 2,
        "explain": "– Лига достижений неоднократно выезжала в топовые локации (Сочи, Марокко, Турция и др.).\n– Вариант про Грецию в этом наборе — «лишний» город с точки зрения известной географии тура.",
    },
    {
        "q": "Как раньше назывался Совкомбанк?",
        "opts": ["Советский", "Костромской", "Буйкомбанк"],
        "ok": 2,
        "explain": "– Историческое название — Буйкомбанк;\n– Остальные варианты намеренно смешивают география и привычное слово «советский».",
    },
    {
        "q": "Сколько денег может сэкономить сотрудник Совкомбанка, активно пользуясь социальными программами, за год?",
        "opts": ["1 700 000", "100 000", "520 000"],
        "ok": 2,
        "explain": "– На мерче и программных материалах для сотрудников фигурирует оценка порядка 520 тысяч рублей экономии при активном участии.",
    },
    {
        "q": "Сколько % руководителей построили свою карьеру в Совкомбанке?",
        "opts": ["70%", "50%", "68%"],
        "ok": 2,
        "explain": "– Совкомбанк подчёркивает долю управленцев, выросших внутри банка;\n– В официальных цифрах для Лиг приключений чаще встречается ~68%.",
    },
    {
        "q": "Как называется проект для похудения вместе с коллегами в Совкомбанке?",
        "opts": ["Здоровые игры", "Худеем с коллегами", "Здоровый Игорь"],
        "ok": 0,
        "explain": "– Проект называется «Здоровые игры»;\n– «Здоровый Игорь» — игра слов-подсказка, а не официальное название программы.",
    },
    {
        "q": "Какой любимый вид спорта в Совкомбанке?",
        "opts": ["Бег", "Кроссфит", "Волейбол"],
        "ok": 2,
        "explain": "– В корпоративной истории активно масштабировался волейбол корпоративных игр;\n– Лига Спорта и смежные инициативы часто ассоциируются именно с волейболом.",
    },
    {
        "q": "Как называется внутренняя валюта Совкомбанка?",
        "opts": ["Денежка", "Карма", "Халва"],
        "ok": 1,
        "explain": "– Внутренняя условная единица для мотивации сотрудников — «карма»;\n– «Халва» — бренд продукта, не валюта.",
    },
    {
        "q": "Где нет коворкинга от Совкомбанка?",
        "opts": ["Алтай", "Сочи", "Черногория"],
        "ok": 0,
        "explain": "– Коворкинг-кластеры банка известны в Сочи и Черногории и др.;\n– Алтай в этом списке выбран как локация без такого коворкинга в рамках квиза.",
    },
    {
        "q": "Какой рабочий график у сотрудников Совкомбанка в коворкинге?",
        "opts": ["4/3", "5/2", "6/7"],
        "ok": 1,
        "explain": "– В коворкинг-формате для сотрудников закреплён привычный офисный график 5/2.",
    },
    {
        "q": "У нас есть Лига Спорта. Сколько городов представляли участники в этом году?",
        "opts": ["19", "15", "10"],
        "ok": 0,
        "explain": "– В материалах сезона Лиги Спорта фигурирует 19 городов-участников.",
    },
    {
        "q": "Как зовут нашу розовую свинку-копилку?",
        "opts": ["Ниночка", "Мариночка", "Изабэль"],
        "ok": 0,
        "explain": "– Маскот-копилка в коммуникациях банка — Ниночка.",
    },
    {
        "q": "«Кредитный доктор» — это?",
        "opts": ["Услуга Совкомбанка", "Книга", "Коллега процентного терапевта"],
        "ok": 0,
        "explain": "– «Кредитный доктор» — сервис/продукт Совкомбанка по работе с кредитной нагрузкой.",
    },
    {
        "q": "Как называется приложение для общения сотрудников Совкомбанка?",
        "opts": ["МОПСС", "ОПСС", "ДРОПС"],
        "ok": 0,
        "explain": "– Корпоративный мессенджер сотрудников — МОПСС.",
    },
    {
        "q": "Как называется карьерный фест от Совкомбанка?",
        "opts": ["Лига Справедливости", "Лига студентов", "Лига Приключений"],
        "ok": 2,
        "explain": "– Фест для кандидатов и студентов — Лига Приключений;\n– Именно под этим брендом вы встречаетесь на мероприятии.",
    },
    {
        "q": "В Италии наравне с золотом и валютой можно хранить в банке?",
        "opts": ["Пармезан", "Виноград", "Макароны"],
        "ok": 0,
        "explain": "– В Италии пармезан (как актив) отчасти воспринимают почти как «ценность», и в медиа встречаются истории про хранение сыра в банковских ячейках;\n– Для квиза верный ответ — пармезан.",
    },
    {
        "q": "Родина банков — это?",
        "opts": ["Венеция", "Греция", "Швеция"],
        "ok": 0,
        "explain": "– Ранние формы банковского дела связывают с итальянскими торговыми центрами, в том числе Венецией;",
    },
]


def quiz_explain_markup(explain_plain: str) -> str:
    """Блок как у цитаты в клиенте TG: полоса слева, при желании можно свернуть."""
    body = html.escape(explain_plain.strip("\n"))
    return f"<blockquote expandable><b>Что важно:</b>\n{body}</blockquote>"


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
        [InlineKeyboardButton(text="🏠 В меню", callback_data="quiz:exit")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def register_quiz_handlers(
    dp: Dispatcher,
    main_reply_menu: MainReplyMenu,
    get_user_by_telegram_id: GetUserByTelegramId,
    grant_activity_once: GrantActivityOnce,
    activity_quiz_reward: str,
) -> None:
    intro_html = (
        "Добро пожаловать в квиз о банке! Ты готов?\n\n"
        "<i>Можно ответить на все 20 вопросов сразу — или вернуться к квизу позже "
        "(например, во время офлайн‑активностей).\n\n"
        "За каждый правильный ответ сразу начисляем +10 баллов кармы.</i>"
    )

    @dp.callback_query(F.data == "quiz:intro")
    async def quiz_intro_callback(callback: CallbackQuery, _state: FSMContext) -> None:
        cb_msg = callback.message
        if not isinstance(cb_msg, Message):
            await callback.answer()
            return
        await cb_msg.answer(
            intro_html,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Стартуем!", callback_data="quiz:start")]
                ]
            ),
        )
        await callback.answer()

    @dp.message(F.text == "Квиз о банке")
    async def quiz_intro_message(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            await message.answer("Сначала нажми /start и зарегистрируйся.")
            return
        await message.answer(
            intro_html,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Стартуем!", callback_data="quiz:start")]
                ]
            ),
        )

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

        # Случайные вопросы без повторов по тексту (даже если в списке есть дубликаты).
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

        await state.set_state(QuizPlay.in_progress)
        await state.update_data(order=order, pos=pos, q_index=order[pos], correct_cnt=0)

        q0 = QUIZ_QUESTIONS[order[pos]]
        q_text = str(q0["q"])
        await cb_msg.answer(
            f"<b>Вопрос 1/{total}</b>\n\n{html.escape(q_text)}",
            parse_mode="HTML",
            reply_markup=quiz_answer_keyboard(order[pos]),
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
        await state.clear()
        if isinstance(cb_msg, Message):
            await cb_msg.answer(
                "Квиз остановлен.\n"
                f"Ты прошёл(ла) {pos}/{total} вопросов, "
                f"правильных ответов: {correct_cnt}.\n\n"
                "<i>Можно вернуться к квизу позже — баллы за уже отвеченные "
                "правильные вопросы сохранены.</i>",
                parse_mode="HTML",
                reply_markup=main_reply_menu(),
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
        quote_html = quiz_explain_markup(explain_plain)

        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer()
            return

        if correct:
            grant_ok, _gmsg, result = await grant_activity_once(
                user["id"],
                activity_quiz_reward,
                None,
            )
            if grant_ok and result:
                u = result["user"]
                header = (
                    f"✅ Верно! Начислено {result['points']} баллов кармы. "
                    f"Баланс: {u['balance']}."
                )
            else:
                header = (
                    "✅ Верно! Награда за квиз уже выдавалась ранее — "
                    "новые баллы не начислялись."
                )
        else:
            header = "❌ Неверно."

        # Переходим к следующему вопросу (или завершаем квиз).
        order = cast(list[int], data.get("order") or [])
        pos = int(data.get("pos") or 0)
        correct_cnt = int(data.get("correct_cnt") or 0) + (1 if correct else 0)
        total = len(order)

        next_pos = pos + 1
        if next_pos >= total:
            await state.clear()
            await cb_msg.answer(
                f"{header}\n\n{quote_html}\n\n"
                f"<b>Квиз завершён!</b>\n"
                f"Правильных ответов: {correct_cnt}/{total}\n"
                f"Максимум за квиз: {total * 10} баллов.\n\n"
                "Если не успел(а) пройти квиз полностью — можно вернуться позже: "
                "баллы начисляются за каждый правильный ответ, но не больше 20 раз.",
                parse_mode="HTML",
                reply_markup=main_reply_menu(),
            )
        else:
            await state.update_data(
                pos=next_pos,
                q_index=order[next_pos],
                correct_cnt=correct_cnt,
            )
            next_q = QUIZ_QUESTIONS[order[next_pos]]
            next_text = str(next_q["q"])
            await cb_msg.answer(
                f"{header}\n\n{quote_html}\n\n"
                f"<b>Вопрос {next_pos + 1}/{total}</b>\n\n"
                f"{html.escape(next_text)}",
                parse_mode="HTML",
                reply_markup=quiz_answer_keyboard(order[next_pos]),
            )

        await callback.answer()
