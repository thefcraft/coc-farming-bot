import logging
import easyocr  # pyright: ignore[reportMissingTypeStubs]
from pydantic import BaseModel, BeforeValidator, ValidationError
from typing import Any, Annotated
from .types import ImageCv2

logger = logging.getLogger(__name__)

reader = easyocr.Reader(["en"])


def clean_loot_int(v: Any):
    if isinstance(v, str):
        return v.replace(" ", "")
    return v


type LootInt = Annotated[int, BeforeValidator(clean_loot_int)]


class LootInfo(BaseModel):
    gold: LootInt
    elixir: LootInt
    dark_elixir: LootInt


def get_loot_info(image: ImageCv2) -> LootInfo | None:
    raw = reader.readtext(  # type: ignore
        image,
        detail=0,
    )
    try:
        _, gold, elixir, dark_elixir = raw  # type: ignore
    except ValueError as e:
        logger.error(msg=f"value error in get loot info\nraw={raw}\nerr={e}")
        return None
    obj = {  # type: ignore
        "gold": gold,
        "elixir": elixir,
        "dark_elixir": dark_elixir,
    }
    try:
        return LootInfo.model_validate(obj=obj)
    except ValidationError as e:
        logger.error(msg=f"validation error in get loot info\nraw={raw}\nobj={obj}\nerr={e}")
        return None


def return_home_btn_exists(image: ImageCv2) -> bool:
    raw = reader.readtext(  # type: ignore
        image,
        detail=0,
    )
    try:
        _, _ = raw  # type: ignore
        logger.debug(msg=f"return_home_btn_exists[raw={raw}]")
        return True
    except ValueError:
        return False