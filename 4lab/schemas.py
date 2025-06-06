from pydantic import BaseModel
from typing import Optional


class CinemaBase(BaseModel):
    name: str     
    address: str   

class CinemaCreate(CinemaBase):
    pass

class Cinema(CinemaBase):
    id: int        
    
    class Config:
        from_attributes = True

class MovieBase(BaseModel):
    name: str     
    genre: str     
    cinema_id: int 

class MovieCreate(MovieBase):
    pass

class MovieUpdate(BaseModel):
    name: Optional[str] = None   
    genre: Optional[str] = None  

class Movie(MovieBase):
    id: int        
    
    class Config:
        from_attributes = True
