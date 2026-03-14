from typing import Annotated

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase

# Type aliases for column lengths
str_20 = Annotated[str, 20]
str_100 = Annotated[str, 100]
str_150 = Annotated[str, 150]
str_200 = Annotated[str, 200]
str_300 = Annotated[str, 300]
str_500 = Annotated[str, 500]
str_1000 = Annotated[str, 1000]
str_4000 = Annotated[str, 4000]


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        str_20: String(20),
        str_100: String(100),
        str_150: String(150),
        str_200: String(200),
        str_300: String(300),
        str_500: String(500),
        str_1000: String(1000),
        str_4000: String(4000),
    }
