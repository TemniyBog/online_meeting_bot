import logging

from aiogram.dispatcher.filters import BoundFilter
from aiogram import types

from connecting_bot.my_bot.db.db_commands import is_he_initiator


class IsPrivateMsg(BoundFilter):
    async def check(self, message: types.Message):
        try:
            if message.chat.type == 'private':
                logging.info('Это приватный msg')
                return True
        except Exception:
            pass

class IsPrivateCb(BoundFilter):
    async def check(self, callback: types.CallbackQuery):
        try:
            if callback.message.chat.type == 'private':
                logging.info('Это приватный cb')
                return True
        except Exception:
            pass

class IsInitiatorMsgFilter(BoundFilter):
    async def check(self, message: types.Message) -> bool:
        return is_he_initiator(message.from_user.id)

# class IsInitiatorMsg(BoundFilter):
#     async def check(self, message: types.Message):
#         try:
#             if is_he_initiator(message.from_user.id):
#                 return True
#         except Exception:
#             pass



