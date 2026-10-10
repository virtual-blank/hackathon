import asyncio
import re
import time
import uuid

import asyncpg
from core.config import get_db_settings

# =====================================================================
#  СОЗДАТЬ В ДОКЕ 3 АККА ДОБАВИТЬ СЮДА: username и id (потом объясню зачем)
# =====================================================================
USERNAME_1 = "misterkredo"
UUID_1 = "01a1277a-2f83-7431-938c-9b760d66a8c7"
USERNAME_2 = "anasyasis"
UUID_2 = "01a1277a-4a21-7f60-963f-3fe3a5942769"
USERNAME_3 = "gufzdoh"
UUID_3 = "01a1277a-61c3-7d05-ac8c-0ce1f5483dfe"

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
--    * N синтетических юзеров (email вида xxx@seed.test)
--    * дружба / заявки / блокировки (без нарушения инвариантов из доки к UserRelation)
--    * переписка между друзьями (id сообщений = UUIDv7 от created_at, курсорная пагинация работает)
--    * привычки, совместные привычки, отметки (со стриками), достижения, ревью
--  Три твоих аккаунта (USERNAME_n / UUID_n в seed.py) получают "жирные" данные:
--  сотни друзей, входящие и исходящие заявки, блокировки, непрочитанные
--  сообщения, ~12 привычек с историей, приглашения на совместные привычки.
--  Ничего существующего не удаляется и не меняется.
--
--  Допущения (я не видел Uuid7PkMixin и TimeStampMixin):
--    * TimeStampMixin даёт колонки created_at и updated_at (timestamptz), они заполняются явно
--    * enum'ы хранятся строками в нижнем регистре (значения задаются в seed.py: ST_*, INV_*)
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
  is_hub boolean NOT NULL       -- true = один из твоих трёх реальных аккаунтов
) ON COMMIT DROP;
 
WITH g AS (
  SELECT i,
         now() - random() * interval '365 days' AS ts,
         left(d.names[1 + floor(random() * cardinality(d.names))::int], 6)
           || '_' || substr(md5(random()::text || i::text), 1, 8) AS username,
         d.themes[1 + floor(random() * cardinality(d.themes))::int] AS theme,
         d.tzs[1 + floor(random() * cardinality(d.tzs))::int] AS tz,
         random() AS r_tg,
         random() AS r_link
  FROM generate_series(1, {{N_USERS}}) AS i CROSS JOIN _dict d
), ins AS (
  INSERT INTO users (id, created_at, updated_at, username, email, password_hash, theme, timezone,
                     telegram_chat_id, telegram_link_token_hash, telegram_link_expires_at)
  SELECT pg_temp.uuid7_at(ts), ts, ts, username, username || '@seed.test',
         '$2b$12$' || substr(md5(random()::text) || md5(random()::text), 1, 53),
         theme, tz,
         CASE WHEN r_tg < 0.3 THEN 100000000 + floor(random() * 9000000000)::bigint END,
         CASE WHEN r_tg >= 0.3 AND r_link < 0.1 THEN md5(random()::text) || md5(random()::text) END,
         CASE WHEN r_tg >= 0.3 AND r_link < 0.1 THEN now() + random() * interval '1 hour' END
  FROM g
  ON CONFLICT DO NOTHING
  RETURNING id, created_at, timezone
)
INSERT INTO _u (id, since, tz, is_hub)
SELECT id, created_at, timezone, false FROM ins;
 
-- твои три аккаунта (должны уже существовать в users)
INSERT INTO _u (id, since, tz, is_hub)
SELECT id, now() - make_interval(days => {{HISTORY_DAYS}}), coalesce(timezone, 'UTC'), true
FROM users
WHERE id IN ({{HUB_IDS}});   -- UUID_1..UUID_3 из seed.py
 
CREATE UNIQUE INDEX ON _u (id);
 
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
 
-- друзья в обе стороны (для переписки, совместных привычек, ревью)
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
 
-- суффикс [seed] нужен только чтобы можно было откатить привычки твоих трёх аккаунтов (см. ОЧИСТКА)
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
 
-- ---------- ДОСТИЖЕНИЯ (согласованы с реальными стриками: макс. серия по любой привычке) ----------
INSERT INTO user_achievements (id, created_at, updated_at, user_id, achievement_name)
SELECT pg_temp.uuid7_at(a.ts), a.ts, a.ts, a.user_id, 'streak_' || a.t
FROM (
  SELECT g.user_id, g.t,
         least(now(), (g.dt::timestamp + random() * interval '20 hours')::timestamptz) AS ts
  FROM (
    SELECT r.user_id, t.t, min(r.d0 + (t.t - 1)) AS dt
    FROM (
      SELECT x.user_id, x.habit_id, min(x.completed_date) AS d0, count(*) AS len
      FROM (
        SELECT l.user_id, l.habit_id, l.completed_date,
               l.completed_date - (row_number() OVER (PARTITION BY l.habit_id, l.user_id
                                                      ORDER BY l.completed_date))::int AS grp
        FROM habit_logs l
        JOIN _h h ON h.hid = l.habit_id
      ) x
      GROUP BY x.user_id, x.habit_id, x.grp
    ) r
    JOIN unnest(ARRAY[1, 7, 30]) AS t(t) ON r.len >= t.t
    GROUP BY r.user_id, t.t
  ) g
) a
ON CONFLICT (user_id, achievement_name) DO NOTHING;
 
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
--  привычками, отметками, достижениями и ревью. Привычки твоих трёх аккаунтов
--  помечены суффиксом [seed] и удаляются вторым запросом.
--  Достижения этих трёх аккаунтов не отличить от настоящих; третий запрос
--  снесёт ВСЕ их достижения (если у них были настоящие, не выполняй его).
--
--  Каскадное удаление привычек ищет их ревью по reviews.habit_id, а отдельного индекса по этой колонке нет
--  (unique начинается с reviewer_id): на ~13 тыс. привычек очистка занимает около 8 секунд, с индексом ниже около 1.
--  Индекс полезен и самому приложению (ревью привычки ищутся по habit_id), так что его можно оставить.
-- =====================================================================
-- CREATE INDEX IF NOT EXISTS ix_reviews_habit_id ON reviews (habit_id);
-- BEGIN;
-- DELETE FROM habits WHERE title LIKE '% [seed]';
-- DELETE FROM users WHERE email LIKE '%@seed.test';
-- DELETE FROM user_achievements WHERE user_id IN ({{HUB_IDS}});
-- COMMIT;
"""

HUBS = [(USERNAME_1, UUID_1), (USERNAME_2, UUID_2), (USERNAME_3, UUID_3)]

TABLES = "users, user_relations, messages, habits, shared_habit_users, habit_logs, user_achievements, reviews"

SUMMARY_SQL = """
SELECT 'users (синтетика)' AS tbl, count(*) AS rows FROM users WHERE email LIKE '%@seed.test'
UNION ALL SELECT 'users (всего)', count(*) FROM users
UNION ALL SELECT 'user_relations', count(*) FROM user_relations
UNION ALL SELECT 'messages', count(*) FROM messages
UNION ALL SELECT 'habits', count(*) FROM habits
UNION ALL SELECT 'shared_habit_users', count(*) FROM shared_habit_users
UNION ALL SELECT 'habit_logs', count(*) FROM habit_logs
UNION ALL SELECT 'user_achievements', count(*) FROM user_achievements
UNION ALL SELECT 'reviews', count(*) FROM reviews
"""


def parse_hub_ids() -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    for i, (name, raw) in enumerate(HUBS, start=1):
        if not name.strip() or not raw.strip():
            raise ValueError(f"[-] USERNAME_{i} и UUID_{i} должны быть заполнены!")
        try:
            ids.append(uuid.UUID(raw.strip()))
        except ValueError:
            raise ValueError(f"[-] UUID_{i} = {raw!r} не UUID") from None
    if len(set(ids)) != len(ids):
        raise ValueError("[-] UUID_1, UUID_2 и UUID_3 должны быть разными!")
    return ids


def render_script(hub_ids: list[uuid.UUID]) -> str:
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
        "HUB_IDS": ", ".join(f"'{u}'" for u in hub_ids),  # uuid.UUID уже прошёл разбор, кавычки не сломать
        **enums,
    }
    sql = script
    for key, val in values.items():
        sql = sql.replace("{{" + key + "}}", str(val))

    left = sorted(set(re.findall(r"\{\{\w+\}\}", sql)))
    if left:
        raise RuntimeError(f"[-] В SQL остались неподставленные токены: {', '.join(left)}")
    return sql


async def check_hubs(conn, hub_ids: list[uuid.UUID]) -> None:
    rows = await conn.fetch("SELECT id, username FROM users WHERE id = ANY($1::uuid[])", hub_ids)
    found = {str(r["id"]): r["username"] for r in rows}

    problems = []
    for i, ((name, _), hub_id) in enumerate(zip(HUBS, hub_ids), start=1):
        actual = found.get(str(hub_id))
        if actual is None:
            problems.append(f"[-]  UUID_{i} = {hub_id}: такого юзера нет в БД")
        elif actual != name.strip():
            problems.append(f"[-]  UUID_{i} = {hub_id}: в БД это {actual!r}, а в USERNAME_{i} указано {name!r}")
    if problems:
        raise RuntimeError(
            "[-] Аккаунты из USERNAME_n / UUID_n не совпадают с БД (после пересоздания БД обнови их):\n"
            + "\n".join(problems)
        )


async def run_seed():
    try:
        hub_ids = parse_hub_ids()
        sql = render_script(hub_ids)
    except (ValueError, RuntimeError) as e:
        raise SystemExit(f"[-] Ошибка в настройках seed.py: {e}")

    dsn_raw = get_db_settings().url
    formatted_dsn = dsn_raw.replace("+asyncpg", "")

    print("[+] Подключение к бд . . .")
    conn = await asyncpg.connect(formatted_dsn)

    try:
        await check_hubs(conn, hub_ids)

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
