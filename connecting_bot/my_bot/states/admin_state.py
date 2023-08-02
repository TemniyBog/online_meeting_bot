from aiogram.dispatcher.filters.state import StatesGroup, State


class AdminState(StatesGroup):
    wait_for = State()
    in_game = State()

    # для ветки, в которой он участник
    show_list_events = State()
    make_choose = State()

    # для ветки событий, где он может поучаствовать
    show_categories = State()
    show_events = State()
    agree_disagree = State()
    agree = State()

    # ждём город для определения часового пояса
    wait_for_city = State()

    # для добавления инициаторов
    wait_for_nick = State()

    # для добавления категории
    wait_for_category = State()
