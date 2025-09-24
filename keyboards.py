from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Описание услуг"), KeyboardButton(text="Заказать услугу")],
        [KeyboardButton(text="Мои баллы"), KeyboardButton(text="Мои заказы")]
    ]
    if user_id == 610269479:  # Только для админа
        kb.append([KeyboardButton(text="Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Клавиатура основных услуг
def get_services_kb() -> InlineKeyboardMarkup:
    from database import get_services
    services = get_services()
    buttons = [[InlineKeyboardButton(text=service.name, callback_data=f"service_{service.id}")] for service in services]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура описания услуг
def get_services_desc_kb() -> InlineKeyboardMarkup:
    from database import get_services
    services = get_services()
    buttons = [[InlineKeyboardButton(text=service.name, callback_data=f"desc_{service.id}")] for service in services]
    buttons.append([InlineKeyboardButton(text="Добавьте к уборке", callback_data="desc_add_to_cleaning")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура дополнительных услуг
def get_extra_services_kb() -> InlineKeyboardMarkup:
    extra_services = {
        "kitchen": "Кухонные шкафчики",
        "fridge": "Холодильник",
        "laundry": "Стирка белья",
        "oven": "Мытьё духовки",
        "ironing": "Глажка белья",
        "grease": "Удаление жировых загрязнений",
        "grilles": "Оконные решётки"
    }
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"desc_extra_{key}")] for key, name in extra_services.items()]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_services_desc")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура выбора дополнительных услуг
def get_extra_services_selection_kb(selected_services: list = None) -> InlineKeyboardMarkup:
    if selected_services is None:
        selected_services = []
    extra_services = {
        "kitchen": "Кухонные шкафчики",
        "fridge": "Холодильник",
        "laundry": "Стирка белья",
        "oven": "Мытьё духовки",
        "ironing": "Глажка белья",
        "grease": "Удаление жировых загрязнений",
        "grilles": "Оконные решётки"
    }
    buttons = []
    for key, name in extra_services.items():
        text = f"✅ {name}" if key in selected_services else name
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"extra_{key}")])
    buttons.append([InlineKeyboardButton(text="Продолжить", callback_data="extra_continue")])
    buttons.append([InlineKeyboardButton(text="Без доп. услуг", callback_data="extra_none")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Клавиатура админ-панели
def get_admin_panel_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Действующие заказы", callback_data="admin_active_orders")],
        [InlineKeyboardButton(text="Выполненные заказы", callback_data="admin_completed_orders")],
        [InlineKeyboardButton(text="Все заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)