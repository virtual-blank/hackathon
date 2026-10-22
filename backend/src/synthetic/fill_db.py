
"""
Наполнение БД синтетическими данными (для разработки и демо).

Запуск:
    python -m src.synthetic.fill_db            # наполнить БД
    python -m src.synthetic.fill_db --wipe     # удалить всё, что создал предыдущий запуск

Что создаётся (всё в одной транзакции: упадёт что-то одно, в БД не останется ничего):
  * 2 основных аккаунта (USERS) с логином/паролем, у которых данные написаны вручную под их роли:
    Александра (ментор) и Дима (её ученик): привычки с историей отметок, друзья, переписки, ревью;
  * небольшое окружение этих двух аккаунтов (коллеги, ученики, друзья): обычные пользователи со своими привычками;
  * N_USERS случайных пользователей: дружба / заявки / блокировки, переписки, привычки, отметки, ревью, refresh-токены;
  * справочник ачивок (из src/achievements/seed_achievements_db.py) и выданные по реальным данным user_achievements.

shared_habit_users НЕ заполняется: таблица есть, строк в ней нет (логика совместных привычек ещё не реализована).

Допущения (файлы enums.py, mixins.py и database/enum.py я не видел):
  * TimeStampMixin даёт created_at и updated_at (timestamptz), они заполняются явно;
  * значения enum'ов в БД лежат строками (задаются константами ST_*, VIS_*, THEME_* ниже).

На Windows для zoneinfo нужен пакет tzdata.
"""

import argparse
import asyncio
import base64
import json
import aioboto3
from core.config import get_minio_settings
import os
import random
import re
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo
from src.achievements.models import RuleTypeEnum

from src.users.pfp.minio import PUBLIC_PREFIX



import asyncpg

from core.config import get_db_settings

from src.auth.hash_argon import create_password
from pydantic_settings import BaseSettings, SettingsConfigDict



BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

USER_1_PFP = f"{PUBLIC_PREFIX}defaults/alexandra-default-pfp.jpg"
USER_2_PFP = f"{PUBLIC_PREFIX}defaults/dima-default-pfp.jpg"

achievements_data = [
    # Стрики
    {
        "name": "Глитч",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 3,
        "color_hex": "#77F77F",
        "icon_url": "streak-3.webp",
        "description": "В твоей системе явный сбой и ей это не нравится. Продолжай",
        "requirement": "Отметить выполнение привычки 3 дня подряд.",
    },
    {
        "name": "В ударе",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 7,
        "color_hex": "#FF6600",
        "icon_url": "streak-7.webp",
        "description": "Неделя без отмазок, а больше можешь?",
        "requirement": "Отметить выполнение привычки 7 дней подряд.",
    },
    {
        "name": "Зависимость",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 21,
        "color_hex": "#02A37B",
        "icon_url": "streak-21.webp",
        "description": "Привычка уже приросла к тебе, не останавливайся",
        "requirement": "Отметить выполнение привычки 21 день подряд.",
    },
    {
        "name": "Познание",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 30,
        "color_hex": "#D780FF",
        "icon_url": "streak-30.webp",
        "description": "Твой мозг стал инструментом, а не просто органом",
        "requirement": "Отметить выполнение привычки 30 дней подряд.",
    },
    # Привычки
    {
        "name": "Первый шаг",
        "rule_type": RuleTypeEnum.TOTAL_HABITS,
        "rule_value": 1,
        "color_hex": "#A1641F",
        "icon_url": "habits-1.webp",
        "description": "Первая цель поставлена. Теперь самое сложное — не забить на неё на второй день.",
        "requirement": "Создать 1 новую привычку.",
    },
    {
        "name": "Архитектор",
        "rule_type": RuleTypeEnum.TOTAL_HABITS,
        "rule_value": 3,
        "color_hex": "#FFE552",
        "icon_url": "habits-3.webp",
        "description": "Три привычки одновременно. Твой энтузиазм похвален, посмотрим, как дела с тайм-менеджментом.",
        "requirement": "Создать суммарно 3 привычки.",
    },
    {
        "name": "Гуру продуктивности",
        "rule_type": RuleTypeEnum.TOTAL_HABITS,
        "rule_value": 10,
        "color_hex": "#FA89E9",
        "icon_url": "habits-10.webp",
        "description": "Десять активных трекеров. Ты вообще спишь или питаешься исключительно кофе и амбициями?",
        "requirement": "Создать суммарно 10 привычек.",
    },
    # Друзья
    {
        "name": "Первый контакт",
        "rule_type": RuleTypeEnum.FRIENDS_COUNT,
        "rule_value": 1,
        "color_hex": "#C7C7C7",
        "icon_url": "friends-1.webp",
        "description": "Теперь за твоими успехами следит как минимум один живой человек. Никакого давления.",
        "requirement": "Добавить 1 пользователя в список друзей.",
    },
    {
        "name": "Пати",
        "rule_type": RuleTypeEnum.FRIENDS_COUNT,
        "rule_value": 5,
        "color_hex": "#690404",
        "icon_url": "friends-5.webp",
        "description": "Свидетелей твоего роста стало больше. Сливаться теперь официально стыдно.",
        "requirement": "Добавить 5 пользователей в список друзей.",
    },
    {
        "name": "Лидер мнений",
        "rule_type": RuleTypeEnum.FRIENDS_COUNT,
        "rule_value": 15,
        "color_hex": "#FFCF70",
        "icon_url": "friends-15.webp",
        "description": "У тебя своя мини-секта. Главное — продолжать делать вид, что ты точно знаешь, куда идешь.",
        "requirement": "Добавить 15 пользователей в список друзей.",
    },
]


class SyntheticUsers(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_prefix="SYNTHETIC_", extra="ignore")
    user_1_username: str
    user_1_password: str
    user_1_email: str
    user_2_username: str
    user_2_password: str
    user_2_email: str

    @property
    def user_1(self) -> dict:
      return {"username": self.user_1_username, "password": self.user_1_password, "email": self.user_1_email}
    
    @property
    def user_2(self) -> dict:
      return {"username": self.user_2_username, "password": self.user_2_password, "email": self.user_2_email}


def get_synthetic_users() -> SyntheticUsers:
  return SyntheticUsers()

user_1_dict = get_synthetic_users().user_1
user_2_dict = get_synthetic_users().user_2

# =====================================================================
#  ОСНОВНЫЕ АККАУНТЫ (логин / пароль для входа)
# =====================================================================

USERS = {
    "USER_1": user_1_dict,  # ментор
    "USER_2": user_2_dict,  # менти
}
MAIN_KEYS = {"USER_1": "alexandra", "USER_2": "dima"}  # ключ в USERS -> ключ в PEOPLE
USERNAME_MAX_LEN = 16

# =====================================================================
#  ОБЪЁМ ДАННЫХ / НАСТРОЙКИ
# =====================================================================
N_USERS = 3000  # сколько случайных пользователей создать
REL_PER_USER = 15  # среднее число заявок/связей, которые инициирует каждый пользователь
MAX_HABITS = 8  # макс. число привычек на пользователя (среднее около половины)
HISTORY_DAYS = 180  # глубина истории в днях
DIALOG_SHARE = 0.3  # доля дружб, у которых есть переписка
MAX_CONVERSATIONS = 4  # макс. число разговоров (по 4-9 сообщений) в одном диалоге
REVIEW_RATE = 0.05  # вероятность, что друг оставил ревью на неприватную привычку друга

# Аватарки: доля случайных пользователей с собственным pfp_url (у остальных NULL = дефолтная иконка).
# Ссылки имеют настоящий формат pfp/<user_id>/<32 hex>.<ext>, но САМИХ ФАЙЛОВ в MinIO нет:
# на фронте такие аватарки будут битыми. Поэтому по умолчанию 0.
PFP_SHARE = 0.0

# Refresh-токены случайных пользователей: сколько максимум на пользователя (0 = не создавать) и срок жизни.
# REFRESH_TTL_DAYS должен совпадать с REFRESH_TOKEN_EXPIRE_DAYS из проекта.
MAX_REFRESH_TOKENS = 3
REFRESH_TTL_DAYS = 30

RNG_SEED = 20260101  # фиксирует «случайность» в данных основных аккаунтов: рисунок отметок одинаков на каждом запуске

# Список id созданных пользователей: по нему --wipe находит, что удалять (метки в самих данных нет).
# Добавь файл в .gitignore.
MANIFEST_PATH = Path(__file__).with_name("fill_db_created_users.json")

# =====================================================================
#  ЗНАЧЕНИЯ ENUM В БД
# =====================================================================
ST_PENDING = "pending"
ST_ACCEPTED = "accepted"
ST_BLOCKED = "blocked"
VIS_PRIVATE = "private"
VIS_FRIENDS = "friends"
VIS_PUBLIC = "public"
THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"

# =====================================================================
#  СЛОВАРИ ДЛЯ СЛУЧАЙНЫХ ПОЛЬЗОВАТЕЛЕЙ (уезжают в SQL как параметры, экранировать ничего не нужно)
# =====================================================================
DICT = {
    "names_m": [
        "ivan", "dmitry", "sergey", "alexey", "andrey", "maxim", "artem", "pavel", "nikita", "roman", "oleg",
        "denis", "egor", "kirill", "ilya", "mikhail", "vladimir", "anton", "evgeny", "vadim", "timur", "gleb",
        "stanislav", "yuri", "konstantin", "danil", "arseny", "leonid", "ruslan", "alexander", "nikolay", "viktor",
        "fedor", "matvey", "lev", "daniil", "mark", "bogdan", "tikhon", "semen", "vasily", "grigory", "boris",
        "valery", "georgy", "platon", "igor",
    ],
    "names_f": [
        "olga", "maria", "elena", "anna", "irina", "natalia", "ekaterina", "daria", "polina", "alina", "svetlana",
        "yulia", "tatiana", "kseniya", "victoria", "sofia", "margarita", "vera", "nina", "diana", "milena",
        "valeria", "anastasia", "alisa", "kristina", "lidia", "zoya", "marina", "larisa", "galina", "evgenia",
        "lyubov", "veronika", "arina", "varvara", "ulyana", "eva", "taisiya", "regina", "angelina",
    ],
    "names_short": [
        "dima", "sasha", "katya", "masha", "olya", "lena", "nastya", "kolya", "vanya", "zhenya", "vlad", "tanya",
        "misha", "lesha", "dasha", "sonya", "pasha", "slava", "kostya", "tema", "yulya", "lera", "ksyusha", "vitya",
        "max", "alex", "den", "sema", "grisha", "zhora", "vika", "nadya", "galya",
    ],
    # мужская форма фамилии; для женщин к ней добавляется "a"
    "surnames": [
        "ivanov", "petrov", "smirnov", "kuznetsov", "popov", "sokolov", "lebedev", "kozlov", "novikov", "morozov",
        "volkov", "vasiliev", "zaitsev", "pavlov", "semenov", "golubev", "vinogradov", "bogdanov", "fedorov",
        "mikhailov", "belov", "tarasov", "belyaev", "komarov", "orlov", "kiselev", "makarov", "andreev", "ilyin",
        "gusev", "titov", "kuzmin", "baranov", "kulikov", "alekseev", "stepanov", "yakovlev", "sorokin", "sergeev",
        "romanov", "zakharov", "borisov", "korolev", "gerasimov", "ponomarev", "grigoriev", "lazarev", "medvedev",
        "ershov", "nikitin", "sobolev", "polyakov", "tsvetkov", "danilov", "zhukov", "frolov", "krylov", "maksimov",
        "sidorov", "osipov", "belousov", "egorov", "matveev", "bobrov", "dmitriev", "kalinin", "antonov", "timofeev",
        "veselov", "filippov", "markov", "mironov", "aleksandrov", "konovalov", "kazakov", "efimov", "denisov",
        "gromov", "fomin", "davydov", "melnikov", "karpov", "vlasov", "maslov", "tikhonov", "gavrilov", "rodionov",
        "kotov", "savelyev", "panov", "suvorov", "abramov", "voronov", "mukhin", "arkhipov", "trofimov", "martynov",
        "chernov", "seleznev", "nazarov", "lobanov", "belyakov", "nekrasov", "zhdanov", "naumov", "ermakov",
        "ignatiev", "savin", "safonov", "kirillov", "moiseev", "efremov", "kalashnikov",
    ],
    "domains": (
        ["gmail.com"] * 7 + ["yandex.ru"] * 5 + ["mail.ru"] * 4
        + ["outlook.com", "icloud.com", "proton.me", "bk.ru", "rambler.ru"]
    ),
    "themes": [THEME_SYSTEM] * 5 + [THEME_LIGHT] * 3 + [THEME_DARK] * 4,
    "tzs": (
        ["Europe/Moscow"] * 14 + ["Asia/Yekaterinburg"] * 2
        + ["Asia/Novosibirsk", "Europe/Berlin", "Europe/London", "America/New_York", "UTC"]
    ),
    "visibilities": [VIS_PRIVATE, VIS_FRIENDS, VIS_FRIENDS, VIS_PUBLIC],
    "colors": ["#4F46E5", "#EF4444", "#10B981", "#F59E0B", "#3B82F6", "#EC4899", "#8B5CF6", "#14B8A6"],
    "habit_titles": [
        "Утренняя зарядка 10 минут", "Выпить стакан воды после пробуждения", "Пить 2 литра воды в день",
        "Прочитать 20 страниц книги", "10 000 шагов в день", "Пробежка 5 км", "Медитация 10 минут", "Йога по утрам",
        "Растяжка перед сном", "Холодный душ", "Вести дневник", "Выучить 5 новых слов", "Английский 20 минут",
        "Подкаст на английском", "Час без телефона перед сном", "Лечь спать до 23:30", "Встать в 7 утра",
        "Не есть сладкое после 18:00", "Принять витамины", "Готовить ужин дома", "Порция овощей за обедом",
        "Не пить кофе после 15:00", "Приседания 50 раз", "Планка 2 минуты", "Отжимания 30 раз",
        "Плавание в бассейне", "Тренировка в зале", "Писать код час", "Решить задачу на алгоритмы",
        "Разобрать почту до нуля", "Записать траты за день", "Откладывать 500 ₽ в копилку", "Позвонить родителям",
        "Написать другу", "Уборка 15 минут", "Полить цветы", "Погулять с собакой", "Гитара 20 минут",
        "Нарисовать скетч", "Планирование дня утром", "Подвести итоги дня", "Не листать ленту соцсетей",
        "Выключить ноутбук в 22:00", "Дыхательная практика", "Записать три вещи, за которые благодарен",
        "Пересмотреть конспекты", "Один урок по Python", "Прочитать статью по работе", "Испанский 15 минут",
        "Растяжка шеи и плеч",
    ],
    "push_comments": [
        "Так держать!", "Красавчик!", "Ну наконец-то", "Горжусь тобой", "Огонь", "Респект", "Отлично справляешься",
        "Продолжай в том же духе", "Вот это дисциплина", "Мотивируешь!", "Крутой стрик", "Так и надо",
    ],
    "shame_comments": [
        "Опять халтура", "Серьёзно?", "Не верю", "Давай лучше", "Слабо", "Стыдно", "Это всё?", "Где стрик?",
        "Снова пропуск?",
    ],
}

# Короткие разговоры между друзьями. a: / b: - кто пишет (какая сторона a или b, решается случайно для каждого диалога).
CHAT_TEMPLATES = [
    ["a:Привет! Видел, ты вчера отметил привычку, молодец", "b:Привет) Да, пока держусь, уже пятый день",
     "a:Ого, круто! У меня на третий день всегда сбой", "b:Просто поставь напоминание на вечер, мне помогло",
     "a:Попробую, спасибо за совет"],
    ["a:Как успехи со стриком?", "b:Неделя уже, но сегодня чуть не забыл", "a:Главное, что вспомнил 🙂",
     "b:Ага, отметил в последний момент"],
    ["a:Погнали в выходные на пробежку?", "b:Давай! Только не рано, ладно?", "a:Ха-ха, в 10 нормально?",
     "b:Вот это уже по-человечески", "a:Тогда у парка в 10, договорились"],
    ["a:Слушай, я на этой неделе всё пропустил, навалилась работа", "b:Бывает, главное не бросай совсем",
     "a:Да, с понедельника начну заново", "b:Если что, пиши, будем вместе подтягиваться"],
    ["a:Ты чем-нибудь пользуешься, чтобы не забывать про привычки?", "b:Просто напоминания в приложении и всё",
     "a:Надо тоже включить, а то вечно забываю", "b:Да, оно реально помогает"],
    ["a:Как твоя привычка с чтением?", "b:Читаю по 20 страниц перед сном, уже вторая книга пошла",
     "a:Круто, что за книга?", "b:Сейчас про привычки, как ни странно 😅", "a:Ха, ну тогда ты точно в теме"],
    ["a:Ты вчера что-то поздно отметил)", "b:Да, пришлось задержаться на работе",
     "a:Главное, что до полуночи успел", "b:Еле-еле, но успел"],
    ["a:Привет! Не знаешь, как лучше вставать пораньше?", "b:Я ложусь на час раньше и убираю телефон от кровати",
     "a:Надо попробовать, а то всё время сплю до последнего", "b:Через неделю привыкнешь, проверено"],
    ["a:Как выходные?", "b:Хорошо, съездили за город, почти не сидел в телефоне", "a:Здорово, завидую",
     "b:Приезжай в следующий раз с нами"],
    ["a:Спасибо за ревью на мою привычку, приятно)", "b:Да ты молодец, реально стараешься",
     "a:Старался. Теперь твоя очередь радовать стриком", "b:Уже работаю над этим 😄"],
    ["a:Не могу вспомнить, во сколько ты обычно делаешь зарядку?", "b:Часов в семь, пока не проснулся окончательно",
     "a:Понятно, я попробую в восемь", "b:Главное, чтобы каждый день в одно и то же время"],
    ["a:Слушай, у тебя получается пить воду по графику?", "b:С трудом, но поставил бутылку на стол, и стало проще",
     "a:Хороший лайфхак, возьму себе"],
    ["a:Привет! Давно не списывались, как дела?", "b:Привет! Всё нормально, много работы, но держусь",
     "a:Рад слышать. Увидимся на выходных?", "b:Да, напиши ближе к субботе"],
    ["a:Сегодня первый раз за месяц пропустил тренировку", "b:Не накручивай, один пропуск ничего не ломает",
     "a:Да, но стрик сгорел...", "b:Начнёшь новый, будет даже интереснее", "a:Ладно, уговорил 😅"],
    ["a:Я записался на курс английского, буду заниматься три раза в неделю", "b:О, круто! Давно хотел то же самое",
     "a:Присоединяйся, вместе веселее", "b:Подумаю, скинь ссылку"],
    ["a:Что посоветуешь почитать про продуктивность?", "b:Мне зашла «Атомные привычки», простая и по делу",
     "a:Да, слышал про неё, возьму", "b:Потом расскажешь, как тебе"],
    ["a:Ты завтра идёшь на пробежку?", "b:Если не будет дождя, то да", "a:Посмотрел прогноз, вроде будет сухо",
     "b:Тогда в 8 у входа в парк?", "a:Договорились"],
    ["a:У меня сегодня сложный день, нет сил даже на привычки",
     "b:Сделай хотя бы минимальную версию, пять минут тоже считается", "a:Да, пожалуй, так и сделаю",
     "b:Вот и молодец"],
    ["a:Видел, у тебя уже три привычки в списке 👀",
     "b:Ага, решил не размениваться по мелочам, но стараюсь не перегрузить себя", "a:Разумно, я на пяти выгорел",
     "b:Вот поэтому и не спешу"],
    ["a:С днём рождения! 🎉", "b:Спасибо большое!", "a:Желаю никогда не терять стрик, ха-ха", "b:Вот это пожелание 😄"],
    ["a:Привет! Скинь, пожалуйста, ссылку на то видео про сон", "b:Секунду, найду", "b:Вот, держи", "a:Спасибо!"],
    ["a:Как думаешь, лучше делать зарядку утром или вечером?", "b:Мне утром проще, вечером всегда находятся дела",
     "a:Тоже склоняюсь к утру", "b:Попробуй пару недель и сам поймёшь"],
    ["a:Ты вечером будешь онлайн?", "b:Да, после восьми", "a:Тогда созвонимся, расскажу новость",
     "b:Интригуешь, но ладно, жду"],
]

# =====================================================================
#  ДАННЫЕ ОСНОВНЫХ АККАУНТОВ И ИХ ОКРУЖЕНИЯ (пишутся вручную)
# =====================================================================
MSK = "Europe/Moscow"
UTC = timezone.utc
NOW = datetime.now(UTC)


@dataclass(frozen=True)
class Person:
    username: str
    email: str
    tz: str
    theme: str
    joined_days_ago: int
    pfp_url: str | None = None


PEOPLE = {
    # основные аккаунты
    "alexandra": Person(USERS["USER_1"]["username"], USERS["USER_1"]["email"], MSK, THEME_DARK, 150, pfp_url=f"{PUBLIC_PREFIX}defaults/alexandra-default-pfp.jpg"),
    "dima": Person(USERS["USER_2"]["username"], USERS["USER_2"]["email"], MSK, THEME_DARK, 75, pfp_url=f"{PUBLIC_PREFIX}defaults/dima-default-pfp.jpg"),
    # коллеги Александры
    "igor": Person("igor_bykov", "igor.bykov@sfm.com", MSK, THEME_LIGHT, 220, pfp_url=f"{PUBLIC_PREFIX}defaults/igor-bykov-default.jpg"),
    "marina": Person("marina_k", "marina.k@sfm.com", MSK, THEME_SYSTEM, 215, pfp_url=f"{PUBLIC_PREFIX}defaults/marina-k-default.jpg"),
    "andrey": Person("andrey_devops", "andrey.s@sfm.com", MSK, THEME_DARK, 190, pfp_url=f"{PUBLIC_PREFIX}defaults/andrey-devops.jpg"),
    # ученики Александры
    "nikita": Person("nikita_sokolov", "nikita.sokolov@gmail.com", MSK, THEME_DARK, 140, pfp_url=f"{PUBLIC_PREFIX}defaults/nikita-sokolov-default.jpg"),
    "anna": Person("anna_vlasova", "anna.vlasova@yandex.ru", "Asia/Yekaterinburg", THEME_LIGHT, 120, pfp_url=f"{PUBLIC_PREFIX}defaults/anna-vlasova-default.jpg"),
    "artem": Person("artem_zhukov", "zhukov.artem@mail.ru", MSK, THEME_SYSTEM, 135, pfp_url=f"{PUBLIC_PREFIX}defaults/artem-zhukov-default.jpg"),
    "vlad": Person("vlad_romanov", "vlad.romanov94@gmail.com", MSK, THEME_DARK, 90, pfp_url=f"{PUBLIC_PREFIX}defaults/vlad-romanov-default.jpg"),
    "kirill": Person("kirill_m", "kirill.m@outlook.com", MSK, THEME_SYSTEM, 100),
    "polina": Person("polina_dev", "polina.dev@gmail.com", MSK, THEME_LIGHT, 15),
    # друг Димы и аккаунт, который Александра заблокировала
    "stas": Person("stas_kh", "stas.kh@yandex.ru", MSK, THEME_SYSTEM, 80),
    "promo": Person("invest_pro_24", "invest.pro.24@mail.ru", "UTC", THEME_SYSTEM, 30),
}
MAIN = ("alexandra", "dima")

# (кто отправил / заблокировал, кому, статус, дней назад, через сколько часов принята заявка)
RELATIONS = [
    ("alexandra", "igor", ST_ACCEPTED, 140, 3),
    ("marina", "alexandra", ST_ACCEPTED, 138, 2),
    ("andrey", "alexandra", ST_ACCEPTED, 125, 6),
    ("nikita", "alexandra", ST_ACCEPTED, 110, 4),
    ("alexandra", "artem", ST_ACCEPTED, 100, 9),
    ("anna", "alexandra", ST_ACCEPTED, 80, 1),
    ("kirill", "alexandra", ST_ACCEPTED, 70, 12),
    ("vlad", "alexandra", ST_ACCEPTED, 62, 7),
    ("dima", "alexandra", ST_ACCEPTED, 72, 3),
    ("polina", "alexandra", ST_PENDING, 2, 0),
    ("alexandra", "promo", ST_BLOCKED, 20, 0),
    ("dima", "vlad", ST_ACCEPTED, 58, 2),
    ("stas", "dima", ST_ACCEPTED, 70, 20),
    ("dima", "kirill", ST_PENDING, 2, 0),
]


@dataclass(frozen=True)
class HabitSpec:
    owner: str
    title: str
    color: str
    visibility: str
    started_days_ago: int
    notify: tuple[str, ...]  # напоминания (до 3, ограничение в БД)
    window: tuple[int, int]  # в какие часы (по местному времени) обычно отмечается
    p: float  # вероятность отметки в подходящий день
    weekdays: tuple[int, ...] | None = None  # только эти дни недели (пн = 0); None = каждый день
    current_run: int | None = None  # принудительно: серия подряд до сегодня


T_AEROBICS = "Занятие аэробикой каждое утро"
T_CALL = "Созвон с учениками каждую среду"
T_TASKS = "Проверка и актуализация своих ежедневных задач"
T_ARTICLE = "Прочитать одну техническую статью"
T_SLEEP = "Лечь спать до полуночи"
T_WATER = "Выпить 2 литра воды"
T_LEETCODE = "1 задача на LeetCode каждый день"
T_PYPROGRESS = "Проверять свой прогресс по Python"
T_REPEAT = "Повторение материала"
T_SNUS = "Не кидать снюс"
T_MEME = "Проверка цен на мемкоины"
T_DISHES = "Вымыть посуду (необязательно)"

HABITS = [
    HabitSpec("alexandra", T_AEROBICS, "#F97316", VIS_FRIENDS, 118, ("07:00",), (7, 9), 0.90, current_run=34),
    HabitSpec("alexandra", T_CALL, "#4F46E5", VIS_FRIENDS, 126, ("17:30",), (19, 21), 0.92, weekdays=(2,)),
    HabitSpec("alexandra", T_TASKS, "#10B981", VIS_PRIVATE, 96, ("09:00",), (9, 11), 0.80, current_run=11),
    HabitSpec("alexandra", T_ARTICLE, "#8B5CF6", VIS_FRIENDS, 80, ("21:30",), (21, 23), 0.55),
    HabitSpec("alexandra", T_SLEEP, "#3B82F6", VIS_PRIVATE, 70, ("23:00",), (22, 23), 0.60),
    HabitSpec("alexandra", T_WATER, "#14B8A6", VIS_PRIVATE, 60, ("11:00", "15:00", "19:00"), (18, 21), 0.75),
    HabitSpec("dima", T_LEETCODE, "#F59E0B", VIS_FRIENDS, 68, ("20:00",), (19, 23), 0.88, current_run=12),
    HabitSpec("dima", T_PYPROGRESS, "#4F46E5", VIS_FRIENDS, 66, ("18:00",), (17, 20), 0.85, weekdays=(6,)),
    HabitSpec("dima", T_REPEAT, "#3B82F6", VIS_FRIENDS, 60, ("21:30",), (21, 23), 0.72, current_run=5),
    HabitSpec("dima", T_SNUS, "#EF4444", VIS_PRIVATE, 41, ("10:00", "22:00"), (21, 23), 1.00, current_run=17),
    HabitSpec("dima", T_MEME, "#EC4899", VIS_PRIVATE, 55, ("12:00", "18:00"), (12, 19), 0.80),
    HabitSpec("dima", T_DISHES, "#14B8A6", VIS_FRIENDS, 33, ("20:30",), (20, 23), 0.45),
]

# (кто оценил, чья привычка, какая, 1 = пуш / 0 = шейм, комментарий, дней назад)
REVIEWS = [
    ("alexandra", "dima", T_LEETCODE, 1, "Так держать! Видно прогресс на созвонах", 9),
    ("vlad", "dima", T_LEETCODE, 1, "Респект, мне бы твою регулярность", 6),
    ("alexandra", "dima", T_REPEAT, 1, "Повторение это половина успеха", 3),
    ("stas", "dima", T_DISHES, 0, "Серьёзно, опять не помыл? Стыдно 😄", 4),
    ("dima", "alexandra", T_AEROBICS, 1, "Бодро! Мне бы так вставать в семь", 11),
    ("igor", "alexandra", T_CALL, 1, "Дисциплина, как всегда", 15),
    ("nikita", "alexandra", T_AEROBICS, 1, None, 7),
]


@dataclass(frozen=True)
class Session:
    """Один разговор: день, местное время начала и реплики (кто, текст). unread = сколько последних не прочитано."""

    days_ago: int
    at: str
    lines: tuple[tuple[str, str], ...]
    unread: int = 0


def S(days_ago: int, at: str, lines: list[tuple[str, str]], unread: int = 0) -> Session:
    return Session(days_ago, at, tuple(lines), unread)


DIALOGS = {
    ("alexandra", "dima"): [
        S(34, "21:12", [
            ("dima", "Александра, привет! Можно вопрос по домашке?"),
            ("alexandra", "Привет, Дим! Конечно, что там?"),
            ("dima", "Не пойму, почему зависимость в FastAPI с yield отрабатывает после ответа. Это нормально?"),
            ("alexandra", "Да, всё штатно. Код после yield выполняется уже после отправки ответа клиенту, туда обычно кладут закрытие сессии"),
            ("dima", "А коммитить там тоже можно?"),
            ("alexandra", "Лучше коммитить явно в сервисе. В зависимости потом сложно понять, где именно что-то записалось"),
            ("dima", "Понял, спасибо! Перепишу"),
        ]),
        S(21, "12:40", [
            ("alexandra", "Дим, глянула твой PR. Логику из роутов лучше вынести в сервисы, а то они разрастутся"),
            ("dima", "Ага, согласен. Сделаю до среды"),
            ("dima", "А тесты на негативные кейсы тоже нужны? Или хватит happy path?"),
            ("alexandra", "Нужны. Минимум: 404, невалидные данные и доступ чужого пользователя"),
            ("dima", "Окей, добавлю 👍"),
        ]),
        S(9, "22:05", [
            ("dima", "Александра, сегодня закрыл три задачи на литкоде подряд, хеш-мапы наконец-то зашли"),
            ("alexandra", "Круто! Только не гонись за количеством, главное разбирать чужие решения после своего"),
            ("dima", "Да, я веду заметки по паттернам. Пока их штук десять"),
            ("alexandra", "Вот это правильный подход. В среду можем разобрать твои заметки на созвоне, если останется время"),
            ("dima", "Было бы супер"),
        ]),
        S(2, "19:48", [
            ("dima", "Не успел доделать асинхронные тесты к созвону, вечером дособираю и скину"),
            ("alexandra", "Ничего, скинь потом в чат, посмотрю до пятницы"),
            ("dima", "Спасибо!"),
        ]),
        S(0, "09:20", [
            ("alexandra", "Дим, к следующему созвону подготовь, пожалуйста, вопросы по асинхронности. Разберём на живом примере"),
        ], unread=1),
    ],
    ("alexandra", "nikita"): [
        S(30, "20:15", [
            ("nikita", "Александра, здравствуйте! Подскажите, как лучше разбить проект на слои? У меня пока всё лежит в одном файле с роутами"),
            ("alexandra", "Привет, Никита! Давай так: роуты, сервисы, репозитории. Роуты только принимают запрос и отдают ответ, вся логика в сервисах"),
            ("nikita", "А pydantic-схемы и модели sqlalchemy тоже разделять?"),
            ("alexandra", "Да, схемы и ORM-модели не смешиваем. Покажу пример на созвоне"),
            ("nikita", "Супер, спасибо! 🙏"),
        ]),
        S(16, "18:30", [
            ("nikita", "Я, кажется, не успею сдать домашку до пятницы. Можно до понедельника?"),
            ("alexandra", "Можно, но давай без привычки переносить 🙂 Что именно не получается?"),
            ("nikita", "Застрял на миграциях alembic, автогенерация вообще не видит мои модели"),
            ("alexandra", "Скорее всего, модели не импортированы в env.py. Проверь, что Base.metadata видит все модули"),
            ("nikita", "Точно, я их не импортировал! Сейчас проверю"),
        ]),
        S(15, "08:50", [
            ("nikita", "Всё заработало, миграция накатилась. Спасибо огромное!"),
            ("alexandra", "Отлично! Тогда в понедельник жду домашку"),
        ]),
        S(1, "22:10", [
            ("nikita", "Александра, добрый вечер! Я сделал рефакторинг по слоям, как вы советовали"),
            ("nikita", "Можно будет посмотреть на созвоне? Особенно интересует, правильно ли я организовал сервисы"),
        ], unread=2),
    ],
    ("alexandra", "anna"): [
        S(28, "13:05", [
            ("anna", "Александра, а можно перенести наш созвон в среду? У меня в 19:00 появилась работа"),
            ("alexandra", "Привет, Аня! Давай на 20:30, подойдёт?"),
            ("anna", "Да, идеально. Спасибо!"),
            ("alexandra", "Записала. Тогда в среду в 20:30 по той же ссылке"),
        ]),
        S(12, "21:40", [
            ("anna", "Подскажите, что почитать про индексы в SQL? Мой запрос на списке пользователей работает очень долго"),
            ("alexandra", "Начни с документации PostgreSQL про B-tree индексы и прогони запрос через EXPLAIN ANALYZE, сразу будет видно, где тормозит"),
            ("anna", "Хорошо, попробую на своём проекте"),
            ("alexandra", "Если не разберёшься, пришли план запроса, посмотрим вместе"),
            ("anna", "Спасибо, что бы я без вас делала 😅"),
        ]),
        S(4, "17:25", [
            ("anna", "Нашла! Не хватало индекса по user_id, запрос стал в разы быстрее"),
            ("alexandra", "Вот, это и есть работа с планом запроса. Молодец!"),
        ]),
    ],
    ("alexandra", "artem"): [
        S(25, "19:00", [
            ("alexandra", "Артём, посмотрела твой PR. Много хорошего, но в списке заказов N+1, используй selectinload"),
            ("artem", "Ой, не заметил. Сегодня исправлю"),
            ("alexandra", "И тесты не пиши с моками базы, подними тестовую через docker, так надёжнее"),
            ("artem", "Окей. А как лучше организовать фикстуры?"),
            ("alexandra", "conftest.py в корне tests, сессия на каждый тест с откатом транзакции"),
            ("artem", "Понял, спасибо!"),
        ]),
        S(8, "11:15", [
            ("artem", "Александра, а в резюме можно писать, что проект учебный?"),
            ("alexandra", "Нужно. Только опиши, что именно сделал сам: auth, миграции, деплой. Это важнее названия"),
            ("artem", "Окей, перепишу. Скину на проверку потом"),
            ("alexandra", "Скидывай 👍"),
        ]),
    ],
    ("alexandra", "igor"): [
        S(22, "15:30", [
            ("igor", "Привет! Ты берёшь учеников на новый поток?"),
            ("alexandra", "Привет! Да, но не больше шести, иначе не успеваю нормально делать ревью"),
            ("igor", "Согласен, у меня тоже потолок шесть. План по курсу уже добавила в общий документ?"),
            ("alexandra", "Добавила. Посмотри блок про асинхронность, там нужны твои комментарии"),
            ("igor", "Гляну вечером"),
        ]),
        S(6, "12:10", [
            ("igor", "Слушай, у тебя есть шаблон фидбека по ревью? Хочу унифицировать со своими учениками"),
            ("alexandra", "Есть, держи структуру: что хорошо, что исправить, что почитать"),
            ("igor", "О, то что надо, спасибо!"),
            ("alexandra", "Если захочешь, можем сверить критерии оценки ближе к концу потока"),
            ("igor", "Давай, это было бы полезно"),
        ]),
    ],
    ("alexandra", "marina"): [
        S(18, "10:00", [
            ("marina", "Саша, привет! Мне нужны твои слоты на следующую неделю для созвонов"),
            ("alexandra", "Привет! Среда 19:00 и 20:30, плюс пятница после 18:00"),
            ("marina", "Окей, внесла в расписание"),
            ("alexandra", "Спасибо! Ане я перенесла среду на 20:30, чтобы ты была в курсе"),
            ("marina", "Да, видела, всё учла"),
        ]),
        S(1, "16:45", [
            ("marina", "Саша, не забудь заполнить отчёт по ученикам до конца недели 🙏"),
        ], unread=1),
    ],
    ("alexandra", "andrey"): [
        S(27, "14:20", [
            ("andrey", "Александра, у учеников часто не получается с Docker на Windows. Может, сделаем вместе мини-гайд?"),
            ("alexandra", "Давай! Я соберу типичные ошибки, а ты расскажешь про WSL2"),
            ("andrey", "Договорились. Черновик скину в пятницу"),
            ("alexandra", "👍"),
        ]),
        S(10, "20:55", [
            ("alexandra", "Андрей, у ученика compose не видит .env. Что смотреть в первую очередь?"),
            ("andrey", "env_file в описании сервиса и путь относительно compose-файла. Часто забывают, что .env должен лежать рядом"),
            ("alexandra", "Точно, у него путь был неверный. Спасибо!"),
            ("andrey", "Обращайся"),
        ]),
    ],
    ("dima", "vlad"): [
        S(14, "22:30", [
            ("vlad", "Дим, ты сегодня литкод решал?"),
            ("dima", "Ага, medium про скользящее окно, еле осилил"),
            ("vlad", "О, я тоже на нём застрял. Какое решение?"),
            ("dima", "Два указателя и set, за O(n). Скину код позже"),
            ("vlad", "Го созвонимся в выходные, разберём вместе"),
            ("dima", "Го. В воскресенье вечером норм?"),
            ("vlad", "Норм 👍"),
        ]),
        S(5, "19:10", [
            ("vlad", "Слушай, ты уже пробовал pytest-cov? Хочу показывать покрытие в CI"),
            ("dima", "Пока нет, но Александра как раз говорила, что надо"),
            ("vlad", "Я на выходных попробую, расскажу что получилось"),
            ("dima", "Давай, интересно"),
        ]),
    ],
    ("dima", "stas"): [
        S(12, "23:05", [
            ("stas", "Бро, глянь график, этот мем опять выстрелил"),
            ("dima", "Я до вечера не смотрю, у меня правило: проверка рынка один раз в день"),
            ("stas", "Скучный ты стал"),
            ("dima", "Зато не слился 😄"),
        ]),
        S(3, "21:50", [
            ("stas", "Как твоё не кидание? Держишься?"),
            ("dima", "Две недели уже. Тянет всё реже"),
            ("stas", "Красавчик, держись"),
            ("dima", "Спасибо, бро"),
        ]),
        S(0, "13:30", [
            ("stas", "Го в выходные на каток? Давно не виделись"),
        ], unread=1),
    ],
}


# =====================================================================
#  ПОМОЩНИКИ
# =====================================================================
def uuid7_at(ts: datetime) -> uuid.UUID:
    """UUIDv7 с временем ts: id растёт вместе со временем (так же, как у Uuid7PkMixin)."""
    ms = int(ts.timestamp() * 1000) & ((1 << 48) - 1)
    value = (ms << 80) | (0x7 << 76) | (random.getrandbits(12) << 64) | (0b10 << 62) | random.getrandbits(62)
    return uuid.UUID(int=value)


def local_today(tz: str) -> date:
    return NOW.astimezone(ZoneInfo(tz)).date()


def at_local(d: date, hh: int, mm: int, tz: str, ss: int = 0) -> datetime:
    return datetime(d.year, d.month, d.day, hh, mm, ss, tzinfo=ZoneInfo(tz)).astimezone(UTC)


def fake_password_hash() -> str:
    """Хеш в формате argon2id, но проверить по нему пароль нельзя: войти под такими аккаунтами невозможно."""

    def b64(n: int) -> str:
        return base64.b64encode(os.urandom(n)).decode().rstrip("=")

    return f"$argon2id$v=19$m=65536,t=3,p=4${b64(16)}${b64(32)}"


def streaks(done: set[date], today: date) -> tuple[int, int, date | None]:
    """(текущий стрик, максимальный стрик, последний день отметки). Текущий жив, если последняя отметка сегодня или вчера."""
    best = run = 0
    prev = None
    for d in sorted(done):
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        best = max(best, run)
        prev = d
    current = run if prev is not None and (today - prev).days <= 1 else 0
    return current, best, prev


def pick_done_days(spec: HabitSpec, start: date, today: date, rng: random.Random) -> set[date]:
    done = set()
    d = start
    while d <= today:
        if (spec.weekdays is None or d.weekday() in spec.weekdays) and rng.random() < spec.p:
            done.add(d)
        d += timedelta(days=1)
    if spec.current_run:
        for i in range(spec.current_run):
            done.add(today - timedelta(days=i))
        done.discard(today - timedelta(days=spec.current_run))  # день перед серией пропущен
    return done


def last_reminder(times: list[dtime], tz: str) -> datetime | None:
    if not times:
        return None
    z = ZoneInfo(tz)
    today = NOW.astimezone(z).date()
    candidates = [
        datetime.combine(d, t, tzinfo=z).astimezone(UTC) for d in (today, today - timedelta(days=1)) for t in times
    ]
    return max(c for c in candidates if c <= NOW)


def require(cond: bool, message: str) -> None:
    if not cond:
        raise ValueError(message)


@dataclass
class MainDataset:
    users: list[tuple]
    relations: list[tuple]
    habits: list[tuple]
    logs: list[tuple]
    reviews: list[tuple]
    messages: list[tuple]
    pool_users: list[tuple]  # (id, since, tz, is_main) для SQL-части: чтобы им тоже считались ачивки и т.д.


def build_main_dataset(password_hashes: dict[str, str]) -> MainDataset:
    rng = random.Random(RNG_SEED)

    # ---------- пользователи ----------
    ids, joined, users, pool_users = {}, {}, [], []
    for key, p in PEOPLE.items():
        day = local_today(p.tz) - timedelta(days=p.joined_days_ago)
        ts = at_local(day, rng.randint(10, 21), rng.randint(0, 59), p.tz)
        joined[key], ids[key] = ts, uuid7_at(ts)
        users.append((ids[key], ts, ts, p.username, p.email, password_hashes.get(key) or fake_password_hash(), p.theme, p.tz, p.pfp_url))
        pool_users.append((ids[key], ts, p.tz, key in MAIN))
    require(len({p.username for p in PEOPLE.values()}) == len(PEOPLE), "в PEOPLE повторяется username")
    require(len({p.email for p in PEOPLE.values()}) == len(PEOPLE), "в PEOPLE повторяется email")
    for key, p in PEOPLE.items():
        require(len(p.username) <= USERNAME_MAX_LEN, f"PEOPLE[{key!r}]: username длиннее {USERNAME_MAX_LEN}")

    # ---------- дружба / заявки / блокировки ----------
    relations, accepted_at, seen_pairs = [], {}, set()
    for src, dst, status, days_ago, hours in RELATIONS:
        pair = frozenset((src, dst))
        require(pair not in seen_pairs, f"RELATIONS: пара {src}/{dst} встречается дважды (нужна одна строка на пару)")
        seen_pairs.add(pair)
        tz = PEOPLE[src].tz
        created = at_local(local_today(tz) - timedelta(days=days_ago), rng.randint(9, 22), rng.randint(0, 59), tz)
        require(created > max(joined[src], joined[dst]), f"RELATIONS: {src}->{dst} старше одного из аккаунтов")
        updated = created + timedelta(hours=hours, minutes=rng.randint(1, 50)) if status == ST_ACCEPTED else created
        relations.append((uuid7_at(created), created, updated, ids[src], ids[dst], status))
        if status == ST_ACCEPTED:
            accepted_at[pair] = updated

    # ---------- привычки и отметки ----------
    habits, logs, habit_info = [], [], {}
    for spec in HABITS:
        tz = PEOPLE[spec.owner].tz
        today = local_today(tz)
        start = today - timedelta(days=spec.started_days_ago)
        created = at_local(start, rng.randint(8, 20), rng.randint(0, 59), tz)
        require(created > joined[spec.owner], f"привычка {spec.title!r} старше аккаунта {spec.owner}")
        hid = uuid7_at(created)

        rows = []
        for d in sorted(pick_done_days(spec, start, today, rng)):
            ts = at_local(d, rng.randint(*spec.window), rng.randint(0, 59), tz, rng.randint(0, 59))
            if created <= ts <= NOW:  # отметки из будущего или раньше создания привычки не бывают
                rows.append((uuid7_at(ts), ts, ts, hid, ids[spec.owner], d))
        current, best, last_day = streaks({r[5] for r in rows}, today)
        expires = at_local(last_day + timedelta(days=2), 0, 0, tz) if current > 0 else None
        notify = [dtime(int(x[:2]), int(x[3:])) for x in spec.notify]
        require(len(notify) <= 3, f"привычка {spec.title!r}: больше 3 напоминаний")

        habits.append((
            hid, created, rows[-1][1] if rows else created, ids[spec.owner], spec.title, spec.color,
            current, expires, best, spec.visibility, start, notify, last_reminder(notify, tz),
        ))
        logs.extend(rows)
        habit_info[(spec.owner, spec.title)] = (hid, created, spec.visibility)

    # ---------- ревью ----------
    reviews, seen_reviews = [], set()
    for reviewer, owner, title, rate, comment, days_ago in REVIEWS:
        hid, hcreated, visibility = habit_info[(owner, title)]
        pair = frozenset((reviewer, owner))
        require(pair in accepted_at, f"ревью: {reviewer} и {owner} не друзья")
        require(visibility != VIS_PRIVATE, f"ревью: привычка {title!r} приватная")
        require((reviewer, hid) not in seen_reviews, f"ревью: {reviewer} дважды оценил {title!r}")
        seen_reviews.add((reviewer, hid))
        tz = PEOPLE[reviewer].tz
        ts = at_local(local_today(tz) - timedelta(days=days_ago), rng.randint(9, 22), rng.randint(0, 59), tz)
        require(ts > max(hcreated, accepted_at[pair]), f"ревью {reviewer} -> {title!r}: раньше привычки или дружбы")
        reviews.append((uuid7_at(ts), ts, ts, ids[reviewer], hid, comment, rate))

    # ---------- переписки ----------
    messages = []
    for (k1, k2), sessions in DIALOGS.items():
        pair = frozenset((k1, k2))
        require(pair in accepted_at, f"переписка {k1}/{k2}: они не друзья")
        tz, prev_end = PEOPLE[k1].tz, None
        for s in sessions:
            hh, mm = map(int, s.at.split(":"))
            t = at_local(local_today(tz) - timedelta(days=s.days_ago), hh, mm, tz, rng.randint(0, 40))
            stamps = [t]
            for _, text in s.lines[1:]:
                t += timedelta(seconds=15 + len(text) * 0.9 + rng.uniform(5, 90))  # время на набор текста
                stamps.append(t)
            while stamps[-1] > NOW - timedelta(seconds=30):  # разговор «сегодня» не может быть в будущем
                stamps = [x - timedelta(days=1) for x in stamps]
            require(stamps[0] > accepted_at[pair], f"переписка {k1}/{k2}: сообщение раньше дружбы")
            require(prev_end is None or stamps[0] > prev_end, f"переписка {k1}/{k2}: разговоры не по порядку")
            prev_end = stamps[-1]
            for idx, ((who, text), ts) in enumerate(zip(s.lines, stamps)):
                require(who in pair, f"переписка {k1}/{k2}: реплика от {who}")
                other = k2 if who == k1 else k1
                is_read = idx < len(s.lines) - s.unread
                read_at = min(NOW, ts + timedelta(seconds=rng.uniform(40, 3 * 3600))) if is_read else None
                messages.append((uuid7_at(ts), ts, read_at or ts, ids[who], ids[other], text, is_read, read_at))

    return MainDataset(users, relations, habits, logs, reviews, messages, pool_users)


def achievements_rows() -> list[tuple]:
    created = NOW - timedelta(days=400)  # справочник заводится раньше любого пользователя
    rows = []
    for i, a in enumerate(achievements_data):
        rule_type = getattr(a["rule_type"], "value", a["rule_type"])
        require(len(a["name"]) <= 25, f"ачивка {a['name']!r}: имя длиннее 25 символов (achievements.name = String(25))")
        ts = created + timedelta(minutes=i)
        rows.append((
            uuid7_at(ts), ts, ts, a["name"], str(rule_type), int(a["rule_value"]), a["color_hex"],
            a["requirement"], a["description"], a.get("icon_url", ""),
        ))
    return rows


# =====================================================================
#  SQL: СЛУЧАЙНЫЕ ПОЛЬЗОВАТЕЛИ И ВСЁ, ЧТО С НИМИ СВЯЗАНО
# =====================================================================
# Токены в двойных фигурных скобках Python подставляет до отправки в БД (см. render_script).
# К моменту запуска уже существуют временные таблицы: _dict (словари), _tpl (шаблоны переписок),
# _fixed (основные аккаунты и их окружение, вставленные из Python).
script = r"""
-- Postgres 14+ кэширует результат LATERAL-вызова по ключу параметров (Memoize) и не замечает random() внутри:
-- у всех пользователей получалось бы одинаковое число привычек/связей. На время транзакции выключаем.
-- На старых версиях параметра нет, ошибка гасится.
DO $$ BEGIN PERFORM set_config('enable_memoize', 'off', true); EXCEPTION WHEN OTHERS THEN NULL; END $$;

-- ---------- UUIDv7 из заданного времени (временная функция, живёт до конца сессии) ----------
CREATE OR REPLACE FUNCTION pg_temp.uuid7_at(ts timestamptz) RETURNS uuid
LANGUAGE sql VOLATILE AS $$
  SELECT encode(
           set_bit(set_bit(
             overlay(uuid_send(gen_random_uuid())
                     PLACING substring(int8send(floor(extract(epoch FROM ts) * 1000)::bigint) FROM 3)
                     FROM 1 FOR 6),
             52, 1), 53, 1),
           'hex')::uuid
$$;

-- ---------- ПУЛ ПОЛЬЗОВАТЕЛЕЙ ----------
-- _u: все, кому генерируются связи и активность (случайные + окружение основных аккаунтов + сами основные).
-- rn: сквозной номер для быстрых случайных выборок.
-- is_main: основные аккаунты. Их связи, привычки, переписки и ревью уже вставлены из Python,
-- поэтому в случайной генерации они не участвуют, но ачивки им считаются по реальным данным ниже.
CREATE TEMP TABLE _u (
  rn int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id uuid NOT NULL,
  since timestamptz NOT NULL,   -- с какого момента аккаунт "существует" для генерации дат
  tz text NOT NULL,
  is_main boolean NOT NULL
) ON COMMIT DROP;

-- uid нужен до вставки: он входит в путь аватарки pfp/<user_id>/<hex>.<ext>
-- (тот же формат, что выдаёт MinioService и проверяет FILE_KEY_RE).
-- Логин и почта собираются из имён (как у настоящих людей); столкнувшиеся строки молча пропускаются (ON CONFLICT).
WITH g AS (
  SELECT i,
         now() - (interval '3 days' + random() * interval '362 days') AS ts,
         random() < 0.52 AS female,
         random() AS r_fn, random() AS r_ln, random() AS r_sn, random() AS r_pat, random() AS r_dig,
         random() AS r_dom, random() AS r_mail,
         random() AS r_tg, random() AS r_link, random() AS r_pfp,
         md5(random()::text || i::text) AS pfp_name,
         (ARRAY['webp','webp','png','jpeg'])[1 + floor(random() * 4)::int] AS pfp_ext
  FROM generate_series(1, {{N_USERS}}) AS i
), n AS (
  SELECT g.*,
         CASE WHEN g.female THEN d.names_f[1 + floor(g.r_fn * cardinality(d.names_f))::int]
              ELSE d.names_m[1 + floor(g.r_fn * cardinality(d.names_m))::int] END AS fn,
         d.names_short[1 + floor(g.r_sn * cardinality(d.names_short))::int] AS sn,
         d.surnames[1 + floor(g.r_ln * cardinality(d.surnames))::int]
           || CASE WHEN g.female THEN 'a' ELSE '' END AS ln,
         d.domains[1 + floor(g.r_dom * cardinality(d.domains))::int] AS domain,
         lpad(floor(g.r_dig * 100)::int::text, 2, '0') AS dd,
         (1985 + floor(g.r_dig * 22)::int)::text AS yy,
         d.themes[1 + floor(random() * cardinality(d.themes))::int] AS theme,
         d.tzs[1 + floor(random() * cardinality(d.tzs))::int] AS tz
  FROM g CROSS JOIN _dict d
), g2 AS (
  SELECT n.*,
         left(lower(CASE
           WHEN n.r_pat < 0.30 THEN n.fn || '_' || n.ln
           WHEN n.r_pat < 0.45 THEN n.fn || n.ln || n.dd
           WHEN n.r_pat < 0.58 THEN n.fn || '_' || n.yy
           WHEN n.r_pat < 0.68 THEN left(n.fn, 1) || n.ln
           WHEN n.r_pat < 0.78 THEN n.ln || '_' || left(n.fn, 1)
           WHEN n.r_pat < 0.90 THEN n.sn || n.dd
           ELSE n.fn || n.dd END), 16) AS username
  FROM n
), g3 AS (
  SELECT g2.*, pg_temp.uuid7_at(g2.ts) AS uid FROM g2
), ins AS (
  INSERT INTO users (id, created_at, updated_at, username, email, password_hash, pfp_url, theme, timezone,
                     telegram_chat_id, telegram_link_token_hash, telegram_link_expires_at)
  SELECT g3.uid, g3.ts, g3.ts, g3.username,
         CASE WHEN g3.r_mail < 0.6 THEN g3.username ELSE replace(g3.username, '_', '.') END || '@' || g3.domain,
         -- формат argon2id, но пароль по такому хешу не подобрать: войти под случайными пользователями нельзя
         '$argon2id$v=19$m=65536,t=3,p=4$'
           || rtrim(encode(decode(md5(random()::text), 'hex'), 'base64'), '=') || '$'
           || rtrim(encode(decode(md5(random()::text) || md5(random()::text), 'hex'), 'base64'), '='),
         CASE WHEN g3.r_pfp < {{PFP_SHARE}}
              THEN '{{PFP_PREFIX}}pfp/' || g3.uid::text || '/' || g3.pfp_name || '.' || g3.pfp_ext END,
         g3.theme, g3.tz,
         CASE WHEN g3.r_tg < 0.3 THEN 100000000 + floor(random() * 9000000000)::bigint END,
         CASE WHEN g3.r_tg >= 0.3 AND g3.r_link < 0.1 THEN md5(random()::text) || md5(random()::text) END,
         CASE WHEN g3.r_tg >= 0.3 AND g3.r_link < 0.1 THEN now() + random() * interval '1 hour' END
  FROM g3
  ON CONFLICT DO NOTHING
  RETURNING id, created_at, timezone
)
INSERT INTO _u (id, since, tz, is_main)
SELECT id, created_at, timezone, false FROM ins;

INSERT INTO _u (id, since, tz, is_main)
SELECT id, since, tz, is_main FROM _fixed;

CREATE UNIQUE INDEX ON _u (id);

-- ---------- REFRESH-ТОКЕНЫ ----------
-- Только у пользователей без основных аккаунтов (у них токены появятся при настоящем логине).
-- Хеши случайные: залогиниться такими токенами нельзя, они нужны для объёма и проверки очистки истёкших.
-- Часть токенов истекла по сроку, ~30% отозваны (logout). MAX_REFRESH_TOKENS = 0 отключает блок.
INSERT INTO refresh_tokens (id, created_at, updated_at, user_id, token_hash, expires_at, revoked_at)
SELECT pg_temp.uuid7_at(t.ts), t.ts, t.ts, t.user_id,
       md5(random()::text || t.user_id::text) || md5(random()::text),
       t.ts + make_interval(days => {{REFRESH_TTL_DAYS}}),
       CASE WHEN t.r_rev < 0.3 THEN least(now(), t.ts + random() * interval '10 days') END
-- Число токенов считается во вложенном запросе uu (random() в списке выбора = своё значение на каждого пользователя).
-- Если поставить random() прямо в аргумент generate_series, он не зависит от пользователя, Postgres вычислит его
-- один раз на весь запрос, и у всех будет одинаковое число токенов (или ни у кого).
FROM (
  SELECT uu.id AS user_id,
         uu.since + (now() - uu.since) * random() AS ts,
         random() AS r_rev
  FROM (
    SELECT u.id, u.since, floor(random() * ({{MAX_REFRESH_TOKENS}} + 1))::int AS cnt
    FROM _u u
    WHERE NOT u.is_main
  ) uu
  CROSS JOIN LATERAL generate_series(1, uu.cnt) AS g
) t;

-- ---------- ДРУЖБА / ЗАЯВКИ / БЛОКИРОВКИ ----------
-- Для каждой неупорядоченной пары максимум ОДНА строка, поэтому инварианты UserRelation соблюдены
-- (нет дружбы + блокировки одновременно, нет встречных pending, нет self-связей).
-- Пары с основными аккаунтами не генерируются: их связи заданы вручную в Python.
-- acc_ts: когда заявку приняли (в updated_at принятой связи); created_at = когда отправили.
CREATE TEMP TABLE _rel ON COMMIT DROP AS
WITH quota AS (
  SELECT u.rn AS a_rn,
         CASE WHEN u.is_main THEN 0 ELSE floor(random() * 2 * {{REL_PER_USER}})::int END AS cnt
  FROM _u u
), picks AS (
  SELECT q.a_rn,
         1 + floor(random() * (SELECT count(*) FROM _u))::int AS b_rn
  FROM quota q
  CROSS JOIN LATERAL generate_series(1, q.cnt) AS g
), pairs AS (
  SELECT DISTINCT least(p.a_rn, p.b_rn) AS lo, greatest(p.a_rn, p.b_rn) AS hi
  FROM picks p
  JOIN _u a ON a.rn = p.a_rn
  JOIN _u b ON b.rn = p.b_rn
  WHERE p.a_rn <> p.b_rn AND NOT a.is_main AND NOT b.is_main
), rnd AS (
  SELECT lo, hi, random() AS r_dir, random() AS r_st, random() AS r_ts, random() AS r_acc FROM pairs
)
SELECT q.*,
       CASE WHEN q.status = '{{ST_ACCEPTED}}' THEN least(now(), q.ts + q.r_acc * interval '2 days') END AS acc_ts
FROM (
  SELECT CASE WHEN r_dir < 0.5 THEN lo ELSE hi END AS u_rn,   -- кто отправил / кто заблокировал
         CASE WHEN r_dir < 0.5 THEN hi ELSE lo END AS t_rn,
         CASE WHEN r_st < 0.75 THEN '{{ST_ACCEPTED}}'
              WHEN r_st < 0.97 THEN '{{ST_PENDING}}'
              ELSE '{{ST_BLOCKED}}' END AS status,
         greatest(ul.since, uh.since) + r_ts * (now() - greatest(ul.since, uh.since)) AS ts,
         r_acc
  FROM rnd
  JOIN _u ul ON ul.rn = rnd.lo
  JOIN _u uh ON uh.rn = rnd.hi
) q;

INSERT INTO user_relations (id, created_at, updated_at, user_id, target_id, status)
SELECT pg_temp.uuid7_at(r.ts), r.ts, coalesce(r.acc_ts, r.ts), a.id, b.id, r.status
FROM _rel r
JOIN _u a ON a.rn = r.u_rn
JOIN _u b ON b.rn = r.t_rn;

-- друзья в обе стороны (для переписки и ревью)
CREATE TEMP TABLE _friends ON COMMIT DROP AS
SELECT u_rn AS a_rn, t_rn AS b_rn, acc_ts AS ts FROM _rel WHERE status = '{{ST_ACCEPTED}}'
UNION ALL
SELECT t_rn, u_rn, acc_ts FROM _rel WHERE status = '{{ST_ACCEPTED}}';
CREATE INDEX ON _friends (a_rn);

-- ---------- СООБЩЕНИЯ (только между друзьями) ----------
-- Диалог = несколько разговоров. Разговор = шаблон из _tpl: реплики по очереди, с паузами на набор текста.
-- Начало разговора: днём (09:00-22:00), ближе к "сейчас" чаще. Всё старше 2 дней прочитано;
-- в свежих разговорах (~40%) последние 1-2 сообщения ещё не прочитаны.
-- id сообщений = UUIDv7 от created_at, курсорная пагинация работает.
CREATE TEMP TABLE _conv ON COMMIT DROP AS
SELECT row_number() OVER () AS conv_id,
       c.u_rn, c.t_rn, c.tpl_id, c.flip, c.unread_conv, c.k_unread,
       least(now() - interval '2 hours',
             greatest(c.since, date_trunc('day', c.raw_ts) + interval '9 hours' + c.r_h * interval '13 hours')) AS start_ts
FROM (
  SELECT d.u_rn, d.t_rn, d.since,
         d.since + greatest(now() - d.since - interval '2 hours', interval '0') * power(random(), 0.6) AS raw_ts,
         random() AS r_h,
         1 + floor(random() * (SELECT count(*) FROM _tpl))::int AS tpl_id,
         random() < 0.5 AS flip,
         random() < 0.4 AS unread_conv,
         1 + floor(random() * 2)::int AS k_unread
  FROM (
    SELECT r.u_rn, r.t_rn, r.acc_ts AS since,
           1 + floor(random() * {{MAX_CONVERSATIONS}})::int AS n_conv
    FROM _rel r
    WHERE r.status = '{{ST_ACCEPTED}}' AND random() < {{DIALOG_SHARE}}
  ) d
  CROSS JOIN LATERAL generate_series(1, d.n_conv) AS g
) c;

INSERT INTO messages (id, created_at, updated_at, sender_id, receiver_id, content, is_read, read_at)
SELECT pg_temp.uuid7_at(m.ts), m.ts,
       CASE WHEN m.is_read THEN least(now(), m.ts + m.r_rd * interval '3 hours') ELSE m.ts END,
       CASE WHEN (m.side = 'a') = m.flip THEN ua.id ELSE ub.id END,
       CASE WHEN (m.side = 'a') = m.flip THEN ub.id ELSE ua.id END,
       m.txt, m.is_read,
       CASE WHEN m.is_read THEN least(now(), m.ts + m.r_rd * interval '3 hours') END
FROM (
  SELECT y.*,
         NOT (y.start_ts > now() - interval '2 days' AND y.unread_conv AND y.ord > y.n_lines - y.k_unread) AS is_read
  FROM (
    SELECT x.*,
           least(now(), x.start_ts + make_interval(secs => sum(x.gap) OVER (PARTITION BY x.conv_id ORDER BY x.ord))) AS ts
    FROM (
      SELECT c.conv_id, c.u_rn, c.t_rn, c.flip, c.start_ts, c.unread_conv, c.k_unread,
             t.ord, left(t.line, 1) AS side, substr(t.line, 3) AS txt, cardinality(p.lines) AS n_lines,
             CASE WHEN t.ord = 1 THEN 0 ELSE 15 + length(t.line) * 0.8 + random() * 150 END AS gap,
             random() AS r_rd
      FROM _conv c
      JOIN _tpl p ON p.id = c.tpl_id
      CROSS JOIN LATERAL unnest(p.lines) WITH ORDINALITY AS t(line, ord)
    ) x
  ) y
) m
JOIN _u ua ON ua.rn = m.u_rn
JOIN _u ub ON ub.rn = m.t_rn;

-- ---------- ПРИВЫЧКИ ----------
-- _h: заготовка (id привычки известен заранее, нужен для логов). Названия у одного пользователя не повторяются.
-- p = вероятность отметки в подходящий день: у ~25% привычек 95-100% (длинные стрики), у остальных 20-90%.
-- mode: 0 = каждый день, 1 = только по будням.
CREATE TEMP TABLE _h ON COMMIT DROP AS
WITH cnt AS (
  SELECT u.rn, u.id, u.tz, u.since,
         (now() AT TIME ZONE u.tz)::date AS today,
         1 + floor(random() * {{MAX_HABITS}})::int AS n
  FROM _u u
  WHERE NOT u.is_main
), pick AS (
  SELECT c.*, t.title,
         row_number() OVER (PARTITION BY c.rn ORDER BY random()) AS k
  FROM cnt c
  CROSS JOIN _dict d
  CROSS JOIN LATERAL unnest(d.habit_titles) AS t(title)
), raw AS (
  SELECT p.rn AS creator_rn, p.id AS creator_id, p.tz, p.since, p.today, p.title AS base_title,
         d.colors[1 + floor(random() * cardinality(d.colors))::int] AS color,
         d.visibilities[1 + floor(random() * cardinality(d.visibilities))::int] AS visibility,
         random() AS r_start, random() AS r_cr, random() AS r_p, random() AS r_p2,
         random() AS r_rem, random() AS r_mode,
         floor(random() * 4)::int AS nt
  FROM pick p
  CROSS JOIN _dict d
  WHERE p.k <= p.n
), calc AS (
  SELECT raw.*,
         raw.today - floor(raw.r_start * greatest(1, least({{HISTORY_DAYS}}, raw.today - raw.since::date)))::int AS start_date
  FROM raw
), calc2 AS (
  SELECT calc.*,
         least(now(), (calc.start_date::timestamp + interval '7 hours' + calc.r_cr * interval '14 hours') AT TIME ZONE calc.tz) AS created_at
  FROM calc
)
SELECT pg_temp.uuid7_at(created_at) AS hid,
       calc2.*,
       CASE WHEN r_p < 0.25 THEN 0.95 + 0.05 * r_p2 ELSE 0.2 + 0.7 * r_p2 END AS p,
       CASE WHEN r_mode < 0.75 THEN 0 ELSE 1 END AS mode
FROM calc2;

-- current_streak_days / max_streak_days / streak_expires_at заполняются ниже, когда будут готовы отметки
INSERT INTO habits (id, created_at, updated_at, creator_id, title, color_hex, visibility, start_date,
                    notification_times, last_reminded_at)
SELECT h.hid, h.created_at, h.created_at, h.creator_id,
       h.base_title, h.color, h.visibility, h.start_date,
       ARRAY(SELECT q.t
             FROM (SELECT DISTINCT make_time(6 + floor(random() * 17)::int,
                                             (ARRAY[0,15,30,45])[1 + floor(random() * 4)::int], 0) AS t
                   FROM generate_series(1, h.nt)) q
             ORDER BY q.t),
       CASE WHEN h.nt > 0 AND h.r_rem < 0.7 THEN now() - random() * interval '24 hours' END
FROM _h h;

-- ---------- ОТМЕТКИ ----------
-- Случайные числа обязаны жить в LATERAL-подзапросе, привязанном к привычке: условие random() < h.p в WHERE
-- ссылалось бы только на h, и Postgres применил бы его один раз на привычку, а не на день.
-- Время отметки: 06:00-23:00 по часовому поясу пользователя; id = UUIDv7 от него же.
INSERT INTO habit_logs (id, created_at, updated_at, habit_id, user_id, completed_date)
SELECT pg_temp.uuid7_at(x.ts), x.ts, x.ts, x.habit_id, x.user_id, x.dt
FROM (
  SELECT h.hid AS habit_id, h.creator_id AS user_id, h.created_at AS hc, d.dt,
         least(now(), (d.dt::timestamp + interval '6 hours' + d.r_t * interval '17 hours') AT TIME ZONE h.tz) AS ts
  FROM _h h
  CROSS JOIN LATERAL (
    SELECT h.start_date + k AS dt, random() AS r_p, random() AS r_t
    FROM generate_series(0, h.today - h.start_date) AS k
  ) d
  WHERE d.r_p < h.p AND (h.mode = 0 OR extract(isodow FROM d.dt) <= 5)
) x
WHERE x.ts >= x.hc;   -- отметка не раньше создания привычки

-- ---------- СЕРИИ (стрики) ----------
-- _runs: все непрерывные серии отметок (по паре привычка + пользователь) у всех пользователей из _u,
-- в том числе у основных аккаунтов. Классика "gaps and islands":
-- дата минус порядковый номер отметки одинакова внутри одной серии.
CREATE TEMP TABLE _runs ON COMMIT DROP AS
SELECT x.habit_id, x.user_id, count(*) AS len,
       min(x.completed_date) AS first_d, max(x.completed_date) AS last_d
FROM (
  SELECT l.habit_id, l.user_id, l.completed_date,
         l.completed_date - (row_number() OVER (PARTITION BY l.habit_id, l.user_id
                                                ORDER BY l.completed_date))::int AS grp
  FROM habit_logs l
  JOIN _u u ON u.id = l.user_id
) x
GROUP BY x.habit_id, x.user_id, x.grp;

-- Стрик привычки считается по отметкам создателя (у основных аккаунтов он уже посчитан в Python).
-- current: серия, которая заканчивается сегодня или вчера (если сегодня ещё не отмечено), иначе 0;
-- max: самая длинная серия за всё время; "сегодня" берётся в часовом поясе создателя.
-- streak_expires_at: конец дня, следующего за последней отметкой серии (до этого момента стрик можно продолжить).
UPDATE habits hb
SET current_streak_days = s.cur,
    max_streak_days = s.mx,
    streak_expires_at = CASE WHEN s.cur > 0 THEN ((s.cur_last + 2)::timestamp AT TIME ZONE s.tz) END
FROM (
  SELECT r.habit_id, h.tz,
         max(r.len) AS mx,
         coalesce(max(r.len) FILTER (WHERE r.last_d >= h.today - 1), 0) AS cur,
         max(r.last_d) FILTER (WHERE r.last_d >= h.today - 1) AS cur_last
  FROM _runs r
  JOIN _h h ON h.hid = r.habit_id AND h.creator_id = r.user_id
  GROUP BY r.habit_id, h.tz
) s
WHERE hb.id = s.habit_id;

-- ---------- ДОСТИЖЕНИЯ ----------
-- Справочник achievements уже заполнен из Python (src/achievements/seed_achievements_db.py).
-- Выдаём ВСЕ ачивки из таблицы с известным rule_type пользователям из _u, условие которых реально выполнено
-- по данным в БД (включая основные аккаунты). Время получения = момент, когда пользователь достиг порога:
--   STREAK        : день, когда первая подходящая серия дошла до rule_value (+ случайное время в этот день)
--   FRIENDS_COUNT : момент, когда принята заявка rule_value-го друга
--   TOTAL_HABITS  : момент создания rule_value-й привычки
-- Случайные числа считаются один раз в _ach_ev, а не размазываются по INSERT.
CREATE TEMP TABLE _ach_ev ON COMMIT DROP AS
SELECT r.user_id, a.id AS achievement_id,
       least(now(), (((min(r.first_d) + (a.rule_value - 1))::timestamp
                      + interval '7 hours' + random() * interval '16 hours') AT TIME ZONE u.tz)) AS ts
FROM _runs r
JOIN _u u ON u.id = r.user_id
JOIN achievements a ON a.rule_type = 'STREAK' AND a.rule_value > 0 AND r.len >= a.rule_value
GROUP BY r.user_id, a.id, a.rule_value, u.tz
UNION ALL
SELECT f.uid, a.id, f.ts
FROM (
  SELECT x.uid, x.ts, row_number() OVER (PARTITION BY x.uid ORDER BY x.ts) AS n
  FROM (
    SELECT rl.user_id AS uid, rl.updated_at AS ts FROM user_relations rl WHERE rl.status = '{{ST_ACCEPTED}}'
    UNION ALL
    SELECT rl.target_id, rl.updated_at FROM user_relations rl WHERE rl.status = '{{ST_ACCEPTED}}'
  ) x
  JOIN _u u ON u.id = x.uid
) f
JOIN achievements a ON a.rule_type = 'FRIENDS_COUNT' AND a.rule_value > 0 AND a.rule_value = f.n
UNION ALL
SELECT h.creator_id, a.id, h.created_at
FROM (
  SELECT hb.creator_id, hb.created_at,
         row_number() OVER (PARTITION BY hb.creator_id ORDER BY hb.created_at) AS n
  FROM habits hb
  JOIN _u u ON u.id = hb.creator_id
) h
JOIN achievements a ON a.rule_type = 'TOTAL_HABITS' AND a.rule_value > 0 AND a.rule_value = h.n;

INSERT INTO user_achievements (id, created_at, updated_at, user_id, achievement_id)
SELECT pg_temp.uuid7_at(e.ts), e.ts, e.ts, e.user_id, e.achievement_id
FROM _ach_ev e
ON CONFLICT (user_id, achievement_id) DO NOTHING;

-- ---------- РЕВЬЮ (друг оценивает привычку друга целиком; 1 = пуш, 0 = шейм) ----------
-- Ревью привязано к привычке, а не к отметке: пара (ревьюер, привычка) = максимум одно ревью (uq_reviewer_id_habit_log).
-- Ревьюер: принятый друг создателя. Приватные привычки друзья не видят, их не ревьюим.
-- Перебираются ВСЕ пары (привычка, друг создателя), и каждая получает ревью с вероятностью REVIEW_RATE,
-- поэтому дублей быть не может. Время ревью: между моментом, когда привычка создана и люди уже дружат, и "сейчас".
CREATE TEMP TABLE _rv ON COMMIT DROP AS
SELECT h.hid AS habit_id, f.b_rn AS reviewer_rn,
       greatest(h.created_at, f.ts) AS since,
       random() AS r_rate, random() AS r_c, random() AS r_pick, random() AS r_ts
FROM _h h
JOIN _friends f ON f.a_rn = h.creator_rn
WHERE h.visibility <> '{{VIS_PRIVATE}}'
  AND random() < {{REVIEW_RATE}};

INSERT INTO reviews (id, created_at, updated_at, reviewer_id, habit_id, comment, rate)
SELECT pg_temp.uuid7_at(q.ts), q.ts, q.ts, rv.id, q.habit_id, q.cmt, q.rate
FROM (
  SELECT v.habit_id, v.reviewer_rn,
         v.since + v.r_ts * (now() - v.since) AS ts,
         CASE WHEN v.r_rate < 0.8 THEN 1 ELSE 0 END AS rate,
         CASE WHEN v.r_c < 0.5 THEN NULL
              WHEN v.r_rate < 0.8 THEN d.push_comments[1 + floor(v.r_pick * cardinality(d.push_comments))::int]
              ELSE d.shame_comments[1 + floor(v.r_pick * cardinality(d.shame_comments))::int]
         END AS cmt
  FROM _rv v CROSS JOIN _dict d
) q
JOIN _u rv ON rv.rn = q.reviewer_rn;
"""

TABLES = (
    "users, refresh_tokens, user_relations, messages, habits, shared_habit_users, "
    "habit_logs, achievements, user_achievements, reviews"
)

SUMMARY_SQL = """
SELECT 'users' AS tbl, count(*) AS rows FROM users
UNION ALL SELECT 'refresh_tokens', count(*) FROM refresh_tokens
UNION ALL SELECT 'user_relations', count(*) FROM user_relations
UNION ALL SELECT 'messages', count(*) FROM messages
UNION ALL SELECT 'habits', count(*) FROM habits
UNION ALL SELECT 'habit_logs', count(*) FROM habit_logs
UNION ALL SELECT 'reviews', count(*) FROM reviews
UNION ALL SELECT 'achievements', count(*) FROM achievements
UNION ALL SELECT 'user_achievements', count(*) FROM user_achievements
UNION ALL SELECT 'shared_habit_users', count(*) FROM shared_habit_users
"""

# ---------- вставки основных аккаунтов (из Python) ----------
INSERT_USER = """
INSERT INTO users (id, created_at, updated_at, username, email, password_hash, theme, timezone, pfp_url)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
"""
INSERT_RELATION = """
INSERT INTO user_relations (id, created_at, updated_at, user_id, target_id, status)
VALUES ($1, $2, $3, $4, $5, $6)
"""
INSERT_HABIT = """
INSERT INTO habits (id, created_at, updated_at, creator_id, title, color_hex, current_streak_days,
                    streak_expires_at, max_streak_days, visibility, start_date, notification_times, last_reminded_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
"""
INSERT_LOG = """
INSERT INTO habit_logs (id, created_at, updated_at, habit_id, user_id, completed_date)
VALUES ($1, $2, $3, $4, $5, $6)
"""
INSERT_REVIEW = """
INSERT INTO reviews (id, created_at, updated_at, reviewer_id, habit_id, comment, rate)
VALUES ($1, $2, $3, $4, $5, $6, $7)
"""
INSERT_MESSAGE = """
INSERT INTO messages (id, created_at, updated_at, sender_id, receiver_id, content, is_read, read_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
"""
INSERT_ACHIEVEMENT = """
INSERT INTO achievements (id, created_at, updated_at, name, rule_type, rule_value, color_hex,
                          requirement, description, icon_url)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
ON CONFLICT (name) DO NOTHING
"""


async def upload_default_avatars():
    print("[+] Загрузка дефолтных аватарок в MinIO . . .")
    settings = get_minio_settings()
    
    # Путь к папке assets на фронтенде (относительно BASE_DIR)
    assets_dir = BASE_DIR / "frontend" / "src" / "assets" / "defaults"
    
    # Словарь: ключ в MinIO -> путь к локальному файлу
    files_to_upload = {
        "defaults/alexandra-default-pfp.jpg": assets_dir / "alexandra-default-pfp.jpg",
        "defaults/dima-default-pfp.jpg": assets_dir / "dima-default-pfp.jpg",
        "defaults/igor-bykov-default.jpg": assets_dir / "igor-bykov-default.jpg",
        "defaults/marina-k-default.jpg": assets_dir / "marina-k-default.jpg",
        "defaults/andrey-devops.jpg": assets_dir / "andrey-devops.jpg",
        "defaults/nikita-sokolov-default.jpg": assets_dir / "nikita-sokolov-default.jpg",
        "defaults/anna-vlasova-default.jpg": assets_dir / "anna-vlasova-default.jpg",
        "defaults/artem-zhukov-default.jpg": assets_dir / "artem-zhukov-default.jpg",
        "defaults/vlad-romanov-default.jpg": assets_dir / "vlad-romanov-default.jpg",
        "defaults/default-pfp.webp": assets_dir / "default-pfp.webp",
    }
    
    session = aioboto3.Session(
        aws_access_key_id=settings.root_user,
        aws_secret_access_key=settings.root_password,
        region_name="us-east-1",
    )
    
    async with session.client("s3", endpoint_url=settings.endpoint) as s3:
        for s3_key, file_path in files_to_upload.items():
            if file_path.exists():
                # Определяем Content-Type по расширению
                content_type = "image/webp" if file_path.suffix == ".webp" else "image/jpeg"
                with open(file_path, "rb") as f:
                    await s3.put_object(
                        Bucket=settings.bucket_name,
                        Key=s3_key,
                        Body=f,
                        ContentType=content_type
                    )
                print(f"  Загружен: {s3_key}")
            else:
                print(f"  [-] Файл не найден: {file_path}")


def validate_users() -> None:
    if tuple(USERS) != tuple(MAIN_KEYS):
        raise ValueError(f"[-] В USERS должны быть ровно ключи {', '.join(MAIN_KEYS)}, сейчас: {', '.join(USERS)}")

    for key, user in USERS.items():
        for field in ("username", "email", "password"):
            if not str(user.get(field, "")).strip():
                raise ValueError(f"[-] USERS[{key!r}]: поле {field!r} должно быть заполнено!")
        if len(user["username"]) > USERNAME_MAX_LEN:
            raise ValueError(f"[-] USERS[{key!r}]: username длиннее {USERNAME_MAX_LEN} символов")

    for field in ("username", "email"):
        values = [user[field] for user in USERS.values()]
        if len(set(values)) != len(values):
            raise ValueError(f"[-] В USERS у разных аккаунтов совпадает {field}!")


async def hash_users() -> dict[str, str]:
    # argon2 считается в потоках (create_password -> asyncio.to_thread), оба пароля хешируются параллельно
    async with asyncio.TaskGroup() as tg:
        tasks = {MAIN_KEYS[key]: tg.create_task(create_password(user["password"])) for key, user in USERS.items()}
    return {key: task.result() for key, task in tasks.items()}


def pool_urls() -> dict[str, str]:
    # адреса аватарок строим из тех же настроек MinIO, что и сервис; если аватарок нет, настройки не нужны
    if PFP_SHARE <= 0:
        return {"PFP_PREFIX": ""}
    from core.config import get_minio_settings

    minio = get_minio_settings()
    return {"PFP_PREFIX": f"{minio.effective_public_url}/{minio.bucket_name}/"}


def render_script() -> str:
    enums = {
        "ST_PENDING": ST_PENDING,
        "ST_ACCEPTED": ST_ACCEPTED,
        "ST_BLOCKED": ST_BLOCKED,
        "VIS_PRIVATE": VIS_PRIVATE,
    }
    for key, val in enums.items():
        if not re.fullmatch(r"\w+", val):  # значения идут в SQL внутри кавычек
            raise ValueError(f"[-] {key} = {val!r}: допустимы только буквы, цифры и _")

    urls = pool_urls()
    for key, val in urls.items():
        if "'" in val or "{{" in val:  # значения идут в SQL внутри кавычек
            raise ValueError(f"[-] {key} = {val!r}: нельзя использовать ' и {{")

    values = {
        "N_USERS": N_USERS,
        "REL_PER_USER": REL_PER_USER,
        "MAX_HABITS": MAX_HABITS,
        "HISTORY_DAYS": HISTORY_DAYS,
        "DIALOG_SHARE": DIALOG_SHARE,
        "MAX_CONVERSATIONS": MAX_CONVERSATIONS,
        "REVIEW_RATE": REVIEW_RATE,
        "PFP_SHARE": PFP_SHARE,
        "MAX_REFRESH_TOKENS": MAX_REFRESH_TOKENS,
        "REFRESH_TTL_DAYS": REFRESH_TTL_DAYS,
        **urls,
        **enums,
    }
    sql = script
    for key, val in values.items():
        sql = sql.replace("{{" + key + "}}", str(val))

    left = sorted(set(re.findall(r"\{\{\w+\}\}", sql)))
    if left:
        raise RuntimeError(f"[-] В SQL остались неподставленные токены: {', '.join(left)}")
    return sql


async def ensure_clean_start(conn: asyncpg.Connection) -> None:
    usernames = [p.username for p in PEOPLE.values()]
    emails = [p.email for p in PEOPLE.values()]
    rows = await conn.fetch(
        "SELECT username, email FROM users WHERE username = ANY($1::text[]) OR email = ANY($2::text[])",
        usernames,
        emails,
    )
    if rows:
        taken = ", ".join(f"{r['username']} <{r['email']}>" for r in rows)
        raise RuntimeError(
            f"в БД уже есть аккаунты из набора: {taken}. "
            "Данные основных аккаунтов нельзя наложить на существующие: запусти с --wipe "
            "(если их создавал этот скрипт) или удали аккаунты вручную."
        )


async def insert_main_dataset(conn: asyncpg.Connection, data: MainDataset) -> None:
    # порядок важен: внешние ключи
    await conn.executemany(INSERT_USER, data.users)
    await conn.executemany(INSERT_RELATION, data.relations)
    await conn.executemany(INSERT_HABIT, data.habits)
    await conn.executemany(INSERT_LOG, data.logs)
    await conn.executemany(INSERT_REVIEW, data.reviews)
    await conn.executemany(INSERT_MESSAGE, data.messages)


async def load_pool_inputs(conn: asyncpg.Connection, data: MainDataset) -> None:
    """Временные таблицы с данными из Python, которые читает SQL-часть."""
    await conn.execute(
        "CREATE TEMP TABLE _fixed (id uuid PRIMARY KEY, since timestamptz NOT NULL, tz text NOT NULL, "
        "is_main boolean NOT NULL) ON COMMIT DROP"
    )
    await conn.executemany("INSERT INTO _fixed VALUES ($1, $2, $3, $4)", data.pool_users)

    await conn.execute("CREATE TEMP TABLE _tpl (id int PRIMARY KEY, lines text[] NOT NULL) ON COMMIT DROP")
    await conn.executemany("INSERT INTO _tpl VALUES ($1, $2)", list(enumerate(CHAT_TEMPLATES, start=1)))

    columns = list(DICT)
    await conn.execute(
        f"CREATE TEMP TABLE _dict ({', '.join(f'{c} text[] NOT NULL' for c in columns)}) ON COMMIT DROP"
    )
    placeholders = ", ".join(f"${i}" for i in range(1, len(columns) + 1))
    await conn.execute(f"INSERT INTO _dict VALUES ({placeholders})", *DICT.values())


def db_dsn() -> str:
    return get_db_settings().url.replace("+asyncpg", "")


async def run_fill() -> None:
    try:
        validate_users()
        print("[+] Хеширование паролей . . .")
        hashes = await hash_users()
        sql = render_script()
        data = build_main_dataset(hashes)
        achievements = achievements_rows()
    except (ValueError, RuntimeError) as e:
        raise SystemExit(f"[-] Ошибка в настройках скрипта: {e}")

    await upload_default_avatars()
    print("[+] Подключение к бд . . .")
    conn = await asyncpg.connect(db_dsn())

    try:
        print("[+] Выполнение (до 60 секунд) . . .")
        started = time.perf_counter()
        async with conn.transaction():
            await ensure_clean_start(conn)
            await conn.executemany(INSERT_ACHIEVEMENT, achievements)
            await insert_main_dataset(conn, data)
            await load_pool_inputs(conn, data)
            await conn.execute(sql)
            created_ids = [str(r["id"]) for r in await conn.fetch("SELECT id FROM _u")]
        print(f"[!] Время выполнения {time.perf_counter() - started:.1f} с.")

        MANIFEST_PATH.write_text(json.dumps(created_ids))
        await conn.execute(f"ANALYZE {TABLES}")
        print("\n[!] Записи в БД:")
        for row in await conn.fetch(SUMMARY_SQL):
            print(f"  {row['tbl']:<20}{int(row['rows']):>10,}")
        print("\n[!] Основные аккаунты (пароли в USERS):")
        for user in USERS.values():
            print(f"  {user['username']:<20}{user['email']}")
    except Exception as e:
        print(f"[-] Ошибка при выполнении: {e}")
        raise SystemExit(1)
    finally:
        await conn.close()
        print("[!] Соединение закрыто")


async def run_wipe() -> None:
    """Удаляет пользователей, созданных предыдущим запуском. Остальное уходит каскадом (ON DELETE CASCADE):
    привычки, отметки, ревью, друзья, переписки, ачивки, токены. Справочник achievements не трогается."""
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"[-] Нет файла {MANIFEST_PATH.name}: неизвестно, кого удалять")
    user_ids = [uuid.UUID(x) for x in json.loads(MANIFEST_PATH.read_text())]

    conn = await asyncpg.connect(db_dsn())
    try:
        print(f"[+] Удаление пользователей: {len(user_ids):,} . . .")
        started = time.perf_counter()
        async with conn.transaction():
            status = await conn.execute("DELETE FROM users WHERE id = ANY($1::uuid[])", user_ids)
        print(f"[!] Готово ({status}), {time.perf_counter() - started:.1f} с.")
        MANIFEST_PATH.unlink()
    except Exception as e:
        print(f"[-] Ошибка при удалении: {e}")
        raise SystemExit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Наполнение БД синтетическими данными")
    parser.add_argument("--wipe", action="store_true", help="удалить данные, созданные предыдущим запуском")
    args = parser.parse_args()
    asyncio.run(run_wipe() if args.wipe else run_fill())