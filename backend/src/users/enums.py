import enum


class Theme(enum.StrEnum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class TimezoneEnum(enum.StrEnum):
    # Универсальное время
    UTC = "UTC"

    # СНГ и Россия
    EUROPE_MOSCOW = "Europe/Moscow"
    EUROPE_SAMARA = "Europe/Samara"
    EUROPE_KALININGRAD = "Europe/Kaliningrad"
    ASIA_YEKATERINBURG = "Asia/Yekaterinburg"
    ASIA_OMSK = "Asia/Omsk"
    ASIA_NOVOSIBIRSK = "Asia/Novosibirsk"
    ASIA_KRASNOYARSK = "Asia/Krasnoyarsk"
    ASIA_IRKUTSK = "Asia/Irkutsk"
    ASIA_YAKUTSK = "Asia/Yakutsk"
    ASIA_VLADIVOSTOK = "Asia/Vladivostok"
    ASIA_MAGADAN = "Asia/Magadan"
    ASIA_KAMCHATKA = "Asia/Kamchatka"

    # Европа
    EUROPE_LONDON = "Europe/London"
    EUROPE_PARIS = "Europe/Paris"
    EUROPE_BERLIN = "Europe/Berlin"
    EUROPE_ROME = "Europe/Rome"
    EUROPE_AMSTERDAM = "Europe/Amsterdam"
    EUROPE_WARSAW = "Europe/Warsaw"
    EUROPE_KIEV = "Europe/Kiev"
    EUROPE_MINSK = "Europe/Minsk"
    EUROPE_CHISINAU = "Europe/Chisinau"
    EUROPE_ISTANBUL = "Europe/Istanbul"

    # Азия и Ближний Восток
    ASIA_ALMATY = "Asia/Almaty"
    ASIA_TASHKENT = "Asia/Tashkent"
    ASIA_BISHKEK = "Asia/Bishkek"
    ASIA_DUSHANBE = "Asia/Dushanbe"
    ASIA_EREVAN = "Asia/Yerevan"
    ASIA_BAKU = "Asia/Baku"
    ASIA_TBILISI = "Asia/Tbilisi"
    ASIA_DUBAI = "Asia/Dubai"
    ASIA_JERUSALEM = "Asia/Jerusalem"
    ASIA_RIYADH = "Asia/Riyadh"
    ASIA_TOKYO = "Asia/Tokyo"
    ASIA_SHANGHAI = "Asia/Shanghai"
    ASIA_SINGAPORE = "Asia/Singapore"
    ASIA_SEOUL = "Asia/Seoul"
    ASIA_KOLKATA = "Asia/Kolkata"

    # Северная и Южная Америка
    AMERICA_NEW_YORK = "America/New_York"
    AMERICA_CHICAGO = "America/Chicago"
    AMERICA_DENVER = "America/Denver"
    AMERICA_LOS_ANGELES = "America/Los_Angeles"
    AMERICA_ANCHORAGE = "America/Anchorage"
    AMERICA_HONOLULU = "Pacific/Honolulu"
    AMERICA_MEXICO_CITY = "America/Mexico_City"
    AMERICA_SAO_PAULO = "America/Sao_Paulo"
    AMERICA_ARGENTINA = "America/Argentina/Buenos_Aires"

    # Австралия и Океания
    AUSTRALIA_SYDNEY = "Australia/Sydney"
    AUSTRALIA_MELBOURNE = "Australia/Melbourne"
    AUSTRALIA_PERTH = "Australia/Perth"
    PACIFIC_AUCKLAND = "Pacific/Auckland"

    # Африка
    AFRICA_CAIRO = "Africa/Cairo"
    AFRICA_JOHANNESBURG = "Africa/Johannesburg"
    AFRICA_NAIROBI = "Africa/Nairobi"
