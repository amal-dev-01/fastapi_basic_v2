from pydantic import BaseModel
from pydantic import BaseModel, Field, EmailStr, field_validator

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str

    @field_validator("username")
    def no_spaces(cls, v):
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str


class ItemBase(BaseModel):
    title: str
    description: str

class ItemCreate(ItemBase):
    pass

class ItemOut(ItemBase):
    id: int
    owner_id: int

    model_config = {"from_attributes": True}


class FileOut(BaseModel):
    id: int
    filename: str
    original_name: str
    file_type: str
    owner_id: int

    model_config = {"from_attributes": True}
