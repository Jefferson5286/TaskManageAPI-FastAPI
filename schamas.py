from pydantic import BaseModel, constr, field_validator


def status_enum_validator(value: str):
    if not any(value == i for i in ('progress', 'pending', 'completed')):
        raise ValueError("Accept only: 'progress', 'pending' or 'completed'.")


class CreateTaskSchema(BaseModel):
    user_reference: constr(max_length=36)
    task: constr(max_length=55)
    description: constr(max_length=255)
    status: str
    token: constr(max_length=36)

    @field_validator('status')
    def status_validator(cls, value: str) -> str:
        status_enum_validator(value)
        return value


class UpdateTaskSchema(BaseModel):
    user_reference: constr(max_length=36)
    task_reference: constr(max_length=36)
    token: constr(max_length=36)
    target: str
    value: str


class UserRegisterSchema(BaseModel):
    username: constr(max_length=25)
    password: str


class AccessTokenSchema(BaseModel):
    token: constr(max_length=36)
