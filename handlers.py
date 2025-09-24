from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user, get_services, create_order, get_user_orders, Service, SessionLocal, get_all_orders, Order
from keyboards import get_main_menu, get_services_kb, get_services_desc_kb, get_extra_services_kb, get_extra_services_selection_kb, get_admin_panel_kb
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
import json
from datetime import datetime, time, timedelta

router = Router()

# Определяем состояния для процесса заказа
class OrderStates(StatesGroup):
    waiting_service = State()
    waiting_meter = State()
    waiting_extra_services = State()
    waiting_extra_quantity = State()
    waiting_date = State()
    waiting_time = State()
    waiting_address = State()
    waiting_confirm = State()

# Цены дополнительных услуг
EXTRA_SERVICES_PRICES = {
    "kitchen": {"name": "Кухонные шкафчики", "price": 800, "unit": "шкафчик"},
    "fridge": {"name": "Холодильник", "price": 800, "unit": "холодильник"},
    "laundry": {"name": "Стирка белья", "price": 250, "unit": "загрузка"},
    "oven": {"name": "Мытьё духовки", "price": 800, "unit": "духовка"},
    "ironing": {"name": "Глажка белья", "price": 990, "unit": "час"},
    "grease": {"name": "Удаление жировых загрязнений", "price": 990, "unit": "час"},
    "grilles": {"name": "Оконные решётки", "price": 450, "unit": "окно"},
}

# Создаём инлайн-клавиатуру для возврата в главное меню
def get_main_inline_kb() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="Вернуться в главное меню", callback_data="back_main")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функция для форматирования дополнительных услуг
def format_extra_services(params: dict) -> str:
    extra_services = params.get('extra_services', {})
    if not extra_services:
        return "Нет"
    services_list = []
    for es, qty in extra_services.items():
        if qty > 0:
            services_list.append(f"{EXTRA_SERVICES_PRICES[es]['name']} ({qty} {EXTRA_SERVICES_PRICES[es]['unit']})")
    return ", ".join(services_list) if services_list else "Нет"

# Обработчик команды /start
@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    print("Команда /start, User ID:", message.from_user.id)
    try:
        user = get_user(message.from_user.id)
        if user:
            await message.answer(f"Привет, Женя! Добро пожаловать. У тебя {user.points} баллов.", reply_markup=get_main_menu(message.from_user.id))
        else:
            await message.answer("Привет! Добро пожаловать.", reply_markup=get_main_menu(message.from_user.id))
    except Exception as e:
        print(f"Ошибка в start_handler: {str(e)}")
        await message.answer("Произошла ошибка при старте. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))

# Обработчик кнопки "Описание услуг"
@router.message(F.text == "Описание услуг")
async def services_desc(message: Message):
    print("Нажата 'Описание услуг', User ID:", message.from_user.id)
    try:
        services = get_services()
        print(f"Услуги из базы в services_desc: {[s.name for s in services]}")
        if not services:
            await message.answer("Нет доступных услуг в базе данных. Обратитесь к администратору.", reply_markup=get_main_menu(message.from_user.id))
            return
        services_kb = get_services_desc_kb()
        if not services_kb:
            await message.answer("Ошибка при создании клавиатуры услуг. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))
            return
        await message.answer("Выберите услугу для описания:", reply_markup=services_kb)
    except Exception as e:
        print(f"Ошибка в services_desc: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))

# Обработчик описания услуг и дополнительных услуг
@router.callback_query(F.data.startswith("desc_"))
async def show_service_description(callback: CallbackQuery):
    print(f"Выбрано описание, Callback data: {callback.data}, User ID: {callback.from_user.id}")
    try:
        data = callback.data
        print(f"Обрабатываем callback_data: {data}")
        if data == "desc_add_to_cleaning":
            print("Выбрано 'Добавьте к уборке'")
            await callback.message.edit_text("Выберите дополнительную услугу:", reply_markup=get_extra_services_kb())
        elif data == "desc_extra_kitchen":
            description = (
                "<b>КУХОННЫЕ ШКАФЧИКИ</b>\n\n"
                "• Помоем все кухонные шкафы снаружи и внутри;\n"
                "• Бережно удалим пятна и разводы лёгкой степени загрязнения;\n\n"
                "<b>Ограничения</b>\n"
                "❌ Вам нужно предоставить табурет или стремянку, чтобы мы ничего не упустили."
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        elif data == "desc_extra_fridge":
            description = (
                "<b>ХОЛОДИЛЬНИК</b>\n\n"
                "• Помоем холодильник и морозильную камеру;\n"
                "• Удалим подтёки и неприятный запах;\n\n"
                "<b>Ограничения</b>\n"
                "❌ Вам нужно предварительно разморозить и освободить холодильник;\n"
                "❌ Если не требуется мытьё морозильной камеры, вы можете просто освободить полки."
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        elif data == "desc_extra_laundry":
            description = (
                "<b>СТИРКА БЕЛЬЯ</b>\n\n"
                "• Загрузим бельё в стирку и развешаем сушиться;"
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        elif data == "desc_extra_oven":
            description = (
                "<b>МЫТЬЁ ДУХОВКИ</b>\n\n"
                "• Помоем духовку внутри и снаружи;\n"
                "• Бережно удалим застарелые пятна жира и другие последствия кулинарных подвигов;"
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        elif data == "desc_extra_ironing":
            description = (
                "<b>ГЛАЖКА БЕЛЬЯ</b>\n\n"
                "• Бережно погладим любые вещи, шторы, постельные и кухонные принадлежности;"
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        elif data == "desc_extra_grease":
            description = (
                "<b>УДАЛЕНИЕ ЖИРОВЫХ ЗАГРЯЗНЕНИЙ</b>\n\n"
                "• Привезём дополнительное средство и отмоем жир;"
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        elif data == "desc_extra_grilles":
            description = (
                "<b>ОКОННЫЕ РЕШЁТКИ</b>\n\n"
                "• Моем оконные решётки;"
            )
            await callback.message.edit_text(description, reply_markup=get_extra_services_kb(), parse_mode="HTML")
        else:
            # Обработка основных услуг (например, desc_1, desc_2, desc_3, desc_4)
            try:
                parts = data.split("_")
                print(f"Разбиваем callback_data: {parts}")
                if len(parts) != 2 or not parts[1].isdigit():
                    print(f"Некорректный формат callback_data: {data}")
                    await callback.message.edit_text(
                        "Ошибка: некорректный формат данных. Попробуйте снова.",
                        reply_markup=get_services_desc_kb()
                    )
                    return
                service_id = int(parts[1])
                print(f"Попытка получить услугу ID: {service_id}")
                db = SessionLocal()
                try:
                    service = db.query(Service).filter(Service.id == service_id).first()
                    print(f"Услуга найдена: {service.name if service else 'None'}")
                    if not service:
                        print("Услуга не найдена в базе данных")
                        await callback.message.edit_text(
                            "Услуга не найдена в базе данных.",
                            reply_markup=get_services_desc_kb(),
                            parse_mode="HTML"
                        )
                        return
                    if service.name == "Поддерживающая уборка":
                        description = (
                            "<b>ВЕСЬ ДОМ</b>\n\n"
                            "• Обеспыливаем и моем все поверхности мебели и интерьера на всей высоте;\n"
                            "• Протираем открытые полки, фоторамки, часы и другие предметы на всей высоте;\n"
                            "• Моем настенные светильники на всей высоте;\n"
                            "• Протираем трубы, радиаторы, розетки и выключатели;\n"
                            "• Протираем карнизы;\n"
                            "• Протираем кондиционер снаружи;\n"
                            "• Моем зеркала на полную высоту;\n"
                            "• Раскладываем вещи по местам;\n"
                            "• Меняем постельное бельё;\n"
                            "• Пылесосим полы, ковры и напольные покрытия (при наличии пылесоса);\n"
                            "• Пылесосим мягкую мебель (при наличии пылесоса);\n"
                            "• Протираем кожаную мебель;\n"
                            "• Моем полы и плинтусы;\n"
                            "• Протираем межкомнатные двери и дверные блоки;\n"
                            "• Выносим мусор, дезинфицируем корзину;\n"
                            "• Протираем входную дверь и моем под входным ковриком.\n\n"
                            "<b>КУХНЯ</b>\n\n"
                            "• Моем и дезинфицируем кухонные рабочие поверхности: фартук, столешницу;\n"
                            "• Моем кухонную плиту и стену над ней;\n"
                            "• Моем микроволновую печь внутри и снаружи;\n"
                            "• Протираем кухонные фасады на всю высоту кухонного гарнитура;\n"
                            "• Моем посуду (не более 15 минут);\n"
                            "• Моем кухонную технику снаружи (духовку, холодильник).\n\n"
                            "<b>ВАННАЯ КОМНАТА</b>\n\n"
                            "• Чистим и дезинфицируем сантехнику;\n"
                            "• Моем ванную и душевую кабину;\n"
                            "• Удаляем локально загрязнения на стенах на всей высоте.\n\n"
                            "<b>ЧТО МЫ НЕ ДЕЛАЕМ</b>\n\n"
                            "❌ НЕ моем окна (закажите дополнительную услугу «Мытьё окон»);\n"
                            "❌ НЕ проводим химчистку мебели и ковров (закажите дополнительную услугу «Химчистка»);\n"
                            "❌ НЕ моем хрустальные люстры и светильники;\n"
                            "❌ НЕ удаляем следы герметика и краски."
                        )
                        await callback.message.edit_text(description, reply_markup=get_services_desc_kb(), parse_mode="HTML")
                    elif service.name == "Генеральная уборка":
                        description = (
                            "<b>ВЕСЬ ДОМ</b>\n\n"
                            "• Обеспыливаем и моем все поверхности мебели и интерьера на всей высоте;\n"
                            "• Удаляем пыль со стен и потолков;\n"
                            "• Удаляем на всех поверхностях сложные загрязнения: известковый налёт, ржавчину, жир, водный камень;\n"
                            "• Удаляем парогенератором сильные загрязнения;\n"
                            "• Чистим парогенератором труднодоступные места;\n"
                            "• Моем мебель внутри, где убраны вещи с полок;\n"
                            "• Моем за мебелью, если её можно отодвинуть (НЕ отодвигаем крупногабаритную тяжёлую мебель);\n"
                            "• Моем настенные светильники на всей высоте;\n"
                            "• Моем потолочные светильники;\n"
                            "• Протираем открытые полки, фоторамки, часы и другие предметы на всей высоте;\n"
                            "• Протираем трубы, розетки, радиаторы и выключатели;\n"
                            "• Протираем карнизы;\n"
                            "• Протираем кондиционер снаружи;\n"
                            "• Моем зеркала на всю высоту;\n"
                            "• Раскладываем вещи по местам;\n"
                            "• Меняем постельное бельё;\n"
                            "• Пылесосим полы, ковры и напольные покрытия;\n"
                            "• Протираем кожаную мебель;\n"
                            "• Пылесосим под напольными коврами;\n"
                            "• Пылесосим мягкую мебель снаружи и внутри;\n"
                            "• Моем полы и плинтусы;\n"
                            "• Протираем межкомнатные двери и дверные блоки;\n"
                            "• Выносим мусор. Дезинфицируем корзину;\n"
                            "• Протираем входную дверь и моем под входным ковриком.\n\n"
                            "<b>КУХНЯ</b>\n\n"
                            "• Моем и дезинфицируем кухонные рабочие поверхности: фартук, столешницу;\n"
                            "• Моем кухонную плиту и стену над ней;\n"
                            "• Моем микроволновую печь снаружи и внутри;\n"
                            "• Протираем кухонные фасады на всю высоту кухонного гарнитура;\n"
                            "• Моем посуду (не более 30 минут);\n"
                            "• Моем кухонную технику снаружи и внутри (холодильник, духовку, если заказано).\n\n"
                            "<b>ВАННАЯ КОМНАТА</b>\n\n"
                            "• Чистим и дезинфицируем сантехнику;\n"
                            "• Моем ванную и душевую кабину;\n"
                            "• Удаляем сложные загрязнения на стенах и полу;\n"
                            "• Чистим швы плитки парогенератором.\n\n"
                            "<b>ЧТО МЫ НЕ ДЕЛАЕМ</b>\n\n"
                            "❌ НЕ моем окна (закажите дополнительную услугу «Мытьё окон»);\n"
                            "• НЕ проводим химчистку мебели и ковров;\n"
                            "❌ НЕ моем хрустальные люстры;\n"
                            "❌ НЕ удаляем строительные загрязнения (герметик, краску)."
                        )
                        await callback.message.edit_text(description, reply_markup=get_services_desc_kb(), parse_mode="HTML")
                    elif service.name == "Уборка после ремонта":
                        description = (
                            "<b>ВЕСЬ ДОМ</b>\n\n"
                            "• Обеспыливаем и моем все поверхности мебели и интерьера на всей высоте;\n"
                            "• Удаляем пыль со стен и потолков;\n"
                            "• Удаляем пыль от строительных работ;\n"
                            "• Удаляем на всех поверхностях сложные загрязнения: известковый налёт, ржавчину, жир, водный камень;\n"
                            "• Удаляем парогенератором сильные загрязнения;\n"
                            "• Чистим парогенератором труднодоступные места;\n"
                            "• Очищаем межплиточные швы от загрязнений в санузлах парогенератором;\n"
                            "• Отмываем следы цемента, клея и скотча;\n"
                            "• Моем мебель внутри, где убраны вещи с полок;\n"
                            "• Моем за мебелью, если её можно отодвинуть (НЕ отодвигаем крупногабаритную и тяжелую мебель);\n"
                            "• Моем настенные светильники на всей высоте;\n"
                            "• Моем потолочные светильники на всей высоте;\n"
                            "• Протираем открытые полки, фоторамки, часы и другие предметы на всей высоте;\n"
                            "• Протираем трубы, радиаторы, розетки и выключатели;\n"
                            "• Протираем карнизы;\n"
                            "• Протираем кондиционер снаружи;\n"
                            "• Моем зеркала на полную высоту;\n"
                            "• Раскладываем вещи по местам;\n"
                            "• Меняем постельное бельё;\n"
                            "• Пылесосим полы, ковры и напольные покрытия;\n"
                            "• Протираем кожаную мебель;\n"
                            "• Пылесосим под напольными коврами;\n"
                            "• Пылесосим мягкую мебель снаружи и внутри;\n"
                            "• Моем полы и плинтусы;\n"
                            "• Протираем межкомнатные двери и дверные блоки;\n"
                            "• Выносим мусор и дезинфицируем корзину;\n"
                            "• Убираем мелкие строительные отходы (не убираем крупный мусор и коробки);\n"
                            "• Протираем входную дверь и моем под входным ковриком.\n\n"
                            "<b>КУХНЯ</b>\n\n"
                            "• Моем и дезинфицируем кухонные рабочие поверхности: фартук, столешницу;\n"
                            "• Моем кухонную плиту и стену над ней;\n"
                            "• Моем микроволновую печь внутри и снаружи;\n"
                            "• Протираем кухонные фасады на всю высоту кухонного гарнитура;\n"
                            "• Моем посуду (не более 15 минут);\n"
                            "• Моем кухонную технику снаружи (духовку, холодильник);\n"
                            "• Моем кухонную технику внутри (духовку, холодильник - должен быть предварительно освобожден от содержимого и разморожен, либо просто освобожден, если не требуется мыть морозилку).\n\n"
                            "<b>ВАННАЯ КОМНАТА</b>\n\n"
                            "• Чистим и дезинфицируем сантехнику;\n"
                            "• Моем ванную и душевую кабину;\n"
                            "• Удаляем полностью загрязнения на стенах на всей высоте;\n"
                            "• Очищаем межплиточные швы от загрязнений в санузлах парогенератором.\n\n"
                            "<b>ЧТО МЫ НЕ ДЕЛАЕМ</b>\n\n"
                            "❌ НЕ моем окна (закажите дополнительную услугу «Мытьё окон»);\n"
                            "❌ НЕ проводим химчистку мебели и ковров (закажите дополнительную услугу «Химчистка»);\n"
                            "❌ НЕ моем хрустальные люстры и светильники;\n"
                            "❌ НЕ удаляем следы герметика и краски."
                        )
                        await callback.message.edit_text(description, reply_markup=get_services_desc_kb(), parse_mode="HTML")
                    elif service.name == "Мытьё окон":
                        description = (
                            "<b>МЫТЬЁ ОКОН</b>\n\n"
                            "• Моем стекла без разводов с двух сторон (глухие окна - только с внутренней стороны);\n"
                            "• Удаляем следы скотча;\n"
                            "• Очищаем москитные сетки;\n"
                            "• Моем рамы;\n"
                            "• Протираем отливы;\n"
                            "• Моем подоконник.\n\n"
                            "<b>ЧТО МЫ НЕ ДЕЛАЕМ</b>\n\n"
                            "❌ НЕ моем жалюзи;\n"
                            "❌ НЕ оттираем известковый налёт;\n"
                            "❌ НЕ моем оконные решётки."
                        )
                        await callback.message.edit_text(description, reply_markup=get_services_desc_kb(), parse_mode="HTML")
                    else:
                        description_text = service.description.replace('<br>', '\n\n') if service.description else "Описание отсутствует."
                        description = f"<b>{service.name}</b>\n\n{description_text}"
                        await callback.message.edit_text(description, reply_markup=get_services_desc_kb(), parse_mode="HTML")
                finally:
                    if db:
                        try:
                            print("Закрываем сессию базы данных")
                            db.close()
                        except Exception as e:
                            print(f"Ошибка при закрытии сессии базы данных: {str(e)}")
            except Exception as e:
                print(f"Ошибка при парсинге или запросе услуги: {str(e)}")
                try:
                    await callback.message.edit_text(
                        "Ошибка при обработке услуги. Попробуйте снова.",
                        reply_markup=get_services_desc_kb()
                    )
                except Exception as edit_error:
                    print(f"Ошибка редактирования сообщения: {str(edit_error)}")
                    await callback.message.answer(
                        "Ошибка при обработке услуги. Попробуйте снова.",
                        reply_markup=get_services_desc_kb()
                    )
    except Exception as e:
        print(f"Внешняя ошибка в show_service_description: {str(e)}")
        try:
            await callback.message.edit_text(
                "Произошла ошибка. Попробуйте позже.",
                reply_markup=get_main_inline_kb()
            )
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer(
                "Произошла ошибка. Попробуйте позже.",
                reply_markup=get_main_inline_kb()
            )
    await callback.answer()

# Обработчик кнопки "Назад" для возврата к описанию услуг
@router.callback_query(F.data == "back_to_services_desc")
async def back_to_services_desc(callback: CallbackQuery):
    print("Нажата 'Назад' к описанию услуг, User ID:", callback.from_user.id)
    try:
        services = get_services()
        print(f"Услуги из базы в back_to_services_desc: {[s.name for s in services]}")
        if not services:
            await callback.message.edit_text("Нет доступных услуг в базе данных.", reply_markup=get_main_inline_kb())
            return
        await callback.message.edit_text("Выберите услугу для описания:", reply_markup=get_services_desc_kb())
    except Exception as e:
        print(f"Ошибка в back_to_services_desc: {str(e)}")
        try:
            await callback.message.edit_text("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
    await callback.answer()

# Обработчик кнопки "Мои баллы"
@router.message(F.text == "Мои баллы")
async def my_points(message: Message):
    print("Нажата 'Мои баллы', User ID:", message.from_user.id)
    try:
        user = get_user(message.from_user.id)
        if user:
            await message.answer(f"У вас {user.points} баллов.", reply_markup=get_main_menu(message.from_user.id))
        else:
            await message.answer("Ошибка: пользователь не найден.", reply_markup=get_main_menu(message.from_user.id))
    except Exception as e:
        print(f"Ошибка в my_points: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))

# Обработчик кнопки "Мои заказы"
@router.message(F.text == "Мои заказы")
async def my_orders(message: Message):
    print("Нажата 'Мои заказы', User ID:", message.from_user.id)
    try:
        user = get_user(message.from_user.id)
        if not user:
            await message.answer("Ошибка: пользователь не найден.", reply_markup=get_main_menu(message.from_user.id))
            return
        orders = get_user_orders(user.id)
        if not orders:
            await message.answer("У вас нет заказов.", reply_markup=get_main_menu(message.from_user.id))
            return
        orders_str = "\n".join([
            f"Заказ #{o.id}\n"
            f"Услуга: {o.service.name}\n"
            f"Метраж: {json.loads(o.params)['meter']} м²\n"
            f"Доп. услуги: {format_extra_services(json.loads(o.params))}\n"
            f"Дата и время: {json.loads(o.params)['date']} {json.loads(o.params)['time']}\n"
            f"Адрес: {json.loads(o.params)['address']}\n"
            f"Цена: {o.total_price} руб.\n"
            f"Статус: {o.status}\n"
            for o in orders
        ])
        await message.answer(f"Ваши заказы:\n\n{orders_str}", reply_markup=get_main_menu(message.from_user.id), parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка в my_orders: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))

# Обработчик кнопки "Админ-панель"
@router.message(F.text == "Админ-панель")
async def admin_panel(message: Message):
    print("Нажата 'Админ-панель', User ID:", message.from_user.id)
    if message.from_user.id != 610269479:
        print("Доступ запрещён: неверный User ID")
        await message.answer("Доступ запрещён.", reply_markup=get_main_menu(message.from_user.id))
        return
    try:
        await message.answer("Админ-панель:", reply_markup=get_admin_panel_kb())
    except Exception as e:
        print(f"Ошибка в admin_panel: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))

# Обработчик кнопок админ-панели
@router.callback_query(F.data.startswith("admin_"))
async def handle_admin_panel(callback: CallbackQuery):
    print(f"Админ-панель, Callback data: {callback.data}, User ID: {callback.from_user.id}")
    if callback.from_user.id != 610269479:
        print("Доступ запрещён: неверный User ID")
        await callback.message.edit_text("Доступ запрещён.", reply_markup=get_main_inline_kb())
        await callback.answer()
        return
    try:
        data = callback.data
        db = SessionLocal()
        try:
            if data == "admin_active_orders":
                orders = db.query(Order).filter(Order.status != "completed").all()
                title = "Действующие заказы"
            elif data == "admin_completed_orders":
                orders = db.query(Order).filter(Order.status == "completed").all()
                title = "Выполненные заказы"
            elif data == "admin_all_orders":
                orders = get_all_orders()
                title = "Все заказы"
            else:
                print(f"Некорректный callback_data: {data}")
                await callback.message.edit_text("Ошибка: некорректный выбор.", reply_markup=get_admin_panel_kb())
                await callback.answer()
                return

            print(f"Получено заказов: {len(orders)}")
            if not orders:
                await callback.message.edit_text(f"{title}: нет заказов.", reply_markup=get_admin_panel_kb())
            else:
                orders_str = "\n".join([
                    f"Заказ #{o.id}\n"
                    f"Услуга: {o.service.name}\n"
                    f"Метраж: {json.loads(o.params)['meter']} м²\n"
                    f"Доп. услуги: {format_extra_services(json.loads(o.params))}\n"
                    f"Дата и время: {json.loads(o.params)['date']} {json.loads(o.params)['time']}\n"
                    f"Адрес: {json.loads(o.params)['address']}\n"
                    f"Цена: {o.total_price} руб.\n"
                    f"Статус: {o.status}\n"
                    for o in orders
                ])
                await callback.message.edit_text(f"<b>{title}</b>\n\n{orders_str}", reply_markup=get_admin_panel_kb(), parse_mode="HTML")
        finally:
            db.close()
    except Exception as e:
        print(f"Ошибка в handle_admin_panel: {str(e)}")
        try:
            await callback.message.edit_text("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
    await callback.answer()

# Обработчик выбора услуги
@router.message(F.text == "Заказать услугу")
async def order_service(message: Message, state: FSMContext):
    print("Нажата 'Заказать услугу', User ID:", message.from_user.id)
    try:
        services = get_services()
        print(f"Услуги из базы в order_service: {[s.name for s in services]}")
        if not services:
            await message.answer("Нет доступных услуг в базе данных.", reply_markup=get_main_menu(message.from_user.id))
            return
        services_kb = get_services_kb()
        if not services_kb:
            await message.answer("Ошибка при создания клавиатуры услуг.", reply_markup=get_main_menu(message.from_user.id))
            return
        await message.answer("Выберите услугу:", reply_markup=services_kb)
        await state.set_state(OrderStates.waiting_service)
    except Exception as e:
        print(f"Ошибка в order_service: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))

# Обработчик выбора основной услуги
@router.callback_query(F.data.startswith("service_"))
async def select_service(callback: CallbackQuery, state: FSMContext):
    print("Выбрана услуга, Callback data:", callback.data)
    try:
        service_id = int(callback.data.split("_")[1])
        db = SessionLocal()
        try:
            service = db.query(Service).filter(Service.id == service_id).first()
            print(f"Запрошена услуга ID: {service_id}, найдена: {service.name if service else 'None'}")
            if not service:
                await callback.message.edit_text("Услуга не найдена.", reply_markup=get_main_inline_kb())
                await state.clear()
                return
            await state.update_data(service_id=service_id)
            await callback.message.edit_text(f"Вы выбрали: {service.name}\nВведите метраж (в м², например, 50):")
            await state.set_state(OrderStates.waiting_meter)
        finally:
            db.close()
    except Exception as e:
        print(f"Ошибка в select_service: {str(e)}")
        try:
            await callback.message.edit_text("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
        await state.clear()
    await callback.answer()

# Обработчик ввода метража
@router.message(OrderStates.waiting_meter)
async def input_meter(message: Message, state: FSMContext):
    print(f"Введён текст для метража: '{message.text}', User ID: {message.from_user.id}")
    current_state = await state.get_state()
    print(f"Текущее состояние: {current_state}")
    try:
        meter_text = message.text.strip()
        if not meter_text.isdigit():
            await message.answer("Пожалуйста, введите число (например, 50):")
            return
        meter = int(meter_text)
        if meter <= 0:
            await message.answer("Метраж должен быть больше 0. Попробуйте снова.")
            return
        await state.update_data(meter=meter)
        await message.answer(
            "Выберите дополнительные услуги (можно выбрать несколько):",
            reply_markup=get_extra_services_selection_kb()
        )
        await state.set_state(OrderStates.waiting_extra_services)
    except Exception as e:
        print(f"Ошибка в input_meter: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_menu(message.from_user.id))
        await state.clear()

# Обработчик выбора дополнительных услуг
@router.callback_query(OrderStates.waiting_extra_services)
async def select_extra_services(callback: CallbackQuery, state: FSMContext):
    print("Выбор доп. услуг, Callback data:", callback.data)
    try:
        user_data = await state.get_data()
        selected_services = user_data.get('extra_services', {})
        data = callback.data
        if data == "extra_continue":
            zero_qty_services = [s for s, qty in selected_services.items() if qty == 0]
            if zero_qty_services:
                service_key = zero_qty_services[0]
                await state.update_data(current_extra_service=service_key)
                unit = EXTRA_SERVICES_PRICES[service_key]['unit']
                await callback.message.edit_text(
                    f"Введите количество для '{EXTRA_SERVICES_PRICES[service_key]['name']}' (в {unit}ах, например, 2):"
                )
                await state.set_state(OrderStates.waiting_extra_quantity)
            else:
                await callback.message.edit_text("Выберите дату:", reply_markup=await SimpleCalendar().start_calendar())
                await state.set_state(OrderStates.waiting_date)
        elif data == "extra_none":
            await state.update_data(extra_services={})
            await callback.message.edit_text("Выберите дату:", reply_markup=await SimpleCalendar().start_calendar())
            await state.set_state(OrderStates.waiting_date)
        else:
            service_key = data.split("_")[1]
            if service_key in selected_services:
                selected_services.pop(service_key)
            else:
                selected_services[service_key] = 0
            await state.update_data(extra_services=selected_services)
            await callback.message.edit_text(
                "Выберите дополнительные услуги (можно выбрать несколько):",
                reply_markup=get_extra_services_selection_kb(list(selected_services.keys()))
            )
    except Exception as e:
        print(f"Ошибка в select_extra_services: {str(e)}")
        try:
            await callback.message.edit_text("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
        await state.clear()
    await callback.answer()

# Обработчик ввода количества для доп. услуг
@router.message(OrderStates.waiting_extra_quantity, F.text.isdigit())
async def input_extra_quantity(message: Message, state: FSMContext):
    print("Введено количество:", message.text)
    try:
        quantity = int(message.text)
        if quantity < 0:
            await message.answer("Количество не может быть отрицательным. Попробуйте снова.")
            return
        user_data = await state.get_data()
        current_service = user_data.get('current_extra_service')
        selected_services = user_data.get('extra_services', {})
        
        if current_service not in selected_services:
            await message.answer("Ошибка: услуга не выбрана. Начните заново.", reply_markup=get_main_menu(message.from_user.id))
            await state.clear()
            return
        
        selected_services[current_service] = quantity
        await state.update_data(extra_services=selected_services)
        
        remaining_services = [s for s in selected_services.keys() if s != current_service and selected_services[s] == 0]
        if remaining_services:
            next_service = remaining_services[0]
            await state.update_data(current_extra_service=next_service)
            unit = EXTRA_SERVICES_PRICES[next_service]['unit']
            await message.answer(f"Введите количество для '{EXTRA_SERVICES_PRICES[next_service]['name']}' (в {unit}ах, например, 2):")
            await state.set_state(OrderStates.waiting_extra_quantity)
        else:
            await state.update_data(current_extra_service=None)
            await message.answer("Выберите дату:", reply_markup=await SimpleCalendar().start_calendar())
            await state.set_state(OrderStates.waiting_date)
    except Exception as e:
        print(f"Ошибка в input_extra_quantity: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_menu(message.from_user.id))
        await state.clear()

# Обработчик некорректного ввода количества
@router.message(OrderStates.waiting_extra_quantity)
async def invalid_extra_quantity(message: Message, state: FSMContext):
    print("Некорректное количество:", message.text)
    user_data = await state.get_data()
    current_service = user_data.get('current_extra_service')
    unit = EXTRA_SERVICES_PRICES[current_service]['unit'] if current_service else "единицах"
    await message.answer(f"Пожалуйста, введите число (например, 2) для '{EXTRA_SERVICES_PRICES[current_service]['name']}' (в {unit}ах):")

# Обработчик выбора даты
@router.callback_query(OrderStates.waiting_date, SimpleCalendarCallback.filter())
async def input_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    print("Обработка выбора даты, Callback data:", callback_data)
    try:
        selected, date = await SimpleCalendar().process_selection(callback, callback_data)
        if not selected:
            print("Дата не выбрана, продолжаем показ календаря")
            return
        current_date = datetime.now().date()
        if date.date() < current_date:
            await callback.message.edit_text("Нельзя выбрать дату раньше сегодняшнего дня. Попробуйте снова:", reply_markup=await SimpleCalendar().start_calendar())
            print("Выбрана прошедшая дата:", date.date())
            return
        date_str = date.strftime("%Y-%m-%d")
        print(f"Выбрана дата: {date_str}")
        await state.update_data(date=date_str)
        time_kb = await get_time_keyboard(state)
        if not time_kb:
            await callback.message.edit_text(
                "На выбранную дату нет доступных временных интервалов. Выберите другую дату:",
                reply_markup=await SimpleCalendar().start_calendar()
            )
            print("Нет доступных интервалов времени для даты:", date_str)
            return
        await callback.message.edit_text("Выберите время:", reply_markup=time_kb)
        await state.set_state(OrderStates.waiting_time)
    except Exception as e:
        print(f"Ошибка в input_date: {str(e)}")
        try:
            await callback.message.edit_text("Произошла ошибка при выборе даты. Попробуйте снова:", reply_markup=await SimpleCalendar().start_calendar())
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка при выборе даты. Попробуйте снова:", reply_markup=await SimpleCalendar().start_calendar())
        await state.clear()
    await callback.answer()

# Функция для создания клавиатуры времени
async def get_time_keyboard(state: FSMContext):
    print("Создание клавиатуры времени")
    try:
        data = await state.get_data()
        selected_date = datetime.strptime(data['date'], "%Y-%m-%d").date()
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        print(f"Текущее время: {current_time}, Выбрана дата: {selected_date}")
        
        times = []
        start_hour = 9
        end_hour = 19
        for hour in range(start_hour, end_hour + 1):
            times.append(f"{hour:02d}:00")
            if hour < end_hour:
                times.append(f"{hour:02d}:30")
        
        if selected_date == current_date:
            min_time = (datetime.now() + timedelta(hours=3)).time()
            print(f"Минимальное время для сегодня: {min_time}")
            filtered_times = [
                t for t in times
                if time(int(t.split(":")[0]), int(t.split(":")[1])) >= min_time and time(int(t.split(":")[0]), int(t.split(":")[1])) <= time(19, 0)
            ]
            times = filtered_times
            print(f"Отфильтрованные интервалы: {times}")
        
        if not times:
            print("Нет доступных интервалов времени")
            buttons = [[InlineKeyboardButton(text="Назад к выбору даты", callback_data="back_to_date")]]
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        
        buttons = [[InlineKeyboardButton(text=t, callback_data=f"time_{t}")] for t in times]
        buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_date")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        print(f"Клавиатура времени создана: {[btn[0].text for btn in buttons]}")
        return kb
    except Exception as e:
        print(f"Ошибка в get_time_keyboard: {str(e)}")
        return None

# Обработчик выбора времени
@router.callback_query(OrderStates.waiting_time, F.data.startswith("time_"))
async def input_time(callback: CallbackQuery, state: FSMContext):
    print("Выбрано время, Callback data:", callback.data)
    try:
        time_str = callback.data.split("_")[1]
        if not time_str or len(time_str.split(":")) != 2:
            print(f"Некорректный формат времени: {time_str}")
            await callback.message.edit_text("Ошибка: некорректное время. Попробуйте снова:", reply_markup=await get_time_keyboard(state))
            return
        await state.update_data(time=time_str)
        await callback.message.edit_text(f"Выбрано время: {time_str}\n\nВведите адрес (например, ул. Ленина 1):", parse_mode="HTML")
        await state.set_state(OrderStates.waiting_address)
    except Exception as e:
        print(f"Ошибка в input_time: {str(e)}")
        time_kb = await get_time_keyboard(state)
        try:
            await callback.message.edit_text("Произошла ошибка при выборе времени. Попробуйте снова:", reply_markup=time_kb)
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка при выборе времени. Попробуйте снова:", reply_markup=time_kb)
        await state.clear()
    await callback.answer()

# Обработчик кнопки "Назад" к выбору даты
@router.callback_query(OrderStates.waiting_time, F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    print("Нажата 'Назад' к выбору даты")
    try:
        await callback.message.edit_text("Выберите дату:", reply_markup=await SimpleCalendar().start_calendar())
        await state.set_state(OrderStates.waiting_date)
    except Exception as e:
        print(f"Ошибка в back_to_date: {str(e)}")
        try:
            await callback.message.edit_text("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_inline_kb())
        except Exception as edit_error:
            print(f"Ошибка редактирования сообщения: {str(edit_error)}")
            await callback.message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_inline_kb())
        await state.clear()
    await callback.answer()

# Обработчик ввода адреса
@router.message(OrderStates.waiting_address)
async def input_address(message: Message, state: FSMContext):
    print("Введён адрес:", message.text)
    try:
        address = message.text.strip()
        if not address:
            await message.answer("Адрес не может быть пустым. Попробуйте снова.")
            return
        await state.update_data(address=address)
        data = await state.get_data()
        db = SessionLocal()
        try:
            service = db.query(Service).filter(Service.id == data['service_id']).first()
            print(f"Проверяем услугу для заказа, ID: {data['service_id']}, найдена: {service.name if service else 'None'}")
            if not service:
                await message.answer("Ошибка: услуга не найдена.", reply_markup=get_main_menu(message.from_user.id))
                await state.clear()
                return
            base_price = service.base_price + service.price_per_meter * data['meter']
            extra_services = data.get('extra_services', {})
            extra_price = sum(EXTRA_SERVICES_PRICES[es]["price"] * qty for es, qty in extra_services.items() if qty > 0)
            total_price = base_price + extra_price
            await state.update_data(total_price=total_price)
            extra_services_str = ", ".join(
                [f"{EXTRA_SERVICES_PRICES[es]['name']} ({qty} {EXTRA_SERVICES_PRICES[es]['unit']}): {qty * EXTRA_SERVICES_PRICES[es]['price']} руб"
                 for es, qty in extra_services.items() if qty > 0]
            ) if extra_services else "Нет"
            await message.answer(
                f"<b>Итог:</b>\n\n"
                f"Основная услуга: {service.name}\n"
                f"Метраж: {data['meter']} м²\n"
                f"Доп. услуги: {extra_services_str}\n"
                f"Дата: {data['date']}\n"
                f"Время: {data['time']}\n"
                f"Адрес: {data['address']}\n"
                f"Цена: {total_price} руб.\n\n"
                f"Напишите 'Да' для подтверждения заказа.",
                parse_mode="HTML"
            )
            await state.set_state(OrderStates.waiting_confirm)
        finally:
            db.close()
    except Exception as e:
        print(f"Ошибка в input_address: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте снова.", reply_markup=get_main_menu(message.from_user.id))
        await state.clear()

# Обработчик подтверждения заказа
@router.message(OrderStates.waiting_confirm, F.text.lower() == "да")
async def confirm_order(message: Message, state: FSMContext):
    print("Подтверждение заказа, User ID:", message.from_user.id)
    try:
        data = await state.get_data()
        user = get_user(message.from_user.id)
        if not user:
            await message.answer("Ошибка: пользователь не найден.", reply_markup=get_main_menu(message.from_user.id))
            await state.clear()
            return
        params = json.dumps({
            "meter": data['meter'],
            "date": data['date'],
            "time": data['time'],
            "address": data['address'],
            "extra_services": data.get('extra_services', {})
        })
        order_id = create_order(user.id, data['service_id'], params, data['total_price'])
        if order_id:
            await message.answer(f"Заказ #{order_id} создан! Цена: {data['total_price']} руб.", reply_markup=get_main_menu(message.from_user.id))
        else:
            await message.answer("Ошибка при создании заказа. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))
        await state.clear()
    except Exception as e:
        print(f"Ошибка в confirm_order: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(message.from_user.id))
        await state.clear()

# Обработчик кнопки "Назад" в главное меню
@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    print("Нажата 'Назад', User ID:", callback.from_user.id)
    try:
        await state.clear()
        await callback.message.edit_text("Главное меню:", reply_markup=get_main_inline_kb())
    except Exception as e:
        print(f"Ошибка в back_main: {str(e)}")
        if "message is not modified" in str(e):
            await callback.message.answer("Главное меню:", reply_markup=get_main_menu(callback.from_user.id))
        else:
            try:
                await callback.message.edit_text("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_inline_kb())
            except Exception as edit_error:
                print(f"Ошибка редактирования сообщения: {str(edit_error)}")
                await callback.message.answer("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()