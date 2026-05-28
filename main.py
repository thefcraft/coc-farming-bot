import os
import time
import logging

from src.agent import CocAgent
from src.config import Config
from src.notify import beep

logger = logging.getLogger(__name__)


def main() -> None:
    config = Config.from_dotenv()
    logger.debug("Config loaded")

    agent = CocAgent(config=config)
    logger.debug("CocAgent initialized")

    num_tries: int = 0
    while True:
        if num_tries == 0:
            agent.start_attack()
        loot_info = agent.find_attack(
            return_on_max_tries=config.next_attack_if_loot_info_failed
        )
        if loot_info is None and config.next_attack_if_loot_info_failed:
            logger.debug("Pressing next attack button")
            agent.press_next_attack(wait_seconds=config.wait_seconds)
            num_tries += 1
            if num_tries >= config.max_tries_loot_info_failed:
                logger.error("max_tries_loot_info_failed reached")
                raise RuntimeError("max_tries_loot_info_failed reached.")
            continue

        agent.attack()

        if config.notify:
            beep()

        time.sleep(config.wait_next_attack_seconds)
        num_tries = 0


if __name__ == "__main__":

    class PackageFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.name == "__main__" or record.name.startswith("src")

    handler_file = logging.FileHandler("main.log", mode="a")
    handler_stream = logging.StreamHandler()

    handler_file.addFilter(PackageFilter())
    handler_stream.addFilter(PackageFilter())

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
        handlers=[
            handler_file,
            handler_stream,
        ],
    )
    # for dir_name in ("dump", "dump_img"):
    #     if not os.path.exists(dir_name):
    #         os.mkdir(dir_name)
    #     else:
    #         assert os.path.isdir(dir_name), f"{dir_name} must be a directory."
    main()
