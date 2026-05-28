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

    while True:
        _ = agent.find_attack()

        if config.notify:
            beep()

        agent.attack()
        
        if config.notify:
            beep()

        time.sleep(config.wait_next_attack_seconds)
        
    

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
