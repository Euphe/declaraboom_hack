import os
import logging
import sqlalchemy
from telegram.ext import Updater, CommandHandler, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup
from .queries import get_query_list, run_query, QueryFailureError, get_declarator_persons
from .utils import prettify as pr
from .db import init_db, get_session, close_session
from .models import Vote


logger = logging.getLogger(__name__)
QUERY_START, ARG_INPUT, VOTE, SEARCH = range(4)


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
    text = "Сначала через /search выбери человека, для которого собираешься искать. Затем ищи информацию черещ /query.\n/cancel сбрасывает всё, если что."
    update.message.reply_text(text)


def start_callback(bot, update, *args, **kwargs):
    start_text = 'Привет! Я бот с хакатона Декларабум.\nЕсли что пиши /help.\nСкорее всего тебе нужна команда /search'
    update.message.reply_text(start_text)


def query_callback(bot, update, user_data=None, *args, **kwargs):
    if not 'person' in user_data or not user_data['person']:
        update.message.reply_text('Выбери цель через `/search`, потом приходи сюда.')
        return ConversationHandler.END
    queries = ", ".join(get_query_list())
    text = f'Твоя цель: {user_data["person"]["name"]}.\nВыбери, что ты хочешь искать.\nДоступные запросы: {queries}'
    keyboard = [[x] for x in get_query_list()]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text(text, reply_markup=markup)
    return ARG_INPUT


def cancel_callback(bot, update, user_data):
    text= "Ок, я все отменил"
    user_data.clear()
    update.message.reply_text(text)
    return ConversationHandler.END


def arg_input_callback(bot, update, user_data):
    user_data['query_method'] = pr(update.message.text)
    text= 'Ищу...'
    update.message.reply_text(text)
    try:
        query_result, collisions = run_query(user_data['query_method'], user_data['person'])
    except QueryFailureError as e:
        update.message.reply_text(f'Произошла ошибка при обработке запроса:\n{e}')
        return ConversationHandler.END
    update.message.reply_text(query_result)

    user_data['collision_options'] = collisions
    data = []
    for i, collision in enumerate(collisions):
        data.append(f'{i+1}. {collision["description"]}')

    if data:
        update.message.reply_text('\n'.join(data))
    if collisions:
        update.message.reply_text('Напиши номер коллизии, которую ты считаешь истинной.\nНапиши 0, если они все неверны.')
        return VOTE
    else:
        return ConversationHandler.END

@close_session
def vote_callback(bot, update, user_data):
    vote_num = int(pr(update.message.text))
    if vote_num != 0:
        try:
            user_data['vote'] = user_data['collision_options'][int(pr(update.message.text))-1]

            session = get_session()
            vote = Vote(
                voter_id=update.message.from_user.id,
                person_id=user_data["person"]["id"],
                param=user_data["vote"]["param"],
                param_value=user_data["vote"]['param_value']
            )
            session.add(vote)
            try:
                session.commit()
                update.message.reply_text('Спасибо, твой голос добавлен!')
            except sqlalchemy.exc.IntegrityError:
                update.message.reply_text('Ты уже голосовал здесь, жми 0')
                return

        except (ValueError, TypeError):
            update.message.reply_text('Введи номер коллизии или 0')
            return
    session = get_session()
    param = user_data['collision_options'][0]['param']
    votes = session.query(Vote).filter_by(person_id=user_data["person"]["id"], param=param).all()
    for collision in user_data['collision_options']:
        votes_for_collision = 0
        for vote in votes:
            if vote.param_value == collision["param_value"]:
                votes_for_collision += 1
        collision['votes'] = votes_for_collision

    data = ['Текущие голоса:\n']
    for i, collision in enumerate(user_data['collision_options']):
        data.append(f'{i+1}. {collision["description"]}: {collision["votes"]}')

    update.message.reply_text('\n'.join(data))
    return ConversationHandler.END


def search_callback(bot, update, user_data=None, args=None):
    if not args or len(args) < 2:
        update.message.reply_text("Нужно ввести как минимум фамилию и имя для начала поиска.\nНапример:\n`/search путин владимир владимирович`")
        return
    update.message.reply_text(f'Ищу "{" ".join(args)}"')
    args = pr(' '.join(args)).split(' ')
    words = [w for w in args]
    #print(words)
    name, position = ' '.join(words[:3]), ' '.join(words[3:])
    #print(name, position)
    persons = get_declarator_persons(name, position, full_output=False)

    if not persons:
        update.message.reply_text('Никто не подходит под запрос, ищи ещё')
    elif len(persons) > 1:
        data = []
        for person in persons:
            data.append(f'{person["name"]} {person["position"]}')

        update.message.reply_text('Я нашел таких людей подходящих под запрос:\n' + '\n'.join(data))
        keyboard = [[f'/search {person["name"]} {person["position"][0:40]}'] for person in persons]
        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        update.message.reply_text('Выбери одного из них', reply_markup=markup)
    else:
        person = persons[0]
        user_data['person'] = person
        update.message.reply_text(f'Теперь твоя цель: {person["name"]} {person["position"]}.\nРазузнай про него что-то через /query')
        return QUERY_START
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
            CommandHandler('help', help_callback),
            CommandHandler('query', query_callback, pass_user_data=True),
            CommandHandler('search', search_callback, pass_user_data=True, pass_args=True),
        ],

        states={
            QUERY_START: [RegexHandler(r'^(?u)\w+\s\w+\s\w+$', query_callback, pass_user_data=True)],
            ARG_INPUT: query_handlers,
            VOTE: [RegexHandler(r'^(?ui)[0-9]$', vote_callback, pass_user_data=True)],
            SEARCH: [CommandHandler('search', search_callback, pass_user_data=True)]
        },

        fallbacks=fallbacks
    )
    return query_conversation_handler


def create_bot(api_key):
    init_db(os.environ['SQLALCHEMY_DATABASE_URI'])

    bot = Bot(api_key)

    conversation_handlers = [
        make_conversation_handler(),
    ]
    bot.add_conversation_handlers(conversation_handlers)
    return bot
