from collections.abc import Awaitable, Callable
from typing import Optional

from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup

MainReplyMenu = Callable[[], ReplyKeyboardMarkup]
GetUserByTelegramId = Callable[[int], Awaitable[Optional[dict]]]
GetQuestionsCountForUser = Callable[[int], Awaitable[int]]
CreateQuestion = Callable[[int, str], Awaitable[None]]


class OpenMicQuestion(StatesGroup):
    waiting_for_text = State()


def register_questions_handlers(
    dp: Dispatcher,
    main_reply_menu: MainReplyMenu,
    get_user_by_telegram_id: GetUserByTelegramId,
    get_questions_count_for_user: GetQuestionsCountForUser,
    create_question: CreateQuestion,
) -> None:
    @dp.message(F.text == "🎤 Задать вопрос (открытый микрофон)")
    async def open_mic_question_start(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            await message.answer("Сначала нажми /start и зарегистрируйся.")
            return

        asked = await get_questions_count_for_user(user["id"])
        if asked >= 3:
            await message.answer(
                "Ты уже задал(а) максимум 3 вопроса для открытого микрофона.\n\n"
                "Если нужно — подойди к организатору.",
                reply_markup=main_reply_menu(),
            )
            return

        await state.set_state(OpenMicQuestion.waiting_for_text)
        await message.answer(
            "Напиши свой вопрос одним сообщением.\n\n"
            "Лимит: 3 вопроса на человека.\n"
            "Чтобы отменить — нажми «Меню».",
            reply_markup=main_reply_menu(),
        )

    @dp.message(OpenMicQuestion.waiting_for_text)
    async def open_mic_question_text(message: Message, state: FSMContext) -> None:
        from_user = message.from_user
        if from_user is None:
            return
        user = await get_user_by_telegram_id(from_user.id)
        if not user:
            await message.answer("Сначала нажми /start и зарегистрируйся.")
            await state.clear()
            return

        text = (message.text or "").strip()
        if not text:
            await message.answer("Напиши вопрос текстом одним сообщением.")
            return

        if len(text) > 1000:
            await message.answer("Слишком длинно. Сократи, пожалуйста, до 1000 символов.")
            return

        asked = await get_questions_count_for_user(user["id"])
        if asked >= 3:
            await state.clear()
            await message.answer(
                "Похоже, лимит 3 вопроса уже исчерпан.",
                reply_markup=main_reply_menu(),
            )
            return

        await create_question(user["id"], text)
        await state.clear()

        remaining = max(0, 3 - (asked + 1))
        await message.answer(
            "✅ Вопрос записан! Спасибо.\n\n"
            f"Осталось вопросов: {remaining} из 3.",
            reply_markup=main_reply_menu(),
        )

