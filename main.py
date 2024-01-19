import datetime
import os
import random
import time

import yadisk
from telebot import types
from telebot.async_telebot import AsyncTeleBot
import pygsheets
import settings
import asyncpg

with open('bot_token.txt') as f:
    BOT_TOKEN = f.readline()
bot = AsyncTeleBot(BOT_TOKEN)
client = pygsheets.authorize(service_account_file="projectcompanybot-cb02e829fad1.json")


class YPR:
    def __init__(self, user_id, username):
        self.username = username
        self.user_id = user_id
        self.condition = 0
        self.cities = []
        self.ans_zones = None
        '''
        conditions = {
            0: 
        }
        '''
        self.way = 0
        self.number_of_zone = 1  # Счётчик для номеров зон
        self.number_of_checks = 0  # Переменная хранящая кол-во проверок из БД
        self.spreadsht = ''
        self.worksht = ''
        self.flag_comment = False  # Суть: проверять, что юзер отправил фотку и следующее сообщение должно быть комментарием
        self.zones17 = ['', '', '', '', '', '',
                        '']  # Тут будут храниться URL на фотки зон, чтобы потом добавить в таблицу base_check
        self.comments = ['', '', '', '', '', '', '']  # Аналогично zones17
        self.user_choice = ['', '']  # Город, Адресс с которыми работает пользователь
        self.addresses = set()  # Будут записываться адреса выбранного города для последующей отловки сообщения пользователя


class SuperUser:
    def __init__(self, user_id, username):
        self.username = username
        self.user_id = user_id
        self.condition = 100
        self.city = ''  # Город, в который надо добавить адрес
        self.spreadsht = ''
        self.worksht = ''
        self.role = 0  # Роль, юзеров которых надо добавить в БД
        '''
        conditions = {
            100: Выбор из меню,
            101: Добавить город,
            102-103: Добавить адрес,
            104-105: Выдать права пользователю/добавить в базу,
            106: Выдать справку по суперюзер UI,
        }
        '''


class Inspector:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.number_of_zone = 1
        self.condition = 200
        '''
        conditions = {
            200: Ожидание/без проверки
            201: В режиме проверки
            202: Пишет комментарий к отвергнутой проверке
            203: Выход из проверки
            204: Выбор города для 
            205: Выбор адреса для
        }
        '''
        self.cities = []
        self.addresses = set()
        self.address = ''  # Город и адрес с которыми работает данный Inspector
        self.city = ''
        self.ans_zones = [0, 0, 0, 0, 0, 0, 0]  # Пусть тут хранятся результаты проверки каждой из зон (bool)
        self.comments_inspector = ['', '', '', '', '', '',
                                   '']  # Пусть тут хранятся комментарии к проверке каждой из зон (str)
        self.spreadsht = ''
        self.worksht = ''
        self.record = ''
        '''
        Поля копирующие столбы из таблицы base_check
        '''
        self.zone17 = []
        self.comments = []
        self.data_id = 0
        self.id = 0
        self.YPR_username = ''
        self.YPR_id = ''
        self.address_id = 0
        self.n = 0  # Номер проверки

        self.number_of_checks = 0  # Столбец из addresses. Показывает сколько проверок уже сделано


users = {}
MAX_ZONES = 7
current_time = datetime.datetime.now()
today = str(current_time.day) + '.' + str(current_time.month) + '.' + str(current_time.year)
ypt_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
ypt_start.add('Начать проверку')
start_inspect = types.ReplyKeyboardMarkup(resize_keyboard=True)
start_inspect.add(types.KeyboardButton('Начать проверку'))
add_user_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
roles = ['Управляющий', 'Проверяющий', 'Суперюзер']
for i in roles:
    add_user_menu.add(types.KeyboardButton(i))

inspector_ways = ['Добавить адрес', 'Удалить адрес', 'Ваши адреса']
inspector_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
for i in inspector_ways:
    inspector_menu.add(types.KeyboardButton(i))
exit_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
exit_btn.add(types.KeyboardButton('Выйти'))
superuser_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
options = ['Добавить город', 'Добавить адрес', 'Выдать права пользователю', 'Создать проверку', 'Справка']
for i in options:
    superuser_menu.add(types.KeyboardButton(i))
ways = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Клавиатура для выбора кол-ва подразделений
ways.add(types.KeyboardButton("1"), types.KeyboardButton("2"))
choice = types.ReplyKeyboardMarkup(resize_keyboard=True).row(types.KeyboardButton('✅ - принято'),
                                                             types.KeyboardButton('❌ - отказано'))


def chid(id):
    return users[id].user_id == id


async def death():
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    await conn.execute('DELETE FROM base_check')
    await conn.execute('DELETE FROM addresses')
    await conn.execute('DELETE FROM cities')
    await conn.execute('DELETE FROM dates')
    await conn.execute('DELETE FROM user_address')
    await conn.execute('UPDATE quantity SET quantity = 0, n = 1')
    await conn.execute('UPDATE users SET condition = 0, number_of_base_checks = 0, online = 0, base_check_id = NULL')
    s = client.open('Тобольск')
    s.delete()
    s = client.open('Тюмень')
    s.delete()


async def check_user(message):
    user_id = str(message.from_user.id)
    if int(user_id) not in users:
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)

        if message.from_user.username == 'perekris':
            if (await conn.fetchrow('SELECT * FROM users WHERE username = $1', message.from_user.username)) is None:
                await conn.execute('INSERT INTO users (user_id, role_id, username) VALUES ($1, 3, $2)', user_id, message.from_user.username)

        try:
            row = (await conn.fetchrow('SELECT role_id FROM users WHERE user_id = $1', user_id))['role_id']

            if row == 1:
                users.update({int(user_id): YPR(int(user_id), message.from_user.username)})
                if (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', user_id))['condition'] == 11:
                    data = (await conn.fetchrow('SELECT data FROM dates ORDER BY id DESC LIMIT 1'))['data']
                    await bot.send_message(int(user_id), 'Приветствую, Управляющий. У вас есть доступная проверка '
                                                         'от {}\nНажмите начать проверку, '
                                                         'чтобы продолжить.'.format(data), reply_markup=ypt_start)
                else:
                    await bot.send_message(int(user_id), 'Приветствую, Управляющий!\nКогда появится доступная проверка '
                                                         'вам придёт уведомление!')

            elif row == 2:
                users.update({int(user_id): Inspector(int(user_id), message.from_user.username)})
                if (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', user_id))['condition'] == 0:
                    await bot.send_message(int(user_id), 'Приветствую, Проверяющий!\nКогда появится доступная проверка '
                                                         'вам придёт уведомление!')
                    await bot.send_message(int(user_id), 'Пока что можете выбрать адреса, которые должны будете '
                                                         'проверять или посмотреть ваши адреса.', reply_markup=inspector_menu)
                else:
                    await bot.send_message(int(user_id), 'Есть доступная проверка.', reply_markup=start_inspect)

            elif row == 3:
                users.update({int(user_id): SuperUser(int(user_id), message.from_user.username)})
                await bot.send_message(int(user_id), 'Приветствую, суперюзер! Выберите опцию:',
                                       reply_markup=superuser_menu)

        except Exception as _ex:
            print(_ex)
            await bot.send_message(message.from_user.id, 'Вы не зарегистрированы в системе')

        await conn.close()


async def show_cities_checker(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    users[id].cities = [i['city'] for i in (await conn.fetch('SELECT city FROM cities'))]

    if bool(users[id].cities):
        users[id].condition = 204
        await conn.execute('UPDATE users SET condition = 1 WHERE user_id = $1 AND role_id = 2', str(id))
        cities_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(len(users[id].cities)):
            cities_menu.add(types.KeyboardButton(users[id].cities[i]))
        await bot.send_message(id, 'Выберите город:',
                               reply_markup=cities_menu)
    else:
        await bot.send_message(id, 'Пока что список городов пуст.')
    await conn.close()


async def show_addresses_checker(id, flag):
    if flag:
        users[id].condition = 205
    else:
        users[id].condition = 207
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    addresses = [i['address'] for i in (await conn.fetch(
        'SELECT address FROM addresses, cities WHERE addresses.city_id=cities.id AND cities.city = $1',
        users[id].city))]
    addresses_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(len(addresses)):
        users[id].addresses.add(addresses[i])
        addresses_menu.add(addresses[i])

    await bot.send_message(id, 'Выберите адрес:', reply_markup=addresses_menu)


async def show_addresses_for_checker(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    ans = 'Ваши адреса:\n'
    records = (await conn.fetch('SELECT city_id, address_id FROM user_address WHERE user_id = $1 ORDER BY city_id ASC', str(id)))
    if bool(records):
        for record in records:
            city = (await conn.fetchrow('SELECT city FROM cities WHERE id = $1', record['city_id']))['city']
            address = (await conn.fetchrow('SELECT address FROM addresses WHERE id = $1', record['address_id']))['address']
            ans += '{} - {}\n'.format(city, address)
        await bot.send_message(id, ans)
    else:
        await bot.send_message(id, 'Пока что ваш список адресов пуст.')
    await conn.close()


async def show_delete_cities_checker(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    records = (await conn.fetch('SELECT city_id FROM user_address WHERE user_id = $1', str(id)))
    if bool(records):
        users[id].condition = 206
        await conn.execute('UPDATE users SET condition = 1 WHERE user_id = $1 AND role_id = 2', str(id))
        cities_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        users[id].cities = []
        for record in records:
            city = (await conn.fetchrow('SELECT city FROM cities WHERE id = $1', record['city_id']))['city']
            if city not in users[id].cities:
                users[id].cities.append(city)
                cities_menu.add(types.KeyboardButton(city))
        await bot.send_message(id, 'Выберите город:',
                               reply_markup=cities_menu)
    else:
        await bot.send_message(id, 'Пока что список городов пуст.')
    await conn.close()


async def add_city(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    if (await conn.fetchrow('SELECT * FROM base_check')) is None:
        users[id].condition = 101
        await bot.send_message(id, 'Введите название города:', reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(id, 'В данный момент существует незаконченная проверка. Изменение данных невозможно.')
    await conn.close()


async def show_cities(id):
    users[id].condition = 102
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    cities = [i['city'] for i in (await conn.fetch('SELECT city FROM cities'))]
    await conn.close()
    cities_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(len(cities)):
        cities_menu.add(types.KeyboardButton(cities[i]))

    await bot.send_message(id, 'Выберите город, к которому хотите добавить новый адрес:',
                           reply_markup=cities_menu)


async def add_address(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    if (await conn.fetchrow('SELECT * FROM base_check')) is None:
        users[id].condition = 103
        await bot.send_message(id, 'Введите название адреса:', reply_markup=types.ReplyKeyboardRemove())
    else:
        await bot.send_message(id, 'В данный момент существует незаконченная проверка. Изменение данных невозможно.')

    await conn.close()


async def add_user(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    if (await conn.fetchrow('SELECT * FROM base_check')) is None:
        users[id].condition = 104
        await bot.send_message(id, 'Выберите каких пользователей хотите добавить в систему:',
                               reply_markup=add_user_menu)
    else:
        await bot.send_message(id, 'В данный момент существует незаконченная проверка. Изменение данных невозможно.')

    await conn.close()


async def reference(id):
    await bot.send_message(id, 'Добавить город - По введённому названию создаёт Гугл таблицу\n'
                               'Добавить адрес - Из списка городов пользователь выбирает город, после чего вводит '
                               'название адреса, который хочет добавить. В гугл таблице по названии города '
                               'добавляется лист с названием адреса.\n'
                               'Выдать права пользователю - Выберите роль, по которой хотите добавить пользователей. '
                               'Чтобы добавить пользователя по выбранной роли, необходимо в чат с ботом переслать '
                               'любое сообщение, отправленное этим пользователем. Чтобы завершить процесс добавления '
                               'пользователей в систему, достаточно отправить любое текстовое сообщение боту.\n'
                               'Создать проверку - Отправляет всем Управляющим сообщение о том, что появилась '
                               'проверка от сегодняшней даты. Создаёт во всех гугл таблицах во всех листах новую '
                               'проверку.')
    await bot.send_message(id, 'Выберите опцию:', reply_markup=superuser_menu)


async def create_check(id):
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    await conn.execute('UPDATE users SET online = 1 WHERE role_id = 1')
    YPRs = [i['user_id'] for i in (await conn.fetch('SELECT user_id FROM users WHERE role_id = 1'))]
    records = await conn.fetch('SELECT city, address FROM cities INNER JOIN addresses ON addresses.city_id = cities.id')
    await conn.execute('INSERT INTO dates(data) VALUES ($1)', today)
    await conn.execute('UPDATE quantity SET n = 1')
    dirs = {}
    for record in records:
        if record['city'] not in dirs:
            dirs[record['city']] = []
        dirs[record['city']].append(record['address'])
    await conn.close()
    ya_client = yadisk.AsyncClient('bb5b8d1e9acd405eaab568e32d1efa20', '7d57f8002cd54111a15539374d591502',
                                   'y0_AgAAAABzb_fwAAsZ9AAAAAD3rkl8FpbUIVBQR1qyqvcQAKjD89sRrk0')

    async with ya_client:
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        for city in dirs:
            try:
                spreadsht = client.open(city)
                for address in dirs[city]:
                    await conn.execute('UPDATE quantity SET quantity = quantity + 1')
                    worksht = spreadsht.worksheet("title", address)
                    worksht.add_rows(17)
                    dates = set()
                    path_dir = city + '/' + address
                    async for data in await ya_client.listdir(path_dir):
                        dates.add(data.name)
                    if today not in dates:
                        await ya_client.mkdir(path_dir + '/' + today)
                    else:
                        await ya_client.mkdir(
                            path_dir + '/' + today + '(' + str(random.randint(1, 100)) + ')')  # Потом убрать

                    number = (await conn.fetchrow('SELECT number_of_checks FROM addresses WHERE address = $1', address))[
                        'number_of_checks']
                    worksht = spreadsht.worksheet("title", address)
                    worksht.update_value(((number + 1) * 16 + (number + 1) + 1, 2), today)

                    worksht.update_values(crange=('A' + str((number + 1) * 16 + 2 + (number + 1)) + ':A' + str(
                        (number + 1) * 16 + 2 + (number + 1) + 14)),
                                          values=[['Зона 1'], ['Комментарий'], ['Зона 2'], ['Комментарий'], ['Зона 3'],
                                                  ['Комментарий'], ['Зона 4'], ['Комментарий'], ['Зона 5'], ['Комментарий'],
                                                  ['Зона 6'], ['Комментарий'], ['Зона 7'], ['Комментарий'], ['ИТОГ']])
            except Exception:
                pass

        await conn.execute('UPDATE addresses SET number_of_checks = number_of_checks + 1')

    for ypr in YPRs:
        await conn.execute('UPDATE users SET condition = 11 WHERE role_id = 1')
        await bot.send_message(int(ypr), 'Появилась проверка от {}\nНажмите начать проверку, '
                                         'чтобы продолжить.'.format(today), reply_markup=ypt_start)
    await bot.send_message(id, 'Проверка создана.')
    await conn.close()


async def show_cities_YPR(id):  # Функция для отображения Городов на клавиатуре в тг
    conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                 host=settings.host)
    users[id].cities = [i['city'] for i in (await conn.fetch('SELECT city FROM cities'))]
    await conn.close()

    if len(users[id].cities) < 2:
        users[id].way = 1

    cities_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(len(users[id].cities)):
        cities_menu.add(types.KeyboardButton(users[id].cities[i]))
    await bot.send_message(id, 'Выберите город:', reply_markup=cities_menu)


async def show_addresses(addresses, id):  # Функция для отображения адресов города на клавиатуре в тг
    addresses_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(len(addresses)):
        addresses_menu.add(addresses[i])

    await bot.send_message(id, 'Выберите адрес:', reply_markup=addresses_menu)


@bot.message_handler(commands=['start'])
async def send_welcome(message):
    #await death()
    await check_user(message)


@bot.message_handler(content_types=['text'])
async def answer(message):
    await check_user(message)
    id = message.from_user.id

    # ЛОГИКА СУПЕРЮЗЕРА
    if message.text == 'Добавить город' and users[id].condition == 100 and chid(id):
        await add_city(id)

    elif message.text == 'Добавить адрес' and users[id].condition == 100 and chid(id):
        await show_cities(id)

    elif message.text == 'Выдать права пользователю':
        await add_user(id)

    elif message.text == 'Создать проверку' and users[id].condition == 100 and chid(id):
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        if (await conn.fetchrow('SELECT * FROM base_check')) is None:
            await create_check(id)
        else:
            await bot.send_message(id,
                                   'В данный момент существует незаконченная проверка. Изменение данных невозможно.')

        await conn.close()

    elif message.text == 'Справка' and users[id].condition == 100 and chid(id):
        await reference(id)

    elif users[id].condition == 101 and chid(id):
        users[id].condition = 100

        city = message.text

        ya_client = yadisk.AsyncClient('bb5b8d1e9acd405eaab568e32d1efa20', '7d57f8002cd54111a15539374d591502',
                                       'y0_AgAAAABzb_fwAAsZ9AAAAAD3rkl8FpbUIVBQR1qyqvcQAKjD89sRrk0')
        path_dir = city
        async with ya_client:
            if await ya_client.is_dir(path_dir):
                try:
                    users[id].spreadsht = client.open(city)
                    await bot.send_message(id, 'Город {} уже существует.\nСсылка на таблицу: {}'.format(city, users[
                        id].spreadsht.url))
                except Exception:
                    users[id].condition = 100
                    await bot.send_message(id, 'Операция была не выполнена. Повторите попытку.')
                    await bot.send_message(id, 'Выберите опцию:', reply_markup=superuser_menu)
            else:
                await ya_client.mkdir(path_dir)
                users[id].spreadsht = client.create(city)
                users[id].spreadsht.share('maslomartbot@gmail.com', role='writer', type='user')
                users[id].spreadsht.share('', role='reader', type='anyone')
                url = users[id].spreadsht.url
                await bot.send_message(id, 'Таблица с именем {} успешно создана!\nСсылка на таблицу: {}\n(перейдите '
                                           'по ссылке, если хотите, чтобы таблица отоброжалась в вашем гугл '
                                           'диске)'.format(city, url))
                conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                             host=settings.host)
                await conn.execute('INSERT INTO cities (city) VALUES ($1)', city)
                await conn.close()

        await bot.send_message(id, 'Выберите опцию:', reply_markup=superuser_menu)

    elif users[id].condition == 102 and chid(id):
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        if (await conn.fetchrow('SELECT * FROM cities WHERE city = $1', str(message.text))) is not None:
            users[id].city = message.text
            await add_address(id)
        else:
            users[id].condition = 100
            await bot.send_message(id, 'Указанного города не существует. Повторите попытку.')
            await bot.send_message(id, 'Выберите опцию:', reply_markup=superuser_menu)

    elif users[id].condition == 103 and chid(id):
        users[id].condition = 100
        address = message.text
        users[id].spreadsht = client.open(users[id].city)
        url = users[id].spreadsht.url

        ya_client = yadisk.AsyncClient('bb5b8d1e9acd405eaab568e32d1efa20', '7d57f8002cd54111a15539374d591502',
                                       'y0_AgAAAABzb_fwAAsZ9AAAAAD3rkl8FpbUIVBQR1qyqvcQAKjD89sRrk0')
        path_dir = users[id].city + '/' + address

        async with ya_client:
            if await ya_client.is_dir(path_dir):
                await bot.send_message(id, 'Адрес {} уже существует.\nСсылка на таблицу: {}'.format(
                    address, users[id].spreadsht.url))
            else:
                conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                             host=settings.host)
                ans = await conn.fetchrow(
                    'SELECT 1 FROM addresses WHERE addresses.city_id = (SELECT id FROM cities WHERE '
                    'city = $1)', users[id].city)
                await conn.execute('INSERT INTO addresses (address, city_id) SELECT $1, id FROM cities WHERE city '
                                   '= $2', address, users[id].city)
                await conn.close()
                await ya_client.mkdir(path_dir)
                # если к городу не прикреплён ни один адрес
                if ans:
                    users[id].spreadsht.add_worksheet(address)
                else:
                    users[id].spreadsht.sheet1.title = address
                await bot.send_message(id, 'Адрес {} успешно добавлен в таблицу {}.\nСсылка на таблицу: {}'.format(
                    address, users[id].city, url))
                users[id].worksht = users[id].spreadsht.worksheet("title", address)
                users[id].worksht.resize(17, 100)

        await bot.send_message(id, 'Выберите опцию:', reply_markup=superuser_menu)

    elif users[id].condition == 104 and chid(id) and message.text in roles:
        users[id].condition = 105
        users[id].role = roles.index(message.text) + 1
        await bot.send_message(id, 'Перешлите сообщение пользователя, которого хотите добавить в систему, как {}.\n'
                                   'Чтобы выйти нажмите кнопку "Выйти".'.format(roles[users[id].role - 1]),
                               reply_markup=exit_btn)

    elif users[id].condition == 105 and chid(id):
        if message.forward_from is None:
            users[id].condition = 100
            await bot.send_message(id, 'Выберите опцию:', reply_markup=superuser_menu)
        else:
            conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                         host=settings.host)
            if (await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', str(message.forward_from.id))) is None:
                await conn.execute('INSERT INTO users (user_id, role_id, username) VALUES ($1, $2, $3)',
                                   str(message.forward_from.id), users[id].role, str(message.forward_from.username))
                await bot.send_message(id, 'Пользователь @{} успешно добавлен в систему.'.format(
                    str(message.forward_from.username)))
                await bot.send_message(id,
                                       'Перешлите сообщение пользователя, которого хотите добавить в систему, как {}.\n'
                                       'Чтобы выйти нажмите кнопку "Выйти".'.format(
                                           roles[users[id].role - 1]), reply_markup=exit_btn)
            else:
                await bot.send_message(id, 'Пользователь @{} уже есть в системе.'.format(
                    str(message.forward_from.username)))
                await bot.send_message(id,
                                       'Перешлите сообщение пользователя, которого хотите добавить в систему, как {}.\n'
                                       'Чтобы выйти нажмите кнопку "Выйти".'.format(
                                           roles[users[id].role - 1]), reply_markup=exit_btn)

            await conn.close()

    # ЛОГИКА УПРАВЛЯЮЩЕГО
    elif users[id].condition == 0 and message.text == 'Начать проверку' and users[id].user_id == id:
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        if (await conn.fetchrow('SELECT "YPR_id" FROM base_check WHERE "YPR_id" = $1', str(id))) is None:
            users[id].addresses = set()
            users[id].zones17 = ['', '', '', '', '', '', '']
            users[id].comments = ['', '', '', '', '', '', '']
            await bot.send_message(id, 'Сколько у вас подразделений?', reply_markup=ways)
        elif (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', str(id)))['condition'] == 11:
            record = (await conn.fetchrow('SELECT * FROM base_check WHERE "YPR_id" = $1', str(id)))
            city = (await conn.fetchrow('SELECT city FROM cities WHERE id = (SELECT city_id FROM addresses '
                                        'WHERE id = $1)', record['address_id']))['city']
            address = (await conn.fetchrow('SELECT address FROM addresses WHERE id = $1', record['address_id']))[
                'address']
            ans_zones = [int(i) for i in record['ans_zones'].split(';')]
            users[id].condition = 3
            users[id].number_of_zone = ans_zones.index(0) + 1
            users[id].user_choice = [city, address]
            users[id].way = 0
            users[id].flag_comment = False
            users[id].ans_zones = ans_zones
            users[id].number_of_checks = (await conn.fetchrow(
                'SELECT number_of_checks FROM addresses WHERE address = $1', users[id].user_choice[1]
            ))['number_of_checks']

            await bot.send_message(id, 'Отправьте фотографию Зоны {} повторно.'.format(ans_zones.index(0) + 1),
                                   reply_markup=types.ReplyKeyboardRemove())
        await conn.close()

    elif users[id].condition == 0 and message.text == '1' and users[id].user_id == id:
        users[id].condition = 1
        await show_cities_YPR(id)

    elif users[id].condition == 0 and message.text == '2' and users[id].user_id == id:
        users[id].way = 2
        users[id].condition = 1
        await show_cities_YPR(id)

    elif users[id].condition == 1 and message.text in users[id].cities and users[id].user_id == id:
        users[id].condition = 2
        users[id].user_choice[0] = message.text

        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        addresses = [i['address'] for i in (await conn.fetch(
            'SELECT address FROM addresses, cities WHERE addresses.city_id=cities.id AND cities.city = $1',
            message.text))]

        await conn.close()

        for address in addresses:
            users[id].addresses.add(address)

        await show_addresses(addresses, id)

    elif users[id].condition == 2 and message.text in users[id].addresses and users[id].user_id == id:
        if users[id].user_choice[1] != message.text:
            users[id].user_choice[1] = message.text
            conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                         host=settings.host)
            users[id].number_of_checks = (await conn.fetchrow(
                'SELECT number_of_checks FROM addresses WHERE address = $1', users[id].user_choice[1]
            ))['number_of_checks']
            await conn.close()
            users[id].condition = 3
            await bot.send_message(id,
                                   'Отправьте фотографию Зоны {}, чтобы получить следующее задание'.format(
                                       users[id].number_of_zone),
                                   reply_markup=types.ReplyKeyboardRemove())
            users[id].spreadsht = client.open(users[id].user_choice[0])
            users[id].worksht = users[id].spreadsht.worksheet("title", users[id].user_choice[1])
        else:
            await bot.send_message(id, 'Проверка по этому адресу уже выполнена.')

    elif users[id].condition == 3 and users[id].flag_comment and users[id].user_id == id:
        comment = message.text
        try:
            comment = comment.replace(';', '.')
        except Exception:
            pass
        users[id].comments[users[id].number_of_zone - 1] = comment
        users[id].worksht.update_value((users[id].number_of_checks * 16 + users[id].number_of_zone * 2 + 1 +
                                        users[id].number_of_checks, 2), comment)

        try:
            if users[id].ans_zones is not None:
                users[id].ans_zones[users[id].ans_zones.index(0)] = 1
                users[id].number_of_zone = users[id].ans_zones.index(0)
        except Exception:
            users[id].number_of_zone = 7

        users[id].number_of_zone += 1

        if users[id].number_of_zone >= MAX_ZONES + 1:
            users[id].condition = 0
            conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                         host=settings.host)
            await bot.send_message(id, 'Город: {}\nАдрес: {}\nДанные отправлены на проверку'.format(
                users[id].user_choice[0], users[id].user_choice[1]))

            city_id = (await conn.fetchrow('SELECT id FROM cities WHERE city = $1', users[id].user_choice[0]))['id']
            address_id = (await conn.fetchrow('SELECT id FROM addresses WHERE address = $1', users[id].user_choice[1]))[
                'id']

            our_inspector_id = (await conn.fetchrow('SELECT user_id FROM user_address WHERE city_id = $1 AND '
                                                    'address_id = $2 AND role_id = 2', city_id, address_id))

            if our_inspector_id is None:

                our_inspector = (await conn.fetchrow('SELECT * FROM users WHERE role_id = 2 AND '
                                                     'number_of_base_checks = (SELECT MIN('
                                                     'number_of_base_checks) FROM users WHERE role_id = 2)'))
            else:
                our_inspector = (await conn.fetchrow('SELECT * FROM users WHERE user_id = $1 AND role_id = 2',
                                                     str(our_inspector_id['user_id'])))
            print(our_inspector)
            if users[id].ans_zones is not None and len(users[id].ans_zones) == MAX_ZONES:
                await conn.execute('UPDATE base_check SET zone17 = $1, comments = $2 WHERE "YPR_id" = $3 AND '
                                   'address_id = (SELECT id FROM addresses WHERE address = $4)',
                                   ';'.join(users[id].zones17), ';'.join(users[id].comments), str(id),
                                   users[id].user_choice[1])
            else:
                data_id = (await conn.fetchrow('SELECT id FROM dates ORDER BY id DESC LIMIT 1'))['id']
                try:
                    await conn.execute(
                        '''
                        INSERT INTO base_check (zone17, comments, data_id, "YPR_username", address_id, "YPR_id", 
                        "Checker_id", "Checker_username") VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ''', ';'.join(users[id].zones17), ';'.join(users[id].comments), data_id, message.from_user.username,
                        address_id, str(id), our_inspector['user_id'], our_inspector['username'])
                    await conn.execute('UPDATE users SET number_of_base_checks = number_of_base_checks + 1 WHERE user_id '
                                       '= $1 AND role_id = 2', our_inspector['user_id'])
                except Exception:
                    our_inspector = (await conn.fetchrow('SELECT * FROM users WHERE role_id = 2 AND '
                                                         'number_of_base_checks = (SELECT MIN('
                                                         'number_of_base_checks) FROM users WHERE role_id = 2)'))
                    await conn.execute(
                        '''
                        INSERT INTO base_check (zone17, comments, data_id, "YPR_username", address_id, "YPR_id", 
                        "Checker_id", "Checker_username") VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ''', ';'.join(users[id].zones17), ';'.join(users[id].comments), data_id,
                        message.from_user.username,
                        address_id, str(id), our_inspector['user_id'], our_inspector['username'])
                    await conn.execute(
                        'UPDATE users SET number_of_base_checks = number_of_base_checks + 1 WHERE user_id '
                        '= $1 AND role_id = 2', our_inspector['user_id'])
            users[id].flag_comment = False
            if users[id].way == 2:
                users[id].way = 1
                users[id].condition = 2
                users[id].zones17 = ['', '', '', '', '', '', '']
                users[id].comments = ['', '', '', '', '', '', '']
                users[id].number_of_zone = 1

                addresses = [i['address'] for i in (await conn.fetch(
                    'SELECT address FROM addresses, cities WHERE addresses.city_id=cities.id AND cities.city = $1',
                    users[id].user_choice[0]))]

                await show_addresses(addresses, id)
            else:
                base_check_id = (await conn.fetchrow('SELECT base_check_id FROM users WHERE user_id = $1 AND role_id '
                                                     '= 1', str(id)))['base_check_id']
                if base_check_id is None:
                    if our_inspector['condition'] == 0:
                        await bot.send_message(
                            our_inspector['user_id'],
                            "Пользователь @{} завершил проверку и ждёт проверки.".format(users[id].username),
                            reply_markup=start_inspect)
                    await conn.execute('UPDATE users SET condition = 1, online = 1 WHERE user_id = $1 AND role_id = 2',
                                       str(our_inspector['user_id']))
                    await conn.execute('UPDATE users SET condition = 0, online = 0 WHERE user_id = $1 AND role_id = 1', str(id))
                else:
                    await conn.execute('UPDATE users SET base_check_id = NULL WHERE user_id = $1', str(id))

                    # Кусок кода из логики Проверяющего
                    check = await conn.fetchrow('SELECT * FROM base_check WHERE id = $1', base_check_id)
                    data = (await conn.fetchrow('SELECT data FROM dates WHERE id = $1', check['data_id']))['data']
                    city = (await conn.fetchrow('SELECT city FROM cities WHERE id = (SELECT city_id FROM addresses '
                                                'WHERE id = $1)', check['address_id']))['city']
                    address = (await conn.fetchrow('SELECT address FROM addresses WHERE id = $1', check['address_id']))[
                        'address']
                    formed = 'Город: {}\nАдрес: {}\n\nВаш результат проверки от {}:\n'.format(city, address, data)
                    ans_zones = [int(i) for i in check['ans_zones'].split(';')]
                    comments_inspector = check['comments_inspector'].split(';')

                    for i in range(MAX_ZONES):
                        if ans_zones[i] == 1:
                            formed += '\nЗона {}: {}'.format(i + 1, '✅')
                        else:
                            formed += '\nЗона {}: {} Причина: {}'.format(i + 1, '❌', comments_inspector[i])
                    formed += '\n\nТребуется повторная проверка'

                    await conn.execute('UPDATE users SET condition = 11 WHERE user_id = $1', check['YPR_id'])
                    await bot.send_message(check['YPR_id'], formed)
                    await bot.send_message(check['YPR_id'], 'Отправьте фотографию Зоны {} '
                                                            'повторно'.format(ans_zones.index(0) + 1),
                                           reply_markup=types.ReplyKeyboardRemove())
                    users[int(check['YPR_id'])].condition = 3
                    users[int(check['YPR_id'])].number_of_zone = ans_zones.index(0) + 1
                    users[int(check['YPR_id'])].user_choice = [city, address]
                    users[int(check['YPR_id'])].way = 0
                    users[int(check['YPR_id'])].flag_comment = False
                    users[int(check['YPR_id'])].ans_zones = ans_zones
                    users[int(check['YPR_id'])].spreadsht = client.open(users[int(check['YPR_id'])].user_choice[0])
                    users[int(check['YPR_id'])].worksht = users[int(check['YPR_id'])].spreadsht.worksheet("title",
                                                                                        users[int(check['YPR_id'])].user_choice[1])
                    users[int(check['YPR_id'])].number_of_checks = (await conn.fetchrow(
                        'SELECT number_of_checks FROM addresses WHERE address = $1', users[int(check['YPR_id'])].user_choice[1]
                    ))['number_of_checks']

            await conn.close()

        else:
            await bot.send_message(id,
                                   'Отправьте фотографию Зоны {}, чтобы получить следующее задание'.format(
                                       users[id].number_of_zone))
            users[id].flag_comment = False

    # ЛОГИКА ПРОВЕРЯЮЩЕГО
    elif users[id].condition == 200 and message.text == 'Добавить адрес' and chid(id):
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        if (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', str(id)))['condition'] == 0:
            await show_cities_checker(id)
        await conn.close()

    elif users[id].condition == 200 and message.text == 'Удалить адрес' and chid(id):
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        if (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', str(id)))['condition'] == 0:
            await show_delete_cities_checker(id)
        await conn.close()

    elif users[id].condition == 200 and message.text == 'Ваши адреса' and chid(id):
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        if (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', str(id)))['condition'] == 0:
            await show_addresses_for_checker(id)
        await conn.close()

    elif users[id].condition == 204 and message.text in users[id].cities and chid(id):
        users[id].city = message.text
        await show_addresses_checker(id, True)

    elif users[id].condition == 205 and message.text in users[id].addresses and chid(id):
        users[id].condition = 200
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        await conn.execute('UPDATE users SET condition = 0 WHERE user_id = $1 AND role_id = 2', str(id))
        address_id = (await conn.fetchrow('SELECT id FROM addresses WHERE address = $1', message.text))['id']
        city_id = (await conn.fetchrow('SELECT id FROM cities WHERE city = $1', users[id].city))['id']
        if (await conn.fetchrow('SELECT * FROM user_address WHERE address_id = $1 AND role_id = 2 AND city_id = $2 '
                                'AND user_id = $3', int(address_id), int(city_id), str(id))) is None:
            await conn.execute('INSERT INTO user_address (address_id, role_id, city_id, user_id) VALUES ($1, 2, $2, $3)',
                               int(address_id), int(city_id), str(id))
            await bot.send_message(id, '{}/{} - теперь является вашей зоной для проверки.'.format(users[id].city,
                                                                                                  message.text))
        else:
            await bot.send_message(id, 'Адрес - {} уже занят.'.format(message.text))
        if (await conn.fetchrow('SELECT * FROM base_check WHERE "Checker_id" = $1', str(id))) is None:
            await bot.send_message(id, 'Пока что доступных проверок нет.', reply_markup=inspector_menu)
        else:
            await bot.send_message(id, 'Есть доступная проверка.', reply_markup=start_inspect)
        await conn.close()

    elif users[id].condition == 206 and message.text in users[id].cities and chid(id):
        users[id].city = message.text
        await show_addresses_checker(id, False)

    elif users[id].condition == 207 and message.text in users[id].addresses and chid(id):
        users[id].condition = 200
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        address_id = (await conn.fetchrow('SELECT id FROM addresses WHERE address = $1', message.text))['id']
        city_id = (await conn.fetchrow('SELECT id FROM cities WHERE city = $1', users[id].city))['id']
        await conn.execute('DELETE FROM user_address WHERE city_id = $1 AND address_id = $2 AND role_id = 2 AND '
                           'user_id = $3', city_id, address_id, str(id))
        await conn.execute('UPDATE users SET condition = 0 WHERE user_id = $1 AND role_id = 2', str(id))

        if (await conn.fetchrow('SELECT * FROM base_check WHERE "Checker_id" = $1', str(id))) is None:
            await bot.send_message(id, 'Пока что доступных проверок нет.', reply_markup=inspector_menu)
        else:
            await bot.send_message(id, 'Есть доступная проверка.', reply_markup=start_inspect)

        await conn.close()

    elif users[id].condition == 200 and (
            message.text == 'Начать проверку' or message.text == 'Начать повторную проверку' or message.text == 'Начать следующую проверку') and chid(
        id):

        users[id].condition = 201
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)

        record = await conn.fetchrow(
            'SELECT * FROM base_check WHERE "Checker_id" = $1 AND n = (SELECT n FROM quantity)',
            str(id))
        if record is None:

            await bot.send_message(id, 'Доступных проверок пока что нет.', reply_markup=types.ReplyKeyboardRemove())
        else:
            address = (await conn.fetchrow('SELECT address FROM addresses WHERE id = $1', record['address_id']))[
                'address']
            city = (
                await conn.fetchrow('SELECT city FROM cities WHERE id = (SELECT city_id FROM addresses WHERE id = $1)',
                                    record['address_id']))['city']
            number_of_checks = (await conn.fetchrow('SELECT number_of_checks FROM addresses WHERE id = $1',
                                                    record['address_id']))['number_of_checks']
            await conn.close()

            users[id].address = address
            users[id].city = city
            users[id].number_of_checks = number_of_checks
            users[id].zone17 = record['zone17'].split(';').copy()
            users[id].comments = record['comments'].split(';')
            users[id].data_id = record['data_id']
            users[id].id = record['id']
            users[id].YPR_username = record['YPR_username']
            users[id].YPR_id = record['YPR_id']
            users[id].address_id = record['address_id']
            users[id].n = record['n']
            users[id].spreadsht = client.open(city)
            users[id].worksht = users[id].spreadsht.worksheet("title", address)
            users[id].record = record
            if record['ans_zones']:
                users[id].ans_zones = [int(i) for i in record['ans_zones'].split(';')]
                users[id].comments_inspector = record['comments_inspector'].split(';')

            users[id].worksht.update_value(
                (1 + users[id].number_of_checks * 16 + users[id].number_of_checks, users[id].n + 2),
                'Проверка {}'.format(users[id].n))

            users[id].condition = 201

            if record['ans_zones'] is None:
                await bot.send_photo(id, users[id].zone17[users[id].number_of_zone - 1],
                                     'Город: {}\nАдрес: {}\nСсылка на изображение: {}\n\nВам отправлена Зона {} от '
                                     '@{}\n\nКомментарий: {}\n\nОпишите результат'
                                     ':'.format(users[id].city, users[id].address,
                                                users[id].zone17[users[id].number_of_zone - 1],
                                                users[id].number_of_zone,
                                                users[id].YPR_username,
                                                users[id].comments[users[id].number_of_zone - 1]),
                                     reply_markup=choice)
            else:
                while users[id].ans_zones[users[id].number_of_zone - 1] == 1:
                    users[id].worksht.update_value(
                        (users[id].number_of_checks * 16 + (users[id].number_of_zone) * 2 +
                         users[id].number_of_checks, users[id].n + 2), '✅')
                    if users[id].number_of_zone == 7:
                        users[id].number_of_zone = 8
                        users[id].condition = 203
                        break
                    users[id].number_of_zone += 1
                await bot.send_photo(id, users[id].zone17[users[id].number_of_zone - 1],
                                     'ПОВТОРНАЯ ПРОВЕРКА!\n'
                                     'Город: {}\n'
                                     'Адрес: {}\n'
                                     'Ссылка на изображение: {}\n\n'
                                     'Вам отправлена Зона {} от @{}\n\n'
                                     'Комментарий: {}\n\n'
                                     'Опишите результат:'.format(users[id].city, users[id].address,
                                                                 users[id].zone17[users[id].number_of_zone - 1],
                                                                 users[id].number_of_zone,
                                                                 users[id].YPR_username,
                                                                 users[id].comments[users[id].number_of_zone - 1]),
                                     reply_markup=choice)

            users[id].number_of_zone += 1

    elif users[id].condition == 201 and message.text == '✅ - принято' and chid(id) and users[
        id].number_of_zone < MAX_ZONES + 2:
        users[id].ans_zones[users[id].number_of_zone - 2] = 1
        users[id].worksht.update_value((users[id].number_of_checks * 16 + (users[id].number_of_zone - 1) * 2 +
                                        users[id].number_of_checks, users[id].n + 2), '✅')
        try:
            while users[id].ans_zones[users[id].number_of_zone - 1] == 1:
                users[id].worksht.update_value(
                    (users[id].number_of_checks * 16 + (users[id].number_of_zone) * 2 +
                     users[id].number_of_checks, users[id].n + 2), '✅')
                if users[id].number_of_zone == 7:
                    users[id].number_of_zone = 8
                    users[id].condition = 203
                    break
                users[id].number_of_zone += 1
        except Exception:
            users[id].number_of_zone = 8
            users[id].condition = 203
        if users[id].number_of_zone < MAX_ZONES + 1:
            if users[id].record['ans_zones'] is None:
                await bot.send_photo(id, users[id].zone17[users[id].number_of_zone - 1],
                                     'Город: {}\nАдрес: {}\nСсылка на изображение: {}\n\nВам отправлена Зона {} от '
                                     '@{}\n\nКомментарий: {}\n\nОпишите результат'
                                     ':'.format(users[id].city, users[id].address,
                                                users[id].zone17[users[id].number_of_zone - 1],
                                                users[id].number_of_zone,
                                                users[id].YPR_username,
                                                users[id].comments[users[id].number_of_zone - 1]),
                                     reply_markup=choice)
            else:
                await bot.send_photo(id, users[id].zone17[users[id].number_of_zone - 1],
                                     'ПОВТОРНАЯ ПРОВЕРКА!\n'
                                     'Город: {}\n'
                                     'Адрес: {}\n'
                                     'Ссылка на изображение: {}\n\n'
                                     'Вам отправлена Зона {} от @{}\n\n'
                                     'Комментарий: {}\n\n'
                                     'Опишите результат:'.format(users[id].city, users[id].address,
                                                                 users[id].zone17[users[id].number_of_zone - 1],
                                                                 users[id].number_of_zone,
                                                                 users[id].YPR_username,
                                                                 users[id].comments[users[id].number_of_zone - 1]),
                                     reply_markup=choice)

        users[id].number_of_zone += 1

    elif users[id].condition == 201 and message.text == '❌ - отказано' and chid(id) and users[
        id].number_of_zone < MAX_ZONES + 2:
        users[id].ans_zones[users[id].number_of_zone - 2] = 0
        users[id].worksht.update_value((users[id].number_of_checks * 16 + (users[id].number_of_zone - 1) * 2 +
                                        users[id].number_of_checks, users[id].n + 2), '❌')
        users[id].condition = 202

        await bot.send_message(id, 'Укажите причину отказа:', reply_markup=types.ReplyKeyboardRemove())

    elif users[id].condition == 202 and chid(id):
        try:
            users[id].comments_inspector[users[id].number_of_zone - 2] = message.text.replace(';', '.')
        except Exception:
            users[id].comments_inspector[users[id].number_of_zone - 2] = message.text
        users[id].condition = 201
        users[id].worksht.update_value((1 + users[id].number_of_checks * 16 + (users[id].number_of_zone - 1) * 2 +
                                        users[id].number_of_checks, users[id].n + 2), message.text)
        try:
            while users[id].ans_zones[users[id].number_of_zone - 1] == 1:
                users[id].worksht.update_value(
                    (users[id].number_of_checks * 16 + (users[id].number_of_zone) * 2 +
                     users[id].number_of_checks, users[id].n + 2), '✅')
                if users[id].number_of_zone == 7:
                    users[id].number_of_zone = 8
                    users[id].condition = 203
                    break
                users[id].number_of_zone += 1
        except Exception:
            users[id].number_of_zone = 8
            users[id].condition = 203
        if users[id].number_of_zone < MAX_ZONES + 1:
            if users[id].record['ans_zones'] is None:
                await bot.send_photo(id, users[id].zone17[users[id].number_of_zone - 1],
                                     'Город: {}\nАдрес: {}\nСсылка на изображение: {}\n\nВам отправлена Зона {} от '
                                     '@{}\n\nКомментарий: {}\n\nОпишите результат'
                                     ':'.format(users[id].city, users[id].address,
                                                users[id].zone17[users[id].number_of_zone - 1],
                                                users[id].number_of_zone,
                                                users[id].YPR_username,
                                                users[id].comments[users[id].number_of_zone - 1]),
                                     reply_markup=choice)
            else:
                await bot.send_photo(id, users[id].zone17[users[id].number_of_zone - 1],
                                     'ПОВТОРНАЯ ПРОВЕРКА!\n'
                                     'Город: {}\n'
                                     'Адрес: {}\n'
                                     'Ссылка на изображение: {}\n\n'
                                     'Вам отправлена Зона {} от @{}\n\n'
                                     'Комментарий: {}\n\n'
                                     'Опишите результат:'.format(users[id].city, users[id].address,
                                                                 users[id].zone17[users[id].number_of_zone - 1],
                                                                 users[id].number_of_zone,
                                                                 users[id].YPR_username,
                                                                 users[id].comments[users[id].number_of_zone - 1]),
                                     reply_markup=choice)

        users[id].number_of_zone += 1
    if users[id].condition == 201 and users[id].number_of_zone == 9:
        users[id].condition = 203

    if users[id].condition == 203 and chid(id):
        conn = await asyncpg.connect(user=settings.user, password=settings.password, database=settings.db_name,
                                     host=settings.host)
        await conn.execute('UPDATE quantity SET quantity = quantity - 1')
        users[id].worksht.update_value(
            (1 + users[id].number_of_checks * 16 + users[id].number_of_checks + 15, users[id].n + 2),
            '{}%'.format(round((users[id].ans_zones.count(1) / 7) * 100)))

        if all(users[id].ans_zones):
            data = (await conn.fetchrow('SELECT data FROM dates WHERE id = $1', users[id].data_id))['data']
            await bot.send_message(users[id].YPR_id, 'Город: {}\nАдрес: {}\n\nВаш результат проверки от {}:\n'
                                                     '\nЗона 1: ✅\nЗона 2: ✅\nЗона 3: ✅\nЗона 4: ✅\nЗона 5: ✅'
                                                     '\nЗона 6: ✅\nЗона 7: ✅\n\nПоздравляем с успешной проверкой!'.format(
                users[id].city, users[id].address,
                data))

            await conn.execute('UPDATE users SET number_of_base_checks = number_of_base_checks - 1 WHERE user_id = $1',
                               str(id))
            await conn.execute('DELETE FROM base_check WHERE id = $1', users[id].id)

            availability_of_records = (
                await conn.fetchrow('SELECT id FROM base_check WHERE "Checker_id" = $1', str(id)))
            if availability_of_records:
                await bot.send_message(id,
                                       'Город: {}\nАдрес: {}\nРезультат: 7/7 - 100%\nОтчёт принят. Попыток: {}'.format(
                                           users[id].city, users[id].address, users[id].n))
                await bot.send_message(id, 'Доступна следующая проверка.', reply_markup=start_inspect)
            else:
                await bot.send_message(id,
                                       'Город: {}\nАдрес: {}\nРезультат: 7/7 - 100%\nОтчёт принят. Попыток: {}'.format(
                                           users[id].city, users[id].address, users[id].n))
                await bot.send_message(id, 'Доступных проверок пока что нет.', reply_markup=types.ReplyKeyboardRemove())
                await conn.execute(
                    'UPDATE users SET condition = 0, online = 0 WHERE user_id = $1 AND role_id = 2', str(id))

            users[id].number_of_zone = 1
            users[id].condition = 200
            users[id].ans_zones = [0, 0, 0, 0, 0, 0, 0]
            users[id].comments_inspector = ['', '', '', '', '', '', '']

            ypr = (await conn.fetchrow('SELECT * FROM base_check WHERE "YPR_id" = $1', users[id].YPR_id))
            if ypr is None:
                users[int(users[id].YPR_id)].ans_zones = None
                users[int(users[id].YPR_id)].condition = 0

        else:
            await conn.execute('UPDATE base_check SET ans_zones = $1, comments_inspector = $2, n = $3 WHERE id = $4',
                               ';'.join([str(i) for i in users[id].ans_zones]), ';'.join(users[id].comments_inspector),
                               users[id].n + 1, users[id].id)

            availability_of_records = (
                await conn.fetchrow(
                    'SELECT id FROM base_check WHERE "Checker_id" = $1 AND n = (SELECT n FROM quantity)', str(id)))

            if availability_of_records:
                await bot.send_message(id,
                                       'Город: {}\nАдрес: {}\nРезультат: {}/7 - {}%\nОтчёт отправлен на переработку.'.format(
                                           users[id].city, users[id].address, users[id].ans_zones.count(1),
                                           round((users[id].ans_zones.count(1) / 7) * 100, 2)))
                await bot.send_message(id, 'Доступна следующая проверка.', reply_markup=start_inspect)
            else:
                await bot.send_message(id,
                                       'Город: {}\nАдрес: {}\nРезультат: {}/7 - {}%\nОтчёт отправлен на переработку.'.format(
                                           users[id].city, users[id].address, users[id].ans_zones.count(1),
                                           round((users[id].ans_zones.count(1) / 7) * 100, 2)))
                await bot.send_message(id, 'Доступных проверок пока что нет.', reply_markup=types.ReplyKeyboardRemove())
                await conn.execute(
                    'UPDATE users SET condition = 0, online = 0 WHERE user_id = $1 AND role_id = 2', str(id))

            users[id].number_of_zone = 1
            users[id].condition = 200
            users[id].ans_zones = [0, 0, 0, 0, 0, 0, 0]
            users[id].comments_inspector = ['', '', '', '', '', '', '']

        if (await conn.fetchrow('SELECT quantity FROM quantity'))['quantity'] == 0 or (await conn.fetchrow('SELECT * FROM users WHERE online = 1')) is None:

            checks = await conn.fetch('SELECT * FROM base_check')

            if len(checks) > 0:
                await conn.execute('UPDATE quantity SET n = n + 1')
                await conn.execute('UPDATE quantity SET quantity = $1', len(checks))
                data = (await conn.fetchrow('SELECT data FROM dates WHERE id = $1', checks[0]['data_id']))['data']
                for check in checks:
                    address = \
                        (await conn.fetchrow('SELECT address FROM addresses WHERE id = $1', check['address_id']))[
                            'address']
                    city = (
                        await conn.fetchrow(
                            'SELECT city FROM cities WHERE id = (SELECT city_id FROM addresses WHERE id = $1)',
                            check['address_id']))['city']
                    formed = 'Город: {}\nАдрес: {}\n\nВаш результат проверки от {}:\n'.format(city, address, data)
                    ans_zones = [int(i) for i in check['ans_zones'].split(';')]
                    comments_inspector = check['comments_inspector'].split(';')
                    address = (await conn.fetchrow('SELECT address FROM addresses WHERE id = $1', check['address_id']))[
                        'address']

                    for i in range(MAX_ZONES):
                        if ans_zones[i] == 1:
                            formed += '\nЗона {}: {}'.format(i + 1, '✅')
                        else:
                            formed += '\nЗона {}: {} Причина: {}'.format(i + 1, '❌', comments_inspector[i])
                    formed += '\n\nТребуется повторная проверка'
                    if (await conn.fetchrow('SELECT condition FROM users WHERE user_id = $1', check['YPR_id']))[
                        'condition'] == 0:
                        await conn.execute('UPDATE users SET condition = 11, online = 1 WHERE user_id = $1', check['YPR_id'])
                        await bot.send_message(check['YPR_id'], formed)
                        await bot.send_message(check['YPR_id'], 'Отправьте фотографию Зоны {} '
                                                                'повторно'.format(ans_zones.index(0) + 1),
                                               reply_markup=types.ReplyKeyboardRemove())
                        try:
                            users[int(check['YPR_id'])].condition = 3
                            users[int(check['YPR_id'])].number_of_zone = ans_zones.index(0) + 1
                            users[int(check['YPR_id'])].user_choice = [city, address]
                            users[int(check['YPR_id'])].way = 0
                            users[int(check['YPR_id'])].flag_comment = False
                            users[int(check['YPR_id'])].ans_zones = ans_zones
                            users[int(check['YPR_id'])].spreadsht = client.open(users[int(check['YPR_id'])].user_choice[0])
                            users[int(check['YPR_id'])].worksht = users[int(check['YPR_id'])].spreadsht.worksheet("title",
                                                                                                users[int(check['YPR_id'])].user_choice[
                                                                                                    1])
                            users[int(check['YPR_id'])].number_of_checks = (await conn.fetchrow(
                                'SELECT number_of_checks FROM addresses WHERE address = $1', users[int(check['YPR_id'])].user_choice[1]
                            ))['number_of_checks']
                        except KeyError:
                            continue
                    else:
                        # в таблицу users добавим id base_check'а, чтобы потом вызвать повторную проверку по этому id
                        await conn.execute('UPDATE users SET base_check_id = $1 WHERE user_id = $2', check['id'], check['YPR_id'])
            else:
                await conn.execute('UPDATE quantity SET n = 1')
                us = [i for i in (await conn.fetch('SELECT * FROM users WHERE role_id = 1'))]
                for u in us:
                    try:
                        user_id = int(u['user_id'])
                        user_username = u['username']
                        users.update({user_id: YPR(user_id, user_username)})
                    except KeyError:
                        continue
                super_user_ids = [i for i in (await conn.fetch('SELECT user_id FROM users WHERE role_id = 3'))]
                data = (await conn.fetchrow('SELECT data FROM dates WHERE id = $1', users[id].data_id))
                for super_user_id in super_user_ids:
                    await bot.send_message(int(super_user_id['user_id']),
                                           'Проверка от {} завершена'.format(data['data']))

        await conn.close()


@bot.message_handler(content_types=['photo'])
async def take_photo(message):
    id = message.from_user.id
    await check_user(message)
    if users[id].condition == 3 and users[id].user_choice[0] != '' and users[id].user_choice[1] != '' \
            and not users[id].flag_comment and users[id].user_id == id:
        if users[id].spreadsht.title != users[id].user_choice[0] and users[id].worksht.title != users[id].user_choice[0]:
            users[id].spreadsht = client.open(users[id].user_choice[0])
            users[id].worksht = users[id].spreadsht.worksheet("title", users[id].user_choice[1])

        upload_dir = users[id].user_choice[0] + '/' + users[id].user_choice[1]
        image_id = message.photo[len(message.photo) - 1].file_id
        file_path = (await bot.get_file(image_id)).file_path

        download_file = await bot.download_file(file_path)
        scr = 'media/' + file_path
        with open(scr, 'wb') as new_file:
            new_file.write(download_file)

        ya_client = yadisk.AsyncClient('bb5b8d1e9acd405eaab568e32d1efa20', '7d57f8002cd54111a15539374d591502',
                                       'y0_AgAAAABzb_fwAAsZ9AAAAAD3rkl8FpbUIVBQR1qyqvcQAKjD89sRrk0')
        # Грузим картинку и получаем на неё ссыль
        async with ya_client:
            upload_dir += '/' + today + '/Зона' + str(users[id].number_of_zone) + '.jpg'
            if await ya_client.is_file(upload_dir):
                await ya_client.remove(upload_dir, permanently=True)
            await ya_client.upload('media/' + file_path, upload_dir, overwrite=True)
            await ya_client.publish(upload_dir)
            time.sleep(0.2)
            URL = (await ya_client.get_meta(upload_dir)).public_url  # Ссылка на изображение publish
            time.sleep(0.2)
            q = 0
            miniflag = False
            while URL is None:
                if q >= 15:
                    await bot.send_message(id, 'Отправьте фотографию повторно')
                    miniflag = True
                    break
                URL = (await ya_client.get_meta(upload_dir)).public_url
                time.sleep(0.5)
                q += 1
            # Удаляем файл
            os.remove(scr)
        # Добавляем ссыль на картинку в гугл таблицу
        if not miniflag:
            users[id].worksht.update_value((users[id].number_of_checks * 16 + users[id].number_of_zone * 2 +
                                            users[id].number_of_checks, 2), URL)
            users[id].zones17[users[id].number_of_zone - 1] = URL
            users[id].flag_comment = True

            await bot.send_message(id, 'Отправьте комментарий к Зоне {}, чтобы получить следующее задание'.format(
                users[id].number_of_zone))


import asyncio

asyncio.run(bot.polling())
