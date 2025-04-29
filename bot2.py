import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Данные об архитектурных объектах
arch_objects = {
    "stalinckiy_ampir": {
        "name": "Жилые дома сталинской эпохи",
        "description": "Типичный пример сталинского ампира с массивными карнизами и симметричным фасадом.",
        "year": "1960-е",
        "address": "Бульварная, 8",
        "photo": "https://autotravel.ru/phalbum/91512/192.jpg"
    },
    "dom_sovetov": {
        "name": "Жилой многоквартирный дом на улице Герцена",
        "description": "Здание в стиле конструктивизма, где размещались городские власти.",
        "year": "1960-е",
        "address": "ул. Герцена, 39",
        "photo": "https://rybinsklift.ru/images/news/komfort/120723.jpg"
    },
    "dvorec_kultury": {
        "name": "Дворец культуры «Авиатор»",
        "description": "Построен в стиле сталинского неоклассицизма с колоннами и барельефами. Внутри – просторный зал, лепнина и советские мозаики.",
        "year": "1950-е",
        "address": "ул. Кирова, 12",
        "photo": "https://goru.travel/storage/app/uploads/public/5ac/339/048/5ac339048a981087790283.jpg"
    }
}


def get_main_menu_keyboard():
    """Возвращает клавиатуру главного меню"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Дом Советов", callback_data="dom_sovetov")],
        [InlineKeyboardButton("Жилой комплекс", callback_data="stalinckiy_ampir")],
        [InlineKeyboardButton("Дворец культуры", callback_data="dvorec_kultury")],
        [InlineKeyboardButton("О проекте", callback_data="about")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - главное меню"""
    text = "Добро пожаловать в бот-гид по советской архитектуре Рыбинска!\nВыберите объект для просмотра:"

    try:
        if update.message:
            await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
        else:
            await update.callback_query.edit_message_text(text, reply_markup=get_main_menu_keyboard())
    except BadRequest as e:
        logger.warning(f"Не удалось отредактировать сообщение: {e}")
        await update.callback_query.message.reply_text(text, reply_markup=get_main_menu_keyboard())


async def show_architecture_object(update: Update, context: ContextTypes.DEFAULT_TYPE, object_id: str):
    """Показывает информацию об архитектурном объекте"""
    query = update.callback_query
    await query.answer()

    obj = arch_objects[object_id]
    message_text = (
        f"🏛 <b>{obj['name']}</b>\n\n"
        f"<i>Годы постройки:</i> {obj['year']}\n"
        f"<i>Адрес:</i> {obj['address']}\n\n"
        f"{obj['description']}"
    )

    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("← Назад к выбору", callback_data="back_to_menu")]
    ])

    try:
        await context.bot.send_photo(
            chat_id=query.message.chat.id,
            photo=obj['photo'],
            caption=message_text,
            parse_mode='HTML',
            reply_markup=back_button
        )
        try:
            await query.message.delete()
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        try:
            await query.edit_message_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=back_button
            )
        except BadRequest:
            await query.message.reply_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=back_button
            )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    if query.data == "about":
        try:
            await query.edit_message_text(
                "Этот бот создан для знакомства с советской архитектурой Рыбинска.\n"
                "Здесь собраны наиболее значимые образцы архитектуры советского периода.\n\n"
                "Для продолжения нажмите /start",
                reply_markup=None
            )
        except BadRequest:
            await query.message.reply_text(
                "Этот бот создан для знакомства с советской архитектурой Рыбинска.\n"
                "Здесь собраны наиболее значимые образцы архитектуры советского периода.\n\n"
                "Для продолжения нажмите /start"
            )
    elif query.data == "back_to_menu":
        await start(update, context)
    elif query.data in arch_objects:
        await show_architecture_object(update, context, query.data)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    await update.message.reply_text(
        "Используйте команду /start для начала работы с ботом.\n"
        "Выберите интересующий вас объект советской архитектуры Рыбинска из списка."
    )


def main() -> None:
    """Запуск бота"""
    # Получаем токен из переменных окружения
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.error("Токен не найден! Проверьте .env файл")
        return

    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запускается...")
    application.run_polling()


if __name__ == "__main__":
    main()