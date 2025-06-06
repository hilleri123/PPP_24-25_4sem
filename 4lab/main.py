from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db, CinemaDB, MovieDB
from schemas import Cinema, CinemaCreate, Movie, MovieCreate, MovieUpdate


app = FastAPI(
    title="Cinema API",
    description="API для управления кинотеатрами и фильмами",
    version="1.0.0"
)


@app.get("/cinemas", 
         response_model=List[Cinema],
         summary="Получить все кинотеатры",
         description="Возвращает список всех кинотеатров")
def read_cinemas(db: Session = Depends(get_db)) -> List[CinemaDB]:
    """
    Получение списка всех кинотеатров
    
    Args:
        db: Сессия базы данных
        
    Returns:
        List[CinemaDB]: Список всех кинотеатров
    """
    return db.query(CinemaDB).all()

@app.post("/cinemas", 
          response_model=Cinema, 
          status_code=status.HTTP_201_CREATED,
          summary="Создать новый кинотеатр",
          description="Добавляет новый кинотеатр в систему")
def create_cinema(
    cinema: CinemaCreate, 
    db: Session = Depends(get_db)
) -> CinemaDB:
    """
    Создание нового кинотеатра
    
    Args:
        cinema: Данные для создания кинотеатра
        db: Сессия базы данных
        
    Returns:
        CinemaDB: Созданный кинотеатр с присвоенным ID
    """
    db_cinema = CinemaDB(name=cinema.name, address=cinema.address)
    
    db.add(db_cinema)
    db.commit()
    db.refresh(db_cinema)
    
    return db_cinema

@app.get("/cinemas/{cinema_id}/movies", 
         response_model=List[Movie],
         summary="Получить фильмы кинотеатра",
         description="Возвращает список фильмов для указанного кинотеатра")
def read_cinema_movies(
    cinema_id: int, 
    db: Session = Depends(get_db)
) -> List[MovieDB]:
    """
    Получение фильмов конкретного кинотеатра
    
    Args:
        cinema_id: Идентификатор кинотеатра
        db: Сессия базы данных
        
    Returns:
        List[MovieDB]: Список фильмов кинотеатра
        
    Raises:
        HTTPException 404: Если кинотеатр не найден
    """
    cinema = db.get(CinemaDB, cinema_id)
    
    if not cinema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кинотеатр не найден"
        )
        
    return cinema.movies

@app.delete("/cinemas/{cinema_id}", 
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Удалить кинотеатр",
            description="Удаляет кинотеатр и все его фильмы (каскадное удаление)")
def delete_cinema(
    cinema_id: int, 
    db: Session = Depends(get_db)
) -> None:
    """
    Удаление кинотеатра
    
    Args:
        cinema_id: Идентификатор кинотеатра
        db: Сессия базы данных
        
    Raises:
        HTTPException 404: Если кинотеатр не найден
    """
    db_cinema = db.get(CinemaDB, cinema_id)
    
    if not db_cinema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кинотеатр не найден"
        )
    
  
    db.delete(db_cinema)
    db.commit()



@app.get("/movies", 
         response_model=List[Movie],
         summary="Получить все фильмы",
         description="Возвращает список фильмов с возможностью фильтрации по кинотеатру")
def read_movies(
    cinema_id: Optional[int] = Query(None, description="Фильтр по ID кинотеатра"),
    db: Session = Depends(get_db)
) -> List[MovieDB]:
    """
    Получение списка фильмов
    
    Args:
        cinema_id: Опциональный фильтр по кинотеатру
        db: Сессия базы данных
        
    Returns:
        List[MovieDB]: Список фильмов (отфильтрованный при наличии cinema_id)
    """
    query = db.query(MovieDB)
    
    # Применение фильтра по кинотеатру, если указан
    if cinema_id:
        query = query.filter(MovieDB.cinema_id == cinema_id)
    
    return query.all()

@app.post("/movies", 
          response_model=Movie, 
          status_code=status.HTTP_201_CREATED,
          summary="Создать новый фильм",
          description="Добавляет новый фильм в систему")
def create_movie(
    movie: MovieCreate, 
    db: Session = Depends(get_db)
) -> MovieDB:
    """
    Создание нового фильма
    
    Args:
        movie: Данные для создания фильма
        db: Сессия базы данных
        
    Returns:
        MovieDB: Созданный фильм с присвоенным ID
        
    Raises:
        HTTPException 404: Если кинотеатр не найден
    """
    if not db.get(CinemaDB, movie.cinema_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Кинотеатр не найден"
        )
    
    db_movie = MovieDB(**movie.model_dump())
    
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    
    return db_movie

@app.put("/movies/{movie_id}", 
         response_model=Movie,
         summary="Обновить данные фильма",
         description="Обновляет информацию о фильме по его идентификатору")
def update_movie(
    movie_id: int, 
    movie_update: MovieUpdate, 
    db: Session = Depends(get_db)
) -> MovieDB:
    """
    Обновление данных фильма
    
    Args:
        movie_id: Идентификатор фильма
        movie_update: Новые данные для обновления
        db: Сессия базы данных
        
    Returns:
        MovieDB: Обновленный объект фильма
        
    Raises:
        HTTPException 404: Если фильм не найден
    """
    db_movie = db.get(MovieDB, movie_id)
    
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фильм не найден"
        )
    
    if movie_update.name is not None:
        db_movie.name = movie_update.name
        
    if movie_update.genre is not None:
        db_movie.genre = movie_update.genre
    
  
    db.commit()
    db.refresh(db_movie)
    
    return db_movie
