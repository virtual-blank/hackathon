from src.achievements.models import RuleTypeEnum

# todo: придумать нормальные названия
# todo: наполнение бд при первом запуске контейнера
# todo: создание бакета для иконок ачивок
# todo: добавление ачивок в схему ответа для Users


achievements_data = [
    # Стрики
    {
        "name": "Глитч",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 3,
        "color_hex": "#FBBF24",
        "icon_url": "",
        "description": "В твоей системе явный сбой и ей это не нравится. Продолжай",
        "requirement": "Отметить выполнение привычки 3 дня подряд.",
    },
    {
        "name": "В ударе",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 7,
        "color_hex": "#F97316",
        "icon_url": "",
        "description": "Неделя без отмазок, а больше можешь?",
        "requirement": "Отметить выполнение привычки 7 дней подряд.",
    },
    {
        "name": "Зависимость",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 21,
        "color_hex": "#EF4444",
        "icon_url": "",
        "description": "Привычка уже приросла к тебе, не останавливайся",
        "requirement": "Отметить выполнение привычки 21 день подряд.",
    },
    {
        "name": "Познание",
        "rule_type": RuleTypeEnum.STREAK,
        "rule_value": 30,
        "color_hex": "#8B5CF6",
        "icon_url": "",
        "description": "Твой мозг стал инструментом, а не просто органом",
        "requirement": "Отметить выполнение привычки 30 дней подряд.",
    },
    # Привычки
    {
        "name": "Первый шаг",
        "rule_type": RuleTypeEnum.TOTAL_HABITS,
        "rule_value": 1,
        "color_hex": "#34D399",
        "icon_url": "",
        "description": "Первая цель поставлена. Теперь самое сложное — не забить на неё на второй день.",
        "requirement": "Создать 1 новую привычку.",
    },
    {
        "name": "Архитектор",
        "rule_type": RuleTypeEnum.TOTAL_HABITS,
        "rule_value": 3,
        "color_hex": "#10B981",
        "icon_url": "",
        "description": "Три привычки одновременно. Твой энтузиазм похвален, посмотрим, как дела с тайм-менеджментом.",
        "requirement": "Создать суммарно 3 привычки.",
    },
    {
        "name": "Гуру продуктивности",
        "rule_type": RuleTypeEnum.TOTAL_HABITS,
        "rule_value": 10,
        "color_hex": "#059669",
        "icon_url": "",
        "description": "Десять активных трекеров. Ты вообще спишь или питаешься исключительно кофе и амбициями?",
        "requirement": "Создать суммарно 10 привычек.",
    },
    # Друзья
    {
        "name": "Первый контакт",
        "rule_type": RuleTypeEnum.FRIENDS_COUNT,
        "rule_value": 1,
        "color_hex": "#60A5FA",
        "icon_url": "",
        "description": "Теперь за твоими успехами следит как минимум один живой человек. Никакого давления.",
        "requirement": "Добавить 1 пользователя в список друзей.",
    },
    {
        "name": "Пати",
        "rule_type": RuleTypeEnum.FRIENDS_COUNT,
        "rule_value": 5,
        "color_hex": "#3B82F6",
        "icon_url": "",
        "description": "Свидетелей твоего роста стало больше. Сливаться теперь официально стыдно.",
        "requirement": "Добавить 5 пользователей в список друзей.",
    },
    {
        "name": "Лидер мнений",
        "rule_type": RuleTypeEnum.FRIENDS_COUNT,
        "rule_value": 15,
        "color_hex": "#EC4899",
        "icon_url": "",
        "description": "У тебя своя мини-секта. Главное — продолжать делать вид, что ты точно знаешь, куда идешь.",
        "requirement": "Добавить 15 пользователей в список друзей.",
    },
]
