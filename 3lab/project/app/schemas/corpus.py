from pydantic import BaseModel
from typing import List

class CorpusCreate(BaseModel):
    corpus_name: str
    text: str

class CorpusOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CorpusListOut(BaseModel):
    corpuses: List[CorpusOut]

class SearchRequest(BaseModel):
    word: str
    algorithm: str
    corpus_id: int

class SearchResult(BaseModel):
    word: str
    distance: int

class SearchResponse(BaseModel):
    execution_time: float
    results: List[SearchResult]