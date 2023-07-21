from aiogram.dispatcher.filters.state import StatesGroup, State

class UserState(StatesGroup):
    wait_for = State()
    in_game = State()
    not_in_game = State()

    # для ветки, в которой он участник
    show_list_events = State()
    make_choose = State()

    # для ветки событий, где он может поучаствовать
    show_categories = State()
    show_events = State()
    agree_disagree = State()
    agree = State()
