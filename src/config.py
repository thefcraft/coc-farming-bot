from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, model_validator, BeforeValidator, Field
from typing import Self, IO, Annotated, Any
from os import PathLike


class BasePoint(BaseModel):
    x: int
    y: int


class BaseRegion(BaseModel):
    x: int
    y: int
    w: int
    h: int


class AttackBtn(BasePoint): ...


class FindMatchBtn(BasePoint): ...


class FinalAttackBtn(BasePoint): ...


class NextAttackBtn(BasePoint): ...


class LootInfoRegion(BaseRegion): ...


class TroopDropTop(BasePoint): ...


class TroopDropLeft(BasePoint): ...


class TroopDropRight(BasePoint): ...


class TroopDropBottom(BasePoint): ...

class ReturnHomeRegion(BaseRegion): ...

def clean_loot_int(v: Any):
    if isinstance(v, str):
        return v.replace(",", "")
    return v


type LootInt = Annotated[int, BeforeValidator(clean_loot_int)]


class MinLoot(BaseModel):
    gold: LootInt
    elixir: LootInt
    dark_elixir: LootInt


class Config(BaseSettings):
    width: int
    height: int
    attack_btn: AttackBtn
    find_match_btn: FindMatchBtn
    final_attack_btn: FinalAttackBtn
    next_attack_btn: NextAttackBtn
    loot_info_region: LootInfoRegion
    min_loot: MinLoot

    troop_btns: list[tuple[int, int]] = Field(min_length=1)
    troop_counts: list[int] = Field(min_length=1)
    troop_drop_top: TroopDropTop
    troop_drop_left: TroopDropLeft
    troop_drop_right: TroopDropRight
    troop_drop_bottom: TroopDropBottom

    return_home_region: ReturnHomeRegion

    wait_troop_seconds: float = 0.1
    wait_seconds: float = 1.0
    wait_next_attack_seconds: float = 3.0
    max_tries: int = 10
    max_wait_attack_seconds: int = 500

    notify: bool = False


    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def verify_landscape(self) -> Self:
        if self.width < self.height:
            raise ValueError("config should be in landscape mode")
        if len(self.troop_btns) != len(self.troop_counts):
            raise ValueError("troop_btns and troop_counts must have same length")
        return self

    @classmethod
    def from_env(cls) -> Self:
        return cls()  # pyright: ignore[reportCallIssue]

    @classmethod
    def from_dotenv(
        cls,
        dotenv_path: PathLike[str] | str | None = None,
        stream: IO[str] | None = None,
        verbose: bool = False,
        override: bool = False,
        interpolate: bool = True,
        encoding: str | None = "utf-8",
    ) -> Self:
        from dotenv import load_dotenv

        load_dotenv(
            dotenv_path=dotenv_path,
            stream=stream,
            verbose=verbose,
            override=override,
            interpolate=interpolate,
            encoding=encoding,
        )
        return cls.from_env()
