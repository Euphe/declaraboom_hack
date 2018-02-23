import logging
from .queries import get_query_list, run_query, QueryFailureError, get_declarator_persons
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup

logger = logging.getLogger(__name__)


NAME_INPUT, ARG_INPUT, VOTE, SEARCH = range(4)


class Bot:
    def __init__(self, api_key):
        self._api_key = api_key

        self.updater = Updater(api_key)
        self.updater.dispatcher.add_error_handler(self.error_handler)

    def add_conversation_handler(self, handler):
        self.updater.dispatcher.add_handler(handler)

    def add_command_handlers(self, command_handlers):
        for command, handler in command_handlers:
            self.updater.dispatcher.add_handler(CommandHandler(command, handler, pass_user_data=True))

    def add_conversation_handlers(self, handlers):
        for handler in handlers:
            self.updater.dispatcher.add_handler(handler)

    def start(self):
        self.updater.start_polling()
        self.updater.idle()

    @staticmethod
    def error_handler(bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)


def not_recognized_callback(bot, update, *args, **kwargs):
    text = "Я не понял тебя. Попробуй ещё раз или введи /cancel и начни заново."
    update.message.reply_text(text)


def help_callback(bot, update, *args, **kwargs):
    text = "/query осуществляет поисковый запрос, бот всё объяснит.\n/cancel или текст \"отмена\" сбрасывает текущий запрос."
    update.message.reply_text(text)


def start_callback(bot, update, *args, **kwargs):
    start_text = 'Привет! Я бот с хакатона Декларабум.\nЕсли запутаешься пиши /help.\nСкорее всего тебе нужна команда /query'
    update.message.reply_text(start_text)


def query_callback(bot, update, user_data=None, *args, **kwargs):
    if user_data:
        user_data.clear()
    text = 'Введи ФИО человека, например `Иванов Иван Иванович`'

    update.message.reply_text(text)
    return NAME_INPUT


def cancel_callback(bot, update, user_data):
    text= "Ок, я все отменил"
    user_data.clear()
    update.message.reply_text(text)
    return ConversationHandler.END


def name_input_callback(bot, update, user_data):
    user_data['query_text'] = update.message.text
    queries = ", ".join(get_query_list())
    text= f'Отлично, теперь введи что хочешь искать.\nДоступные запросы: {queries}'
    update.message.reply_text(text)
    return ARG_INPUT


def arg_input_callback(bot, update, user_data):
    user_data['query_method'] = update.message.text
    text= 'Поищу...'
    update.message.reply_text(text)
    try:
        query_result, collisions = run_query(user_data['query_method'], user_data['query_text'])
    except QueryFailureError:
        update.message.reply_text(f'Произошла ошибка при обработке запроса:\n{e}')
        return ConversationHandler.END
    update.message.reply_text(query_result)

    data = []
    for i, collision in enumerate(collisions):
        data.append(f'{i+1}. {collision["description"]}')

    if data:
        update.message.reply_text('\n'.join(data))

    update.message.reply_text('Напиши номер коллизии, которую ты считаешь истинной.\nНапиши 0, если они все неверны.')
    return VOTE


def vote_callback(bot, update, user_data):
    user_data['vote'] = update.message.text
    import random
    votes_total = random.randint(0, 50)
    percentage_for = random.randint(0, 100)
    text = f'Спасибо за твой голос!\n{percentage_for}% проголсоовали так же (из {votes_total} голосов)'
    update.message.reply_text(text)
    return ConversationHandler.END


def search_callback(bot, update, user_data=None, args=None):
    if not args or len(args) < 2:
        update.message.reply_text("Нужно ввести как минимум два слова: фамилию и имя")
    update.message.reply_text(f'Ищу "{" ".join(args)}"')
    words = args
    name, position = ' '.join(words[:3]),' '.join(words[3:])

    persons = get_declarator_persons(name, position, full_output=False)

    if not persons:
        update.message.reply_text('Никто не подходит под запрос, ищи ещё')
    elif len(persons) > 1:
        data = []
        for person in persons:
            data.append(f'{person["name"]} {person["position"]}')

        update.message.reply_text('Я нашел таких людей подходящих под запрос:\n' + '\n'.join(data))
        keyboard = [[f'/search {person["name"]} {person["position"]}'] for person in persons]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text('Выбери одного из них', reply_markup=markup)
    else:
        person = persons[0]
        user_data['person'] = person
        update.message.reply_text(f'Теперь твой покемон: {person["name"]} {person["position"]}. Иди разузнай про него что-то через /query')
        return ARG_INPUT
    return ConversationHandler.END

def make_conversation_handler():
    query_list = get_query_list()
    query_handlers = [ RegexHandler(f'^(?u){query}', arg_input_callback, pass_user_data=True) for query in query_list ]

    command_handlers = [
        ('help', help_callback),
        ('cancel', cancel_callback),
        ('query', query_callback)
    ]
    fallbacks = [CommandHandler(command, handler, pass_user_data=True) for command, handler in command_handlers]

    fallbacks.append(RegexHandler(r'.+', not_recognized_callback, pass_user_data=True))
    query_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_callback, pass_user_data=True),
            CommandHandler('query', query_callback, pass_user_data=True),
            CommandHandler('search', search_callback, pass_user_data=True, pass_args=True),
        ],

        states={
            NAME_INPUT: [RegexHandler(r'^(?u)\w+\s\w+\s\w+$', name_input_callback, pass_user_data=True)],
            ARG_INPUT: query_handlers,
            VOTE: [RegexHandler(r'^(?ui)[0-9]$', vote_callback, pass_user_data=True)],
            SEARCH: [CommandHandler('search', search_callback, pass_user_data=True)]
        },

        fallbacks=fallbacks
    )
    return query_conversation_handler


def create_bot(api_key):
    bot = Bot(api_key)

    conversation_handlers = [
        make_conversation_handler(),
    ]
    bot.add_conversation_handlers(conversation_handlers)
    return bot
