from aiogram.dispatcher.filters.state import StatesGroup, State


class InitiatorState(StatesGroup):
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

    #для ветки событий, где он главный в ивенте
    show_my_list_events = State()
    make_my_choose = State()

    # добавление события
    set_category = State()
    set_title = State()
    set_about = State()
    set_date = State()
    set_time = State()
    set_number = State()
    confirm = State()

    # ждём ссылку на событие
    wait_for_url = State()