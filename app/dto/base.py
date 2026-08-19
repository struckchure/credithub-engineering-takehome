from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class BaseDto(BaseModel):
    """``from_attributes`` is what lets FastAPI serialize an ORM object against
    a ``response_model`` — properties included, not just mapped columns.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)
