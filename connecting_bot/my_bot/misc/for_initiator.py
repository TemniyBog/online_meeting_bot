from aiogram import types

from connecting_bot.my_bot.keyboards.initiator_kb import ini_main_menu
from connecting_bot.my_bot.states.initiator_state import InitiatorState


async def message_to_initiator(message: types.Message, user_id):
    bot = message.bot
    await bot.send_message(chat_id=user_id,
                           text='Вы назначены инициатором, '
                                'зайдите в Главное меню',
                           reply_markup=ini_main_menu())