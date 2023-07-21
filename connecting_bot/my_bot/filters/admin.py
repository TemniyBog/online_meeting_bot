from aiogram.dispatcher.filters import BoundFilter

from connecting_bot.my_bot.config import ADMIN
from connecting_bot.my_bot.db.db_commands import is_he_initiator


class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin=None):
        self.is_admin = is_admin

    async def check(self, obj):
        if self.is_admin is None:
            return
        user_id = obj.from_user.id
        return str(user_id) in ADMIN


