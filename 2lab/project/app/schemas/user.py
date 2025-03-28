from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    token: str

    class Config:
        orm_mode = True

class UserInDB(UserBase):
    id: int

    class Config:
        orm_mode = True