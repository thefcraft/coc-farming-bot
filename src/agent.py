import logging
import time
import uiautomator2 as u2  # pyright: ignore[reportMissingTypeStubs]
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Literal, overload
from .types import HasRead, ImageCv2, ImagePil, PointLike, RegionLike
from .config import Config
from . import img_parser

logger = logging.getLogger(__name__)


def parse_xml_root(file: HasRead[str] | HasRead[bytes]) -> ET.Element:
    """Parse XML file and return root element."""
    return ET.parse(file).getroot()


class CocAgentBase:
    def __init__(self, config: Config) -> None:
        self.config: Config = config
        self.device: u2.Device = u2.connect()
        self.width, self.height = self.device.window_size()
        assert self.width > self.height, "device should be in landscape mode"
        assert self.width == config.width and self.height == config.height, (
            "config and device missmatch"
        )
        xml = self.device.dump_hierarchy()
        root = ET.parse(StringIO(initial_value=xml)).getroot()
        if not list(
            filter(
                lambda node: node is not None and node == "com.supercell.clashofclans",
                map(
                    lambda node: node.attrib.get("package", None),
                    root,
                ),
            )
        ):
            raise RuntimeError("please open com.supercell.clashofclans in forground")

    def click(self, point: PointLike) -> None:
        self.device.click(x=point.x, y=point.y)

    def screenshot(self, region: RegionLike | None = None) -> ImagePil:
        img: ImagePil = self.device.screenshot()  # pyright: ignore[reportAssignmentType]

        if region is None:
            return img

        return img.crop(
            (
                region.x,
                region.y,
                region.x + region.w,
                region.y + region.h,
            )
        )

    def screenshot_cv(self, region: RegionLike | None = None) -> ImageCv2:
        img: ImageCv2 = self.device.screenshot(format="opencv")  # pyright: ignore[reportAssignmentType]
        if region is None:
            return img

        img_cropped = img[
            region.y : region.y + region.h,
            region.x : region.x + region.w,
        ]
        return img_cropped


class CocAgent(CocAgentBase):
    def press_attack(self, wait_seconds: float | None) -> None:
        self.click(point=self.config.attack_btn)
        if wait_seconds is not None:
            time.sleep(wait_seconds)

    def press_find_match(self, wait_seconds: float | None) -> None:
        self.click(point=self.config.find_match_btn)
        if wait_seconds is not None:
            time.sleep(wait_seconds)

    def press_final_attack(self, wait_seconds: float | None) -> None:
        self.click(point=self.config.final_attack_btn)
        if wait_seconds is not None:
            time.sleep(wait_seconds)

    def press_next_attack(self, wait_seconds: float | None) -> None:
        self.click(point=self.config.next_attack_btn)
        if wait_seconds is not None:
            time.sleep(wait_seconds)

    def loot_info(self) -> img_parser.LootInfo | None:
        screen = self.screenshot_cv(
            region=self.config.loot_info_region,
        )
        return img_parser.get_loot_info(screen)
    
    def start_attack(self) -> None:
        logger.debug("Pressing attack button")
        self.press_attack(wait_seconds=self.config.wait_seconds)

        logger.debug("Pressing find match button")
        self.press_find_match(wait_seconds=self.config.wait_seconds)

        logger.debug("Pressing final attack button")
        self.press_final_attack(wait_seconds=self.config.wait_seconds)


    @overload
    def find_attack(self, *, return_on_max_tries: Literal[False] = False) -> img_parser.LootInfo: ...
    @overload
    def find_attack(
        self, *, return_on_max_tries: Literal[True]
    ) -> img_parser.LootInfo | None: ...
    def find_attack(
        self, *, return_on_max_tries: bool = False
    ) -> img_parser.LootInfo | None:
        logger.info(
            "Waiting for loot info (max_tries=%s, wait_seconds=%s)",
            self.config.max_tries,
            self.config.wait_seconds,
        )
        num_tries: int = 0
        while True:
            info = self.loot_info()
            if info is not None:
                logger.info("Loot info found: %s", info)
                if (
                    info.gold >= self.config.min_loot.gold
                    and info.elixir >= self.config.min_loot.elixir
                    and info.dark_elixir >= self.config.min_loot.dark_elixir
                ):
                    logger.info(
                        "Loot requirements satisfied "
                        "(gold=%s/%s, elixir=%s/%s, dark_elixir=%s/%s)",
                        info.gold,
                        self.config.min_loot.gold,
                        info.elixir,
                        self.config.min_loot.elixir,
                        info.dark_elixir,
                        self.config.min_loot.dark_elixir,
                    )
                    break

                num_tries = 0

                logger.debug("Pressing next attack button")
                self.press_next_attack(wait_seconds=self.config.wait_seconds)

                continue

            logger.warning(
                "Loot info not detected on attempt %s",
                num_tries + 1,
            )
            time.sleep(self.config.wait_seconds)
            num_tries += 1
            if num_tries >= self.config.max_tries:
                logger.error("max_tries reached")
                if return_on_max_tries:
                    return None
                raise RuntimeError("max_tries reached.")

        return info

    def attack(self):
        logger.info("Starting attack deployment")
        i: int = 0
        for troop_index, (troop_count, (x, y)) in enumerate(
            zip(self.config.troop_counts, self.config.troop_btns),
            start=1,
        ):
            logger.info(
                "Selecting troop slot %s at (%s, %s) with count=%s",
                troop_index,
                x,
                y,
                troop_count,
            )
            self.device.click(x=x, y=y)
            time.sleep(self.config.wait_troop_seconds)
            for _ in range(troop_count):
                if i % 4 == 0:
                    self.click(self.config.troop_drop_top)
                elif i % 4 == 1:
                    self.click(self.config.troop_drop_left)
                elif i % 4 == 2:
                    self.click(self.config.troop_drop_right)
                elif i % 4 == 3:
                    self.click(self.config.troop_drop_bottom)
                i += 1
                time.sleep(self.config.wait_troop_seconds)

        logger.info("Attack deployment completed")

        logger.info("Waiting for return home button")

        num_checks: int = 0
        while True:
            num_checks += 1
            if num_checks % 10 == 0:
                logger.debug(
                    "Checking for return home button (attempt=%s)",
                    num_checks,
                )
            if num_checks > self.config.max_wait_attack_seconds:
                logger.error(
                    "Return home button not detected after %s seconds", num_checks
                )
                raise RuntimeError("Timed out waiting for return home button")

            screen = self.screenshot_cv(
                region=self.config.return_home_region,
            )
            done = img_parser.return_home_btn_exists(image=screen)
            if done:
                logger.info(
                    "Return home button detected",
                )
                break
            time.sleep(self.config.wait_seconds)

        region = self.config.return_home_region

        click_x = region.x + (region.w // 2)
        click_y = region.y + (region.h // 2)

        logger.info(
            "Clicking return home button at (%s, %s)",
            click_x,
            click_y,
        )

        self.device.click(
            x=click_x,
            y=click_y,
        )

        time.sleep(self.config.wait_seconds)

        logger.info("Attack flow completed")
