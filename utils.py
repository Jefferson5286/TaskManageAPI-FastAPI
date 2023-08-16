from json import load

from starlette.exceptions import HTTPException
from models import *


async def user_not_found_exception(reference: str):
    if not await User.filter(reference=reference).exists():
        raise HTTPException(status_code=404, detail=f'User with <user_reference={reference}> not found!')


async def task_not_found_exception(reference: str, user: str):
    user_reference = await User.get_or_none(reference=user)

    if not user_reference:
        raise HTTPException(status_code=404, detail=f'User with <user_reference={reference}> not found!')

    if not await Task.filter(user=user_reference).all().get_or_none(reference=reference):
        raise HTTPException(status_code=404, detail=f'Task with <task_reference={reference}> not found!')


async def compare_access_token(token: str, reference: str):
    if not await User.filter(reference=reference).exists():
        raise HTTPException(status_code=404, detail=f'User with <user_reference={reference}> not found!')

    user = await User.filter(reference=reference).first()

    if token != user.current_access_token:
        raise HTTPException(status_code=401, detail='The access token is not valid. Unauthorized access!')


def get_test_data(pk: str = None):
    with open('testes/test_data.json', 'r', encoding='utf-8') as file:
        if pk:
            return load(file)[pk]
        return load(file)
