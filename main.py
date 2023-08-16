from uuid import uuid4

from utils import *
from schamas import *
from models import *

# noinspection PyUnresolvedReferences
from pydantic import constr
from starlette.responses import JSONResponse,  Response
from starlette.exceptions import HTTPException
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

app = FastAPI()

register_tortoise(
    app=app,
    modules={'models': ['models']},
    db_url='sqlite://database.bin',
    generate_schemas=True,
)


@app.post('/user/register')
async def register_user(data: UserRegisterSchema):
    """
        Rota responsável por registrar um novo usuário. Sendo que <username> não deve
    ser igual a nem outro <username> já registrado.

    :param data: É um <PydanticSchema> que deve ser um JSON contendo as seguintes 'keys':

        {
            "username": <É o nome de usuário, deve ser único. Tipo 'string'>,
            "password": <É a senha do usuário. Tipo 'string'>
        }

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'statusCode' == 200:
                Significa que o usuário foi registrado com sucesso. Será retornado também um JSON, contendo a referência
            do usuário e o token de acesso.

        Para 'statusCode' == 409:
            Significa que já existe um usuário com o mesmo username já registrado.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            com o desenvolvedor para solucionar um problema. Esse status não pode ser retornado.
    """
    hasher = PasswordHasher()

    if await User.filter(username=data.username).exists():
        raise HTTPException(409, 'User with the same username provided, has already been registered!')

    try:
        access_token = str(uuid4())
        reference = str(uuid4())

        await User(
            username=data.username,
            password=hasher.hash(data.password),
            current_access_token=access_token,
            reference=reference
        ).save()

        return JSONResponse({
            'details': 'Successfully registered user!',
            'reference': reference,
            'token': access_token
        })

    except Exception as e:
        raise HTTPException(500, f'Server Error detail: {e}')


@app.post('/user/login')
async def user_login(data: UserRegisterSchema):
    """
        Rota responsável autorizar autenticação com um usuário.

    :param data: É um <PydanticSchema> que deve ser um JSON que deve seguir o seguinte formato:

        {
            "username": <É o nome de usuário, deve ser único. Tipo 'string'>,
            "password": <É a senha do usuário. Tipo 'string'>
        }

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'statusCode' == 200:
            Foi autorizado o acesso. O token de acesso é atualizado no banco de dados. Além disso, o novo token de
            acesso e a referência do usuário são retornadas em um JSON.

        Para 'statusCode' == 401:
            Autorização negada, ou seja, a senha em <password> é inválida.

        Para 'statusCode' == 404:
            Nenhum usuário correspondente a <username> foi encontrado.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            como desenvolvedor para solucionar um problema. Esse 'status' não pode ser retornado.
    """

    if not await User.filter(username=data.username).exists():
        raise HTTPException(404, 'User not found!')

    try:
        hasher = PasswordHasher()
        user = await User.filter(username=data.username).first()

        hasher.verify(user.password, data.password)
        new_access_token = str(uuid4())
        reference = user.reference

        user.current_access_token = new_access_token

        await user.save()

        return JSONResponse({
            'details': 'Authentication performed successfully! A new access token was generated.',
            'token': new_access_token,
            'reference': reference
        })

    except VerifyMismatchError:
        raise HTTPException(401, 'The password is not valid. Unauthorized access!')

    except Exception as e:
        raise HTTPException(500, f'Server Error detail: {e}')


@app.post('/task/create')
async def create_task(data: CreateTaskSchema):
    """
        Criar uma nova tarefa para um usuário.

    :param data: É um <PydanticSchema> que deve ser um JSON que deve seguir o seguinte formato:

        {
            "user_reference": <Referencia do usuário, criador da tarefa. Tipo 'string'>,
            "token": <Token de acesso do usuário referido. Tipo 'string'>,
            "task": <Nome da tarefa, sugerido que seja algo descritivo minimamente. Tipo 'string'.
                Máximo de caracteres 55>,
            "description": <Descrição da tarefa, oferecer mais detalhas da tarefa. Tipo 'string'.
                Máximo de caracteres 255>,
            "status": <Status atual da tarefa, deve passar somente as seguintes strings:
                'progress', 'pending' ou 'completed'. Tipo 'string'>,
        }

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'status code' == 200:
            A tarefa foi registrada com sucesso.

        Para 'statusCode' == 401:
            Autorização negada. Token de acesso é inválido

        Para 'statusCode' == 404:
            Nenhum usuário correspondente a <user_reference> foi encontrado.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.
            Ou o valor de <status> não corresponde aos seguintes termos: 'progress', 'pending' ou 'completed'

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            com o desenvolvedor para solucionar um problema. Esse 'status' não pode ser retornado.
    """

    await user_not_found_exception(data.user_reference)
    await compare_access_token(data.token, data.user_reference)

    reference = str(uuid4())

    try:
        user = await User.get(reference=data.user_reference)

        await Task(
            user=user,
            reference=reference,
            task=data.task,
            description=data.description,
            status=data.status
        ).save()

        return JSONResponse({
            'details': 'Task successfully saved!',
            'reference': reference
        })

    except Exception as e:
        raise HTTPException(500, f'Server Error detail: {e}')


@app.get('/task/list/{user_reference}')
async def list_tasks(user_reference: str):
    """
        Retorna uma lista com todas as tarefas registradas de um usuário.

    :param user_reference: Referência de usuário para buscar as tarefas. A URL deve seguir o padrão:
        /task/list/<referência do usuário>

        exemplo: /task/list/bcee11a4-3686-4833-aac3-488772453f5a

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'statusCode' == 200:
            A lista foi retornada

        Para 'statusCode' == 404:
            Nenhum usuário correspondente a <user_reference> foi encontrado.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            com o desenvolvedor para solucionar um problema. Esse status não pode ser retornado.

    """

    await user_not_found_exception(user_reference)

    try:
        user = await User.get(reference=user_reference)
        tasks = await Task.filter(user=user).all()
        response = list()

        for task in tasks:
            response.append({
                'reference': task.reference,
                'task': task.task,
                'description': task.description,
                'status': task.status
            })

        return JSONResponse(response)

    except Exception as e:
        raise HTTPException(500, f'Server Error detail: {e}')


@app.delete('/task/delete/{user}/{task}')
async def delete_task(user: constr(max_length=36), task: constr(max_length=36)):
    """
        Deleta uma tarefa

    :param user: Referência de usuário para buscar a tarefa.
    :param task: Referência de tarefa à qual será deletada.

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'statuCode' == 200:
            Caso seja deletada

        Para 'statusCode' == 404:
            Nenhum usuário correspondente a <user_reference> foi encontrado.
            Ou a tarefa correspondente não foi encontrada.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            com o desenvolvedor para solucionar um problema. Esse status não pode ser retornado.
    """
    await user_not_found_exception(user)
    await task_not_found_exception(task, user)

    try:
        user = await User.get(reference=user)
        task = await Task.filter(user=user).first()
        name = task.task

        await task.delete()

        return Response(status_code=200, content=f'Task <task={name}> was deleted.')

    except Exception as e:
        raise HTTPException(500, f'Server Error detail: {e}')


@app.put('/task/update')
async def update_task(data: UpdateTaskSchema):
    """
        Atualiza algum campo de uma tarefa

    :param data: É um <PydanticSchema> que deve ser um JSON que deve seguir o seguinte formato:

        {
            "token": <token de usuário. Tipo 'string'>,
            "user_reference": <referência de usuário. Tipo 'string'>
            "task_reference": <referência de tarefa. Tipo 'string'>,
            "target": <qual campo será alterado, sendo eles: description, task ou status. Tipo 'string'>
            "value": <novo valor que target receberá. Tipo 'string'>
        }

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'status code' == 200:
            Atualizado com sucesso

        Para 'statusCode' == 401:
            Autorização negada, ou seja, token inválido.

        Para 'statusCode' == 404:
            Nenhum usuário correspondente a <user_reference> foi encontrado.
            Ou a tarefa correspondente não foi encontrada.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            com o desenvolvedor para solucionar um problema. Esse status não pode ser retornado.
    """

    await user_not_found_exception(data.user_reference)
    await compare_access_token(data.token, data.user_reference)
    await task_not_found_exception(data.task_reference, data.user_reference)

    user = await User.get(reference=data.user_reference)
    task = await Task.filter(user=user).first()

    match data.target:
        case 'task':
            task.task = data.value
        case 'description':
            task.description = data.value
        case 'status':
            task.status = data.value

    await task.save()

    return Response(status_code=200, content=f'Task <task={task.task}> has been updated.')


@app.delete('/task/clear/{user}')
async def clear_all_tasks(user: constr(max_length=36)):
    """
            Limpa todas as tarefas de um usuário.

    :param user: Referencia de usuário.

    :return: Os retornos são correspondentes a consistência dos dados recebidos. Possíveis respostas válidas:
        Para 'status code' == 200:
            Tudo foi limpo para esse usuário

        Para 'statusCode' == 404:
            Nenhum usuário correspondente a <user_reference> foi encontrado.
            Ou a tarefa correspondente não foi encontrada.

        Para 'statusCode' == 422:
            Os dados não passaram na validação Pydentic, deve revisar os requisitos dos dados.

        Para 'statusCode' == 500:
                Um erro interno no servidor foi invocádo, consulte o retorno JSON para mais detalhes e entre em contando
            com o desenvolvedor para solucionar um problema. Esse status não pode ser retornado.

    """
    await user_not_found_exception(user)

    try:
        user = await User.get(reference=user)
        await Task.filter(user=user).all().delete()

        return Response(status_code=200, content=f'All tasks for <user_reference={user}> have been deleted!')

    except Exception as e:
        raise HTTPException(500, f'Server Error detail: {e}')


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='localhost', port=8080, log_level='info', lifespan='on')
