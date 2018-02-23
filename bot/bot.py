import logging
from .query import query
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler


logger = logging.getLogger(__name__)


class Bot:
    def __init__(self, api_key):
        self._api_key = api_key

        self.updater = Updater(api_key)
        self.updater.dispatcher.add_error_handler(self.error_handler)

    def add_conversation_handler(self, handler):
        self.updater.dispatcher.add_handler(handler)

    def add_command_handlers(self, command_handlers):
        for command, handler in command_handlers:
            self.updater.dispatcher.add_handler(CommandHandler(command, handler))

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



def start_command_callback(bot, update):
    start_text = 'Привет! Я бот с хакатона Декларабум. Тебе нужна команда /query'
    update.message.reply_text(start_text)

def query_command_callback(bot, update, user_data):
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
    text= 'Отлично, теперь введи что хочешь искать. Например "инн"'
    update.message.reply_text(text)
    return ARG_INPUT

def arg_input_callback(bot, update, user_data):
    user_data['query_method'] = update.message.text
    text= 'Поищу...'
    update.message.reply_text(text)
    try:
        query_result = query(user_data['query_method'], user_data['query_text'])

        update.message.reply_text(query_result)

        update.message.reply_text('Ты считаешь это значимая коллизия?')
    except Exception as e:
        update.message.reply_text(f'Произошла ошибка при обработке запроса: "{e}"')
    return VOTE

def vote_callback(bot, update, user_data):
    user_data['vote'] = update.message.text
    import random
    votes_total = random.randint(0, 50)
    percentage_for = random.randint(0, 100)
    text = f'Спасибо за твой голос!\n{percentage_for}% проголсоовали "ЗА" (из {votes_total} голосов)'
    update.message.reply_text(text)
    return ConversationHandler.END

NAME_INPUT, ARG_INPUT, VOTE = range(3)
query_conversation_handler = ConversationHandler(
    entry_points=[CommandHandler('query', query_command_callback, pass_user_data=True)],

    states={
        NAME_INPUT: [RegexHandler(r'(?u)\w+\s\w+\s\w+', name_input_callback, pass_user_data=True)],
        ARG_INPUT: [RegexHandler(r'(?u)\w+', arg_input_callback, pass_user_data=True)],
        VOTE: [RegexHandler(r'(?ui)(да|нет)', vote_callback, pass_user_data=True)],

    },

    fallbacks=[RegexHandler('^отмена$', cancel_callback, pass_user_data=True)]
)


def create_bot(api_key):
    bot = Bot(api_key)

    command_handlers = [
        ('start', start_command_callback)
    ]
    bot.add_command_handlers(command_handlers)

    conversation_handlers = [
        query_conversation_handler
    ]
    bot.add_conversation_handlers(conversation_handlers)
    return bot