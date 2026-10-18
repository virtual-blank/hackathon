import asyncio
import re
import time

import asyncpg

from core.config import get_db_settings, get_minio_settings
from src.auth.hash_argon import create_password

# =====================================================================
#  3 ЮЗЕРА
# =====================================================================
USERS = {
    "USER_1": {"username": "nullnull", "password": "nullnull", "email": "nullnull@gmail.com"},
    "USER_2": {"username": "testtest", "password": "testtest", "email": "testtest@gmail.com"},
    "USER_3": {"username": "sudosudo", "password": "sudosudo", "email": "sudosudo@gmail.com"},
}

tasks = {}


async def hash_users():

    async with asyncio.TaskGroup() as tg:
        for user_id, user_data in USERS.items():
            task = tg.create_task(create_password, user_data.get("password"))
            tasks[user_id] = task
        for user_id, task in tasks.items():
            result = task.result()
            if result:
                USERS[user_id]["password_hash"] = result


# =====================================================================
#  ОБЪЁМ ДАННЫХ / НАСТРОЙКИ
# =====================================================================
N_USERS = 3000  # сколько синтетических юзеров создать
REL_PER_USER = 15  # среднее число заявок/связей, которые инициирует каждый юзер
MAX_HABITS = 8  # макс. число привычек на юзера (среднее около половины)
HISTORY_DAYS = 180  # глубина истории в днях
DIALOG_SHARE = 0.3  # доля дружб, у которых есть переписка
MSGS_PER_DIALOG = 30  # макс. сообщений в одном диалоге (среднее около половины)
SHARE_RATE = 0.15  # доля привычек, которые являются совместными
REVIEW_RATE = 0.05  # вероятность, что друг оставил ревью на неприватную привычку друга (у твоих трёх аккаунтов 0.2)
# сколько связей, привычек и сообщений на диалог у ТВОИХ трёх аккаунтов
HUB_RELATIONS = 250
HUB_HABITS = 12
HUB_MSGS = 150

# Аватарки: доля синтетических юзеров с собственным pfp_url (у остальных NULL = дефолтная иконка).
# Ссылки имеют настоящий формат pfp/<user_id>/<32 hex>.<ext>, но САМИХ ФАЙЛОВ в MinIO нет:
# на фронте такие аватарки будут битыми. Для демо поставь 0.
PFP_SHARE = 0.3

# Refresh-токены синтетических юзеров: сколько максимум на юзера (0 = не создавать) и срок жизни.
# REFRESH_TTL_DAYS должен совпадать с REFRESH_TOKEN_EXPIRE_DAYS из проекта.
MAX_REFRESH_TOKENS = 3
REFRESH_TTL_DAYS = 30

# Иконки ачивок лежат в отдельном бакете MinIO.
# True: в achievements.icon_url пишется полный URL, False: только имя файла (streak-7.webp).
ACHIEVEMENTS_BUCKET = "achievements"
ACH_ICON_FULL_URL = True

# =====================================================================
#  ЗНАЧЕНИЯ ENUM В БД
# =====================================================================
ST_PENDING = "pending"
ST_ACCEPTED = "accepted"
ST_BLOCKED = "blocked"
INV_PENDING = "pending"
INV_ACCEPTED = "accepted"

# =====================================================================
# AI ЗАПРОСИК
# =====================================================================
script = r"""
-- =====================================================================
--  Синтетические данные для теста ручек. Выполняется из seed.py через asyncpg.
--  Токены в двойных фигурных скобках Python подставляет до отправки в БД (см. render_script).
--  Транзакцию открывает и закрывает Python (conn.transaction()), поэтому BEGIN/COMMIT тут нет:
--  если что-то упадёт, в БД не останется ничего.
--
--  Что создаётся:
--    * три твоих аккаунта из USERS в seed.py (username, email, argon2-хеш пароля), если их ещё нет в БД
--    * N синтетических юзеров (email вида xxx@seed.test), у части есть pfp_url, у остальных NULL
--    * refresh-токены синтетических юзеров (часть истекла, часть отозвана)
--    * дружба / заявки / блокировки (без нарушения инвариантов из доки к UserRelation)
--    * переписка между друзьями (id сообщений = UUIDv7 от created_at, курсорная пагинация работает)
--    * привычки (с current_streak_days / max_streak_days), совместные привычки, отметки, ревью
--    * справочник ачивок (STREAK / FRIENDS_COUNT / TOTAL_HABITS) и выданные по реальным данным user_achievements
--  Три твоих аккаунта получают "жирные" данные:
--  сотни друзей, входящие и исходящие заявки, блокировки, непрочитанные
--  сообщения, ~12 привычек с историей, приглашения на совместные привычки.
--  Если аккаунт с таким username и email уже есть, он остаётся как есть (пароль не перезаписывается),
--  а данные ему всё равно добавляются. Ничего существующего не удаляется и не меняется.
--
--  Допущения (я не видел Uuid7PkMixin и TimeStampMixin):
--    * TimeStampMixin даёт колонки created_at и updated_at (timestamptz), они заполняются явно
--    * enum'ы хранятся строками в нижнем регистре (значения задаются в seed.py: ST_*, INV_*)
--    * achievements.rule_type хранится как есть: 'STREAK' / 'FRIENDS_COUNT' / 'TOTAL_HABITS'
-- =====================================================================
 
-- Postgres 14+ кэширует результат LATERAL-вызова по ключу параметров (Memoize) и не замечает random() внутри:
-- у всех юзеров получалось бы одинаковое число привычек/связей и одинаковые "случайные" отметки.
-- На время транзакции выключаем. На старых версиях параметра нет, ошибка гасится.
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
 
-- ---------- словари ----------
CREATE TEMP TABLE _dict ON COMMIT DROP AS SELECT
  ARRAY['ivan','olga','dmitry','maria','sergey','elena','alex','anna','pavel','nina','oleg','irina','maxim','katya','denis','vera','artem','sasha','roman','julia','kirill','tanya','egor','lena','stas','alina','timur','zoya','gleb','mila'] AS names,
  ARRAY['UTC','Europe/Moscow','Europe/Berlin','Europe/Zurich','Europe/London','Asia/Yekaterinburg','Asia/Novosibirsk','Asia/Tokyo','America/New_York'] AS tzs,
  ARRAY['system','light','dark'] AS themes,
  ARRAY['private','friends','friends','public'] AS visibilities,
  ARRAY['#4F46E5','#EF4444','#10B981','#F59E0B','#3B82F6','#EC4899','#8B5CF6','#14B8A6'] AS colors,
  ARRAY['Зарядка','Пить 2 литра воды','Читать 20 минут','Медитация','Прогулка 10 000 шагов','Бег по утрам','Учить английский','Без сахара','Лечь спать до 23:00','Холодный душ','Дневник','Растяжка','Йога','Выучить 5 слов','Не сидеть в телефоне','Приседания','Планка','Витамины','Готовить дома','Писать код час'] AS habits,
  ARRAY['Привет! Как дела?','Ты сегодня уже отметил привычку?','Молодец, так держать!','Давай завтра вместе?','Не забывай про стрик','Сегодня не успел, завтра наверстаю','Ого, у тебя уже неделя подряд!','Присоединяйся к моей привычке','Отличная идея','Окей, договорились','Я только что сделал зарядку','Напомни мне вечером','Ха-ха, ну ты даёшь','Спасибо за поддержку!','Как успехи?','Погнали бегать в выходные','У меня сегодня сложный день','Не сдавайся!','Супер, поздравляю','Давай сверим стрики','Я пас на сегодня','Ты как всегда в форме','Завтра в 7 утра?','Скинь, что там по книге'] AS msgs,
  ARRAY['Так держать!','Красавчик!','Ну наконец-то','Горжусь тобой','Огонь','Респект','Отлично справляешься','Продолжай в том же духе'] AS push_comments,
  ARRAY['Опять халтура','Серьёзно?','Не верю','Давай лучше','Слабо','Стыдно','Это всё?'] AS shame_comments;
 
-- ---------- ПОЛЬЗОВАТЕЛИ ----------
-- _u: общий пул (синтетика + твои 3 аккаунта). rn: сквозной номер для быстрых случайных выборок.
CREATE TEMP TABLE _u (
  rn int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id uuid NOT NULL,
  since timestamptz NOT NULL,   -- с какого момента аккаунт "существует" для генерации дат
  tz text NOT NULL,
  is_hub boolean NOT NULL       -- true = один из твоих трёх аккаунтов (USERS в seed.py)
) ON COMMIT DROP;
 
-- g2 нужен, чтобы id юзера был известен до вставки: он входит в путь аватарки pfp/<user_id>/<hex>.<ext>
-- (тот же формат, что выдаёт MinioService и проверяет FILE_KEY_RE).
WITH g AS (
  SELECT i,
         now() - random() * interval '365 days' AS ts,
         left(d.names[1 + floor(random() * cardinality(d.names))::int], 6)
           || '_' || substr(md5(random()::text || i::text), 1, 8) AS username,
         d.themes[1 + floor(random() * cardinality(d.themes))::int] AS theme,
         d.tzs[1 + floor(random() * cardinality(d.tzs))::int] AS tz,
         random() AS r_tg,
         random() AS r_link,
         random() AS r_pfp,
         md5(random()::text || i::text) AS pfp_name,
         (ARRAY['webp','webp','png','jpeg'])[1 + floor(random() * 4)::int] AS pfp_ext
  FROM generate_series(1, {{N_USERS}}) AS i CROSS JOIN _dict d
), g2 AS (
  SELECT g.*, pg_temp.uuid7_at(g.ts) AS uid FROM g
), ins AS (
  INSERT INTO users (id, created_at, updated_at, username, email, password_hash, pfp_url, theme, timezone,
                     telegram_chat_id, telegram_link_token_hash, telegram_link_expires_at)
  SELECT uid, ts, ts, username, username || '@seed.test',
         '$2b$12$' || substr(md5(random()::text) || md5(random()::text), 1, 53),
         CASE WHEN r_pfp < {{PFP_SHARE}}
              THEN '{{PFP_PREFIX}}pfp/' || uid::text || '/' || pfp_name || '.' || pfp_ext END,
         theme, tz,
         CASE WHEN r_tg < 0.3 THEN 100000000 + floor(random() * 9000000000)::bigint END,
         CASE WHEN r_tg >= 0.3 AND r_link < 0.1 THEN md5(random()::text) || md5(random()::text) END,
         CASE WHEN r_tg >= 0.3 AND r_link < 0.1 THEN now() + random() * interval '1 hour' END
  FROM g2
  ON CONFLICT DO NOTHING
  RETURNING id, created_at, timezone
)
INSERT INTO _u (id, since, tz, is_hub)
SELECT id, created_at, timezone, false FROM ins;
 
-- ---------- ТВОИ ТРИ АККАУНТА ----------
-- Данные приходят из USERS в seed.py: username, email и УЖЕ готовый argon2-хеш пароля (хеширует Python).
-- Аккаунт создаётся с тем же набором колонок, что у обычной регистрации; created_at отодвинут на
-- HISTORY_DAYS назад, чтобы привычки и дружбы ниже не оказались старше самого аккаунта.
-- Если username или email уже заняты, вставка молча пропускается (ON CONFLICT DO NOTHING), а ниже
-- аккаунт находится по паре username + email. Если занят только один из двух, скрипт падает с понятной ошибкой.
CREATE TEMP TABLE _hubs ON COMMIT DROP AS
SELECT * FROM (VALUES
  ('{{USER_1_USERNAME}}', '{{USER_1_EMAIL}}', '{{USER_1_PASSWORD_HASH}}'),
  ('{{USER_2_USERNAME}}', '{{USER_2_EMAIL}}', '{{USER_2_PASSWORD_HASH}}'),
  ('{{USER_3_USERNAME}}', '{{USER_3_EMAIL}}', '{{USER_3_PASSWORD_HASH}}')
) AS v(username, email, password_hash);
 
INSERT INTO users (id, created_at, updated_at, username, email, password_hash, theme, timezone)
SELECT pg_temp.uuid7_at(s.ts), s.ts, s.ts, h.username, h.email, h.password_hash, 'system', 'UTC'
FROM _hubs h
CROSS JOIN (SELECT now() - make_interval(days => {{HISTORY_DAYS}}) AS ts) s
ON CONFLICT DO NOTHING;
 
INSERT INTO _u (id, since, tz, is_hub)
SELECT u.id, now() - make_interval(days => {{HISTORY_DAYS}}), coalesce(u.timezone, 'UTC'), true
FROM users u
JOIN _hubs h ON h.username = u.username AND h.email = u.email;
 
DO $$
BEGIN
  IF (SELECT count(*) FROM _u WHERE is_hub) <> (SELECT count(*) FROM _hubs) THEN
    RAISE EXCEPTION 'Не удалось создать или найти все три аккаунта из USERS: username или email уже занят другим аккаунтом';
  END IF;
END $$;
 
CREATE UNIQUE INDEX ON _u (id);
 
-- ---------- REFRESH-ТОКЕНЫ ----------
-- Только у синтетических юзеров (у твоих трёх аккаунтов токены появятся при настоящем логине).
-- Хеши случайные: залогиниться такими токенами нельзя, они нужны для объёма и проверки очистки истёкших.
-- Часть токенов истекла по сроку, ~30% отозваны (logout). MAX_REFRESH_TOKENS = 0 отключает блок.
INSERT INTO refresh_tokens (id, created_at, updated_at, user_id, token_hash, expires_at, revoked_at)
SELECT pg_temp.uuid7_at(t.ts), t.ts, t.ts, t.user_id,
       md5(random()::text || t.user_id::text) || md5(random()::text),
       t.ts + make_interval(days => {{REFRESH_TTL_DAYS}}),
       CASE WHEN t.r_rev < 0.3 THEN least(now(), t.ts + random() * interval '10 days') END
-- Число токенов считается во вложенном запросе uu (random() в списке выбора = своё значение на каждого юзера).
-- Если поставить random() прямо в аргумент generate_series, он не зависит от юзера, Postgres вычислит его
-- один раз на весь запрос, и у всех юзеров будет одинаковое число токенов (или ни у кого).
FROM (
  SELECT uu.id AS user_id,
         uu.since + (now() - uu.since) * random() AS ts,
         random() AS r_rev
  FROM (
    SELECT u.id, u.since, floor(random() * ({{MAX_REFRESH_TOKENS}} + 1))::int AS cnt
    FROM _u u
    WHERE NOT u.is_hub
  ) uu
  CROSS JOIN LATERAL generate_series(1, uu.cnt) AS g
) t;
 
-- ---------- ДРУЖБА / ЗАЯВКИ / БЛОКИРОВКИ ----------
-- Для каждой неупорядоченной пары максимум ОДНА строка, поэтому инварианты UserRelation соблюдены
-- (нет дружбы + блокировки одновременно, нет встречных pending, нет self-связей).
CREATE TEMP TABLE _rel ON COMMIT DROP AS
WITH picks AS (
  SELECT a.rn AS a_rn,
         1 + floor(random() * (SELECT count(*) FROM _u))::int AS b_rn
  FROM _u a
  CROSS JOIN LATERAL generate_series(1, CASE WHEN a.is_hub THEN {{HUB_RELATIONS}}
                                            ELSE floor(random() * 2 * {{REL_PER_USER}})::int END) AS g
), pairs AS (
  SELECT DISTINCT least(p.a_rn, p.b_rn) AS lo, greatest(p.a_rn, p.b_rn) AS hi
  FROM picks p
  JOIN _u a ON a.rn = p.a_rn
  JOIN _u b ON b.rn = p.b_rn
  WHERE p.a_rn <> p.b_rn AND NOT (a.is_hub AND b.is_hub)
), rnd AS (
  SELECT lo, hi, random() AS r_dir, random() AS r_st, random() AS r_ts FROM pairs
)
SELECT CASE WHEN r_dir < 0.5 THEN lo ELSE hi END AS u_rn,   -- кто отправил / кто заблокировал
       CASE WHEN r_dir < 0.5 THEN hi ELSE lo END AS t_rn,
       CASE WHEN r_st < 0.75 THEN '{{ST_ACCEPTED}}'
            WHEN r_st < 0.97 THEN '{{ST_PENDING}}'
            ELSE '{{ST_BLOCKED}}' END AS status,
       greatest(ul.since, uh.since) + r_ts * (now() - greatest(ul.since, uh.since)) AS ts
FROM rnd
JOIN _u ul ON ul.rn = rnd.lo
JOIN _u uh ON uh.rn = rnd.hi;
 
INSERT INTO user_relations (id, created_at, updated_at, user_id, target_id, status)
SELECT pg_temp.uuid7_at(r.ts), r.ts, r.ts, a.id, b.id, r.status
FROM _rel r
JOIN _u a ON a.rn = r.u_rn
JOIN _u b ON b.rn = r.t_rn;
 
-- друзья в обе стороны (для переписки, совместных привычек, ревью, ачивок)
CREATE TEMP TABLE _friends ON COMMIT DROP AS
SELECT u_rn AS a_rn, t_rn AS b_rn, ts FROM _rel WHERE status = '{{ST_ACCEPTED}}'
UNION ALL
SELECT t_rn, u_rn, ts FROM _rel WHERE status = '{{ST_ACCEPTED}}';
CREATE INDEX ON _friends (a_rn);
 
-- ---------- СООБЩЕНИЯ (только между друзьями) ----------
CREATE TEMP TABLE _dlg ON COMMIT DROP AS
SELECT r.u_rn, r.t_rn, r.ts AS since,
       1 + floor(random() * CASE WHEN ua.is_hub OR ub.is_hub THEN {{HUB_MSGS}} ELSE {{MSGS_PER_DIALOG}} END)::int AS cnt
FROM _rel r
JOIN _u ua ON ua.rn = r.u_rn
JOIN _u ub ON ub.rn = r.t_rn
WHERE r.status = '{{ST_ACCEPTED}}'
  AND random() < CASE WHEN ua.is_hub OR ub.is_hub THEN 0.8 ELSE {{DIALOG_SHARE}} END;
 
-- ts смещён к "сейчас" (power < 1), чтобы свежих сообщений было больше;
-- всё старше 7 дней прочитано, свежее прочитано примерно на половину
INSERT INTO messages (id, created_at, updated_at, sender_id, receiver_id, content, is_read, read_at)
SELECT pg_temp.uuid7_at(m.ts), m.ts, m.ts,
       CASE WHEN m.flip THEN a.id ELSE b.id END,
       CASE WHEN m.flip THEN b.id ELSE a.id END,
       d.msgs[1 + floor(random() * cardinality(d.msgs))::int]
         || CASE WHEN m.r_two < 0.4
                 THEN ' ' || d.msgs[1 + floor(random() * cardinality(d.msgs))::int]
                 ELSE '' END,
       (m.ts < now() - interval '7 days' OR m.r_rd < 0.5),
       CASE WHEN (m.ts < now() - interval '7 days' OR m.r_rd < 0.5)
            THEN least(now(), m.ts + random() * interval '6 hours') END
FROM (
  SELECT dl.u_rn, dl.t_rn,
         dl.since + (now() - dl.since) * power(random(), 0.5) AS ts,
         random() < 0.5 AS flip,
         random() AS r_two,
         random() AS r_rd
  FROM _dlg dl
  CROSS JOIN LATERAL generate_series(1, dl.cnt) AS g
) m
JOIN _u a ON a.rn = m.u_rn
JOIN _u b ON b.rn = m.t_rn
CROSS JOIN _dict d;
 
-- ---------- ПРИВЫЧКИ ----------
-- _h: заготовка (id привычки известен заранее, нужен для логов).
-- p = вероятность отметки в день: у ~25% привычек 95-100% (длинные стрики), у остальных 20-90%.
CREATE TEMP TABLE _h ON COMMIT DROP AS
WITH raw AS (
  SELECT u.rn AS creator_rn, u.id AS creator_id, u.tz, u.since, u.is_hub,
         (now() AT TIME ZONE u.tz)::date AS today,
         d.habits[1 + floor(random() * cardinality(d.habits))::int] AS base_title,
         d.colors[1 + floor(random() * cardinality(d.colors))::int] AS color,
         d.visibilities[1 + floor(random() * cardinality(d.visibilities))::int] AS visibility,
         random() AS r_start, random() AS r_cr, random() AS r_p, random() AS r_p2, random() AS r_rem,
         floor(random() * 4)::int AS nt
  FROM _u u
  CROSS JOIN _dict d
  CROSS JOIN LATERAL generate_series(1, CASE WHEN u.is_hub THEN {{HUB_HABITS}}
                                            ELSE 1 + floor(random() * {{MAX_HABITS}})::int END) AS g
), calc AS (
  SELECT raw.*,
         raw.today - floor(raw.r_start * greatest(1, least({{HISTORY_DAYS}}, raw.today - raw.since::date)))::int AS start_date
  FROM raw
), calc2 AS (
  SELECT calc.*,
         least(now(), (calc.start_date::timestamp + calc.r_cr * interval '20 hours') AT TIME ZONE calc.tz) AS created_at
  FROM calc
)
SELECT pg_temp.uuid7_at(created_at) AS hid,
       calc2.*,
       CASE WHEN r_p < 0.25 THEN 0.95 + 0.05 * r_p2 ELSE 0.2 + 0.7 * r_p2 END AS p
FROM calc2;
 
-- суффикс [seed] нужен только чтобы можно было откатить привычки аккаунтов, существовавших до запуска (см. ОЧИСТКА)
-- current_streak_days / max_streak_days заполняются ниже, когда будут готовы отметки
INSERT INTO habits (id, created_at, updated_at, creator_id, title, color_hex, visibility, start_date,
                    notification_times, last_reminded_at)
SELECT h.hid, h.created_at, h.created_at, h.creator_id,
       h.base_title || ' [seed]', h.color, h.visibility, h.start_date,
       ARRAY(SELECT make_time(floor(random() * 24)::int, (ARRAY[0,15,30,45])[1 + floor(random() * 4)::int], 0) AS t
             FROM generate_series(1, h.nt) AS g
             ORDER BY 1),
       CASE WHEN h.nt > 0 AND h.r_rem < 0.7 THEN now() - random() * interval '24 hours' END
FROM _h h;
 
-- ---------- СОВМЕСТНЫЕ ПРИВЫЧКИ (один партнёр из друзей создателя) ----------
CREATE TEMP TABLE _sh ON COMMIT DROP AS
SELECT s.*,
       CASE WHEN s.accepted THEN s.inv_ts + s.r_acc * (now() - s.inv_ts) END AS acc_ts
FROM (
  SELECT h.hid, f.b_rn AS partner_rn,
         random() < 0.6 AS accepted,
         random() AS r_acc,
         h.created_at + random() * (now() - h.created_at) AS inv_ts
  FROM _h h
  -- партнёр: случайный друг, но твои три аккаунта выбираются заметно чаще (будет много входящих приглашений)
  CROSS JOIN LATERAL (SELECT fr.b_rn FROM _friends fr
                      JOIN _u pb ON pb.rn = fr.b_rn
                      WHERE fr.a_rn = h.creator_rn
                      ORDER BY random() * CASE WHEN pb.is_hub THEN 0.1 ELSE 1 END LIMIT 1) f
  WHERE random() < CASE WHEN h.is_hub THEN 0.5 ELSE {{SHARE_RATE}} END
) s;
 
INSERT INTO shared_habit_users (id, created_at, updated_at, habit_id, user_id, status, accepted_at)
SELECT pg_temp.uuid7_at(s.inv_ts), s.inv_ts, coalesce(s.acc_ts, s.inv_ts), s.hid, p.id,
       CASE WHEN s.accepted THEN '{{INV_ACCEPTED}}' ELSE '{{INV_PENDING}}' END,
       s.acc_ts
FROM _sh s
JOIN _u p ON p.rn = s.partner_rn;
 
-- ---------- ОТМЕТКИ ----------
-- источники: создатель каждой привычки + принятые партнёры (с даты принятия)
CREATE TEMP TABLE _log_src ON COMMIT DROP AS
SELECT h.hid AS habit_id, h.creator_id AS user_id, h.tz,
       h.start_date AS from_date, h.today AS to_date, h.p
FROM _h h
UNION ALL
SELECT h.hid, pu.id, pu.tz,
       (s.acc_ts AT TIME ZONE pu.tz)::date,
       (now() AT TIME ZONE pu.tz)::date,
       least(0.99, greatest(0.1, h.p + (random() - 0.5) * 0.3))
FROM _sh s
JOIN _h h ON h.hid = s.hid
JOIN _u pu ON pu.rn = s.partner_rn
WHERE s.accepted;
 
-- Случайные числа обязаны жить в LATERAL-подзапросе: условие random() < s.p в WHERE ссылалось бы только
-- на s и Postgres применил бы его один раз на привычку, а не на день.
-- created_at = updated_at = момент отметки (в течение дня completed_date в часовом поясе юзера); id = UUIDv7 от него же
INSERT INTO habit_logs (id, created_at, updated_at, habit_id, user_id, completed_date)
SELECT pg_temp.uuid7_at(x.ts), x.ts, x.ts, x.habit_id, x.user_id, x.dt
FROM (
  SELECT s.habit_id, s.user_id, d.dt,
         least(now(), (d.dt::timestamp + d.r_t * interval '23 hours') AT TIME ZONE s.tz) AS ts
  FROM _log_src s
  CROSS JOIN LATERAL (
    SELECT s.from_date + k AS dt, random() AS r_p, random() AS r_t
    FROM generate_series(0, s.to_date - s.from_date) AS k
  ) d
  WHERE d.r_p < s.p
) x;
 
-- ---------- СЕРИИ (стрики) ----------
-- _runs: все непрерывные серии отметок (по паре привычка + юзер). Классика "gaps and islands":
-- дата минус порядковый номер отметки одинакова внутри одной серии.
CREATE TEMP TABLE _runs ON COMMIT DROP AS
SELECT x.habit_id, x.user_id, count(*) AS len,
       min(x.completed_date) AS first_d, max(x.completed_date) AS last_d
FROM (
  SELECT l.habit_id, l.user_id, l.completed_date,
         l.completed_date - (row_number() OVER (PARTITION BY l.habit_id, l.user_id
                                                ORDER BY l.completed_date))::int AS grp
  FROM habit_logs l
  JOIN _h h ON h.hid = l.habit_id
) x
GROUP BY x.habit_id, x.user_id, x.grp;
 
-- Стрик привычки считается по отметкам создателя.
-- current: серия, которая заканчивается сегодня или вчера (если сегодня ещё не отмечено), иначе 0;
-- max: самая длинная серия за всё время. "Сегодня" берётся в часовом поясе создателя.
UPDATE habits hb
SET current_streak_days = s.cur,
    max_streak_days = s.mx
FROM (
  SELECT r.habit_id,
         max(r.len) AS mx,
         coalesce(max(r.len) FILTER (WHERE r.last_d >= h.today - 1), 0) AS cur
  FROM _runs r
  JOIN _h h ON h.hid = r.habit_id AND h.creator_id = r.user_id
  GROUP BY r.habit_id
) s
WHERE hb.id = s.habit_id;
 
-- ---------- ДОСТИЖЕНИЯ ----------
-- Справочник в проде создаёт администратор. Для теста добавляем набор по трём типам правил;
-- уже существующие ачивки (совпало name) не трогаются.
-- Иконки: имена файлов лежат в frontend/assets/achievements (см. ACH_ICON_FULL_URL в seed.py).
INSERT INTO achievements (id, created_at, updated_at, name, rule_type, rule_value, color_hex,
                          requirement, description, icon_url)
SELECT pg_temp.uuid7_at(now()), now(), now(), v.name, v.rule_type, v.rule_value, v.color_hex,
       v.req, v.descr, '{{ACH_ICON_BASE}}' || v.icon
FROM (VALUES
  ('Первый шаг',          'STREAK',        1,   '#10B981', 'Серия 1 день подряд по любой привычке',   'Первый день в копилке. Начало положено!', 'streak-1.webp'),
  ('Неделя огня',         'STREAK',        7,   '#F59E0B', 'Серия 7 дней подряд по любой привычке',   'Целая неделя без пропусков',              'streak-7.webp'),
  ('Месяц без пропусков', 'STREAK',        30,  '#EF4444', 'Серия 30 дней подряд по любой привычке',  'Тридцать дней подряд. Это уже привычка',  'streak-30.webp'),
  ('Сотня',               'STREAK',        100, '#8B5CF6', 'Серия 100 дней подряд по любой привычке', 'Сто дней подряд. Легенда',                'streak-100.webp'),
  ('Первый друг',         'FRIENDS_COUNT', 1,   '#3B82F6', 'Иметь 1 друга',                           'Вместе веселее',                          'friends-1.webp'),
  ('Душа компании',       'FRIENDS_COUNT', 10,  '#EC4899', 'Иметь 10 друзей',                         'Десять друзей поддерживают тебя',         'friends-10.webp'),
  ('Знаменитость',        'FRIENDS_COUNT', 50,  '#14B8A6', 'Иметь 50 друзей',                         'Тебя знают все',                          'friends-50.webp'),
  ('Три привычки',        'TOTAL_HABITS',  3,   '#4F46E5', 'Создать 3 привычки',                      'Ты набираешь обороты',                    'habits-3.webp'),
  ('Пять привычек',       'TOTAL_HABITS',  5,   '#10B981', 'Создать 5 привычек',                      'Целая коллекция полезных дел',            'habits-5.webp'),
  ('Мастер привычек',     'TOTAL_HABITS',  10,  '#F59E0B', 'Создать 10 привычек',                     'Ты в этом профи',                         'habits-10.webp')
) AS v(name, rule_type, rule_value, color_hex, req, descr, icon)
ON CONFLICT (name) DO NOTHING;
 
-- Выдаём ВСЕ ачивки из таблицы (в том числе заведённые админом) с известным rule_type,
-- условие которых реально выполнено по сгенерированным данным. Время получения = момент,
-- когда пользователь достиг порога:
--   STREAK        : день, когда первая подходящая серия дошла до rule_value (+ случайное время в этот день)
--   FRIENDS_COUNT : момент появления rule_value-го друга
--   TOTAL_HABITS  : момент создания rule_value-й привычки
-- Случайные числа считаются один раз в _ach_ev, а не размазываются по INSERT.
CREATE TEMP TABLE _ach_ev ON COMMIT DROP AS
SELECT r.user_id, a.id AS achievement_id,
       least(now(), (((min(r.first_d) + (a.rule_value - 1))::timestamp
                      + random() * interval '20 hours') AT TIME ZONE u.tz)) AS ts
FROM _runs r
JOIN _u u ON u.id = r.user_id
JOIN achievements a ON a.rule_type = 'STREAK' AND a.rule_value > 0 AND r.len >= a.rule_value
GROUP BY r.user_id, a.id, a.rule_value, u.tz
UNION ALL
SELECT u.id, a.id, f.ts
FROM (SELECT a_rn, ts, row_number() OVER (PARTITION BY a_rn ORDER BY ts) AS n FROM _friends) f
JOIN _u u ON u.rn = f.a_rn
JOIN achievements a ON a.rule_type = 'FRIENDS_COUNT' AND a.rule_value > 0 AND a.rule_value = f.n
UNION ALL
SELECT u.id, a.id, h.created_at
FROM (SELECT creator_rn, created_at, row_number() OVER (PARTITION BY creator_rn ORDER BY created_at) AS n FROM _h) h
JOIN _u u ON u.rn = h.creator_rn
JOIN achievements a ON a.rule_type = 'TOTAL_HABITS' AND a.rule_value > 0 AND a.rule_value = h.n;
 
-- если один из твоих аккаунтов существовал до запуска, у него могут быть настоящие ачивки: дубли молча пропускаются
INSERT INTO user_achievements (id, created_at, updated_at, user_id, achievement_id)
SELECT pg_temp.uuid7_at(e.ts), e.ts, e.ts, e.user_id, e.achievement_id
FROM _ach_ev e
ON CONFLICT (user_id, achievement_id) DO NOTHING;
 
-- ---------- РЕВЬЮ (друг оценивает привычку друга целиком; 1 = пуш, 0 = шейм) ----------
-- Ревью привязано к привычке, а не к отметке: пара (ревьюер, привычка) = максимум одно ревью (uq_reviewer_id_habit_log).
-- Ревьюер: принятый друг создателя. Приватные привычки друзья не видят, их не ревьюим.
-- Перебираются ВСЕ пары (привычка, друг создателя), и каждая получает ревью с вероятностью REVIEW_RATE
-- (0.2, если в паре есть один из твоих трёх аккаунтов: и как автор, и как ревьюер), поэтому дублей быть не может.
-- Время ревью: между моментом, когда привычка создана и люди уже дружат, и "сейчас".
CREATE TEMP TABLE _rv ON COMMIT DROP AS
SELECT h.hid AS habit_id, f.b_rn AS reviewer_rn,
       greatest(h.created_at, f.ts) AS since,
       random() AS r_rate, random() AS r_c, random() AS r_pick, random() AS r_ts
FROM _h h
JOIN _friends f ON f.a_rn = h.creator_rn
JOIN _u rv ON rv.rn = f.b_rn
WHERE h.visibility <> 'private'
  AND random() < CASE WHEN h.is_hub OR rv.is_hub THEN 0.2 ELSE {{REVIEW_RATE}} END;
 
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
 
 
-- =====================================================================
--  ОЧИСТКА: убрать всё, что создал скрипт (выполни руками в psql, здесь это просто комментарий)
--  Юзеры с @seed.test удаляются каскадом вместе со своими связями, сообщениями,
--  привычками, отметками, достижениями, refresh-токенами и ревью.
--
--  Вариант 1 (аккаунты создал сам скрипт): удалить всё одним запросом. Три твоих аккаунта тоже уйдут,
--  а вместе с ними каскадом их привычки, отметки, друзья, переписка, ревью, ачивки и токены.
--  Если уже заходил под ними в приложение и что-то менял руками, это тоже пропадёт.
--
--  Вариант 2 (аккаунты существовали ДО запуска и их надо сохранить): удалить только данные скрипта.
--  Привычки этих аккаунтов помечены суффиксом [seed] и удаляются вторым запросом.
--  Их связи и переписка с синтетикой уходят каскадом вместе с @seed.test юзерами.
--  Ачивки этих аккаунтов не отличить от настоящих; третий запрос снесёт ВСЕ их достижения
--  (если у них были настоящие, не выполняй его).
--
--  Справочник achievements скриптом не чистится: это обычные данные, их мог завести и админ.
--  Если нужно убрать и его: DELETE FROM achievements WHERE name IN ('Первый шаг', ...);
--  (user_achievements удалятся каскадом).
--
--  Каскадное удаление привычек ищет их ревью по reviews.habit_id, а отдельного индекса по этой колонке нет
--  (unique начинается с reviewer_id): на ~13 тыс. привычек очистка занимает около 8 секунд, с индексом ниже около 1.
--  Индекс полезен и самому приложению (ревью привычки ищутся по habit_id), так что его можно оставить.
-- =====================================================================
-- CREATE INDEX IF NOT EXISTS ix_reviews_habit_id ON reviews (habit_id);
--
-- Вариант 1:
-- BEGIN;
-- DELETE FROM users WHERE email LIKE '%@seed.test'
--                      OR username IN ('{{USER_1_USERNAME}}', '{{USER_2_USERNAME}}', '{{USER_3_USERNAME}}');
-- COMMIT;
--
-- Вариант 2:
-- BEGIN;
-- DELETE FROM habits WHERE title LIKE '% [seed]';
-- DELETE FROM users WHERE email LIKE '%@seed.test';
-- DELETE FROM user_achievements WHERE user_id IN (SELECT id FROM users WHERE username IN ('{{USER_1_USERNAME}}', '{{USER_2_USERNAME}}', '{{USER_3_USERNAME}}'));
-- COMMIT;
"""

TABLES = (
    "users, refresh_tokens, user_relations, messages, habits, shared_habit_users, "
    "habit_logs, achievements, user_achievements, reviews"
)

SUMMARY_SQL = """
SELECT 'users (синтетика)' AS tbl, count(*) AS rows FROM users WHERE email LIKE '%@seed.test'
UNION ALL SELECT 'users (всего)', count(*) FROM users
UNION ALL SELECT 'refresh_tokens', count(*) FROM refresh_tokens
UNION ALL SELECT 'user_relations', count(*) FROM user_relations
UNION ALL SELECT 'messages', count(*) FROM messages
UNION ALL SELECT 'habits', count(*) FROM habits
UNION ALL SELECT 'shared_habit_users', count(*) FROM shared_habit_users
UNION ALL SELECT 'habit_logs', count(*) FROM habit_logs
UNION ALL SELECT 'achievements', count(*) FROM achievements
UNION ALL SELECT 'user_achievements', count(*) FROM user_achievements
UNION ALL SELECT 'reviews', count(*) FROM reviews
"""

# в SQL-шаблоне зашиты токены USER_1_*, USER_2_*, USER_3_*, поэтому ключи USERS должны быть именно такими
USER_KEYS = ("USER_1", "USER_2", "USER_3")
USERNAME_MAX_LEN = 16  # users.username = String(16)


def validate_users() -> None:
    if tuple(USERS) != USER_KEYS:
        raise ValueError(f"[-] В USERS должны быть ровно ключи {', '.join(USER_KEYS)}, сейчас: {', '.join(USERS)}")

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


async def hash_users() -> None:
    # argon2 считается в потоках (create_password -> asyncio.to_thread), три пароля хешируются параллельно
    async with asyncio.TaskGroup() as tg:
        tasks = {key: tg.create_task(create_password(user["password"])) for key, user in USERS.items()}
    for key, task in tasks.items():
        USERS[key]["password_hash"] = task.result()


def render_script() -> str:
    enums = {
        "ST_PENDING": ST_PENDING,
        "ST_ACCEPTED": ST_ACCEPTED,
        "ST_BLOCKED": ST_BLOCKED,
        "INV_PENDING": INV_PENDING,
        "INV_ACCEPTED": INV_ACCEPTED,
    }
    for key, val in enums.items():
        if not re.fullmatch(r"\w+", val):  # значения идут в SQL внутри кавычек
            raise ValueError(f"[-] {key} = {val!r}: допустимы только буквы, цифры и _")

    # адреса аватарок и иконок строим из тех же настроек MinIO, что и сервис
    minio = get_minio_settings()
    urls = {
        "PFP_PREFIX": f"{minio.endpoint}/{minio.bucket_name}/",
        "ACH_ICON_BASE": f"{minio.endpoint}/{ACHIEVEMENTS_BUCKET}/" if ACH_ICON_FULL_URL else "",
    }
    for key, val in urls.items():
        if "'" in val or "{{" in val:  # значения идут в SQL внутри кавычек
            raise ValueError(f"[-] {key} = {val!r}: нельзя использовать ' и {{")

    # USER_1 -> {{USER_1_USERNAME}}, {{USER_1_EMAIL}}, {{USER_1_PASSWORD_HASH}} и так далее.
    # Знак $ в argon2-хеше безопасен: значение стоит внутри обычных одинарных кавычек.
    users = {}
    for key, user in USERS.items():
        for field in ("username", "email", "password_hash"):
            val = user[field]
            if "'" in val or "{{" in val:  # значения идут в SQL внутри кавычек
                raise ValueError(f"[-] USERS[{key!r}][{field!r}]: нельзя использовать ' и двойную фигурную скобку")
            users[f"{key}_{field.upper()}"] = val

    values = {
        "N_USERS": N_USERS,
        "REL_PER_USER": REL_PER_USER,
        "MAX_HABITS": MAX_HABITS,
        "HISTORY_DAYS": HISTORY_DAYS,
        "DIALOG_SHARE": DIALOG_SHARE,
        "MSGS_PER_DIALOG": MSGS_PER_DIALOG,
        "SHARE_RATE": SHARE_RATE,
        "REVIEW_RATE": REVIEW_RATE,
        "HUB_RELATIONS": HUB_RELATIONS,
        "HUB_HABITS": HUB_HABITS,
        "HUB_MSGS": HUB_MSGS,
        "PFP_SHARE": PFP_SHARE,
        "MAX_REFRESH_TOKENS": MAX_REFRESH_TOKENS,
        "REFRESH_TTL_DAYS": REFRESH_TTL_DAYS,
        **users,
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


async def run_seed():
    try:
        validate_users()
        print("[+] Хеширование паролей . . .")
        await hash_users()
        sql = render_script()
    except (ValueError, RuntimeError) as e:
        raise SystemExit(f"[-] Ошибка в настройках seed.py: {e}")

    dsn_raw = get_db_settings().url
    formatted_dsn = dsn_raw.replace("+asyncpg", "")

    print("[+] Подключение к бд . . .")
    conn = await asyncpg.connect(formatted_dsn)

    try:
        print("[+] Выполенение (до 60 секунд) . . .")
        started = time.perf_counter()
        async with conn.transaction():
            await conn.execute(sql)
        print(f"[!] Время выполнения {time.perf_counter() - started:.1f} с.")

        await conn.execute(f"ANALYZE {TABLES}")
        print("\n[!] Записи в БД:")
        for row in await conn.fetch(SUMMARY_SQL):
            print(f"  {row['tbl']:<20}{int(row['rows']):>10,}")
    except Exception as e:
        print(f"[-] Ошибка при выполнении: {e}")
        raise SystemExit(1)
    finally:
        await conn.close()
        print("[!] Соединение закрыто")


if __name__ == "__main__":
    asyncio.run(run_seed())
