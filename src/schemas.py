from pydantic import BaseModel, field_validator
from typing import Optional

class MovieRaw(BaseModel):
    id: int
    title: str
    original_title: Optional[str] = None
    original_language: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    release_date: Optional[str] = None
    adult: Optional[bool] = None
    backdrop_path: Optional[str] = None
    poster_path: Optional[str] = None
    genre_ids: list[int] = []

    @field_validator("release_date")
    @classmethod
    def fecha_vacia_a_none(cls, v):
        if v == "":
            return None
        return v