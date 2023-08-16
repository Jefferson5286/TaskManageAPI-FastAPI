import pytest
from httpx import AsyncClient
from utils import get_test_data
from tortoise import Tortoise


async def cls_db():
    """
        Isso apaga todos os dados do banco de dados.

        ATENÇÃO:
            Isso é um 'workaround', feito para evitar problemas com conflito de dados. Mas não é uma solução aprovável.
    """
    models = Tortoise.apps.get('models')

    for model_name, models_object in models.items():
        if model_name == 'Aerich':
            continue
        await models_object.all().delete()


# =============================================== Test of /user/register ===============================================

@pytest.mark.anyio
async def test_user_register_success(client: AsyncClient):
    data = get_test_data('user_register')['jeff']

    response = await client.post('/user/register', json=data)
    assert response.status_code == 200


@pytest.mark.anyio
async def test_user_register_duplicate_username_exception(client: AsyncClient):
    data1 = get_test_data('user_register')['jeff']
    data2 = get_test_data('user_register')['kaelly']

    data1['username'] = data2['username']

    resp1 = await client.post('/user/register', json=data1)
    resp2 = await client.post('/user/register', json=data2)

    print(f'\n{resp2.json()}')

    assert resp1.status_code == 200
    assert resp2.status_code == 409


# ================================================ Test of /user/login ================================================

@pytest.mark.anyio
async def test_user_login_success(client: AsyncClient):
    data = get_test_data('user_register')['jeff']
    await client.post('/user/register', json=data)

    response = await client.post('/user/login', json=data)
    assert response.status_code == 200


# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_user_login_without_authorization_exception(client: AsyncClient):
    data = get_test_data('user_register')['jeff']
    await client.post('/user/register', json=data)

    data['password'] = '221009'

    response = await client.post('/user/login', json=data)
    assert response.status_code == 401


@pytest.mark.anyio
async def test_user_login_user_not_found_exception(client: AsyncClient):
    await cls_db()
    data = get_test_data('user_register')['jeff']

    response = await client.post('/user/login', json=data)
    assert response.status_code == 404


# ================================================ Test of /task/create ================================================

# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_create_task_success(client: AsyncClient):
    await cls_db()

    user = get_test_data('user_register')['jeff']
    task = get_test_data('create_task')['task1']

    user_register = await client.post('/user/register', json=user)

    task['user_reference'] = user_register.json()['reference']
    task['token'] = user_register.json()['token']

    response = await client.post('/task/create', json=task)

    assert response.status_code == 200


# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_create_task_status_value_outside_enum(client: AsyncClient):
    await cls_db()

    user = get_test_data('user_register')['jeff']
    task = get_test_data('create_task')['task1']

    user_register = await client.post('/user/register', json=user)

    task['user_reference'] = user_register.json()['reference']
    task['token'] = user_register.json()['token']
    task['status'] = 'pregresso'

    response = await client.post('/task/create', json=task)

    assert response.status_code == 422


# ============================================= Test of /task/list/{user} ==============================================

# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_list_all_tasks_of_one_user_success(client: AsyncClient):
    await cls_db()

    user = get_test_data('user_register')['jeff']

    task1 = get_test_data('create_task')['task1']
    task2 = get_test_data('create_task')['task2']

    user_register = await client.post('/user/register', json=user)

    task1['reference'] = user_register.json()['reference']
    task1['token'] = user_register.json()['token']
    task2['reference'] = user_register.json()['reference']
    task2['token'] = user_register.json()['token']

    await client.post('/task/create', json=task1)
    await client.post('/task/create', json=task2)

    response = await client.get(f'/task/list/{user_register.json()["reference"]}')

    print()
    print(response.json())

    assert response.status_code == 200


# ======================================== Test of /task/delete/{user}/{task} ==========================================

# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_delete_task_success(client: AsyncClient):
    await cls_db()

    user = get_test_data('user_register')['jeff']
    task = get_test_data('create_task')['task1']

    user_register = await client.post('/user/register', json=user)

    task['user_reference'] = user_register.json()['reference']
    task['token'] = user_register.json()['token']

    task_register = await client.post('/task/create', json=task)

    user_reference = user_register.json()['reference']
    task_reference = task_register.json()['reference']

    response = await client.delete(f'/task/delete/{user_reference}/{task_reference}')

    assert response.status_code == 200


# ======================================== Test of /task/delete/{user}/{task} ==========================================

# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_update_a_field_of_task_success(client: AsyncClient):
    await cls_db()

    user = get_test_data('user_register')['jeff']
    task = get_test_data('create_task')['task1']

    user_register = await client.post('/user/register', json=user)

    task['user_reference'] = user_register.json()['reference']
    task['token'] = user_register.json()['token']

    task_register = await client.post('/task/create', json=task)

    user_reference = user_register.json()['reference']
    task_reference = task_register.json()['reference']

    response = await client.put('/task/update', json={
        'user_reference': user_reference,
        'task_reference': task_reference,
        'token': user_register.json()['token'],
        'target': 'task',
        'value': 'Python para burros'
    })

    assert response.status_code == 200


# ======================================== Test of /task/clear/{user} ==========================================

# noinspection DuplicatedCode
@pytest.mark.anyio
async def test_clear_all_tasks_of_a_user(client: AsyncClient):
    await cls_db()

    user = get_test_data('user_register')['jeff']
    task = get_test_data('create_task')['task1']
    task2 = get_test_data('create_task')['task2']

    user_register = await client.post('/user/register', json=user)

    task['user_reference'] = user_register.json()['reference']
    task['token'] = user_register.json()['token']

    task2['user_reference'] = user_register.json()['reference']
    task2['token'] = user_register.json()['token']

    await client.post('/task/create', json=task)
    await client.post('/task/create', json=task2)

    response = await client.delete(f'/task/clear/{user_register.json()["reference"]}')

    assert response.status_code == 200
