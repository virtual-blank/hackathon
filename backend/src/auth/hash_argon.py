import asyncio

from argon2 import PasswordHasher

ph = PasswordHasher()


DUMMY_HASH = ph.hash("DUMMY")


async def create_password(password: str) -> str:
    return await asyncio.to_thread(ph.hash, password)


async def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return await asyncio.to_thread(ph.verify, hash=hashed_password, password=password)
    except Exception:  # todo: ловить ошибки asyncio и argon раздельно
        return False
