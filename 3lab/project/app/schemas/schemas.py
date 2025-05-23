from pydantic import BaseModel


class CorpusCreate(BaseModel):
    corpus_name: str
    text: str


class SearchRequest(BaseModel):
    word: str
    algorithm: str
    corpus_id: int


class UserCreate(BaseModel):
    email: str
    password: str


class UserMe(BaseModel):
    id: int
    email: str


class UserWithToken(UserMe):
    token: str
