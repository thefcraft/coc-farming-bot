import os
import nava  # pyright: ignore[reportMissingTypeStubs]

basedir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
)
assets = os.path.join(basedir, "assets")


def beep() -> None:
    nava.play(  # pyright: ignore[reportUnknownMemberType]
        os.path.join(assets, "beep-02.wav"),
        async_mode=False,
        loop=False,
    )


if __name__ == "__main__":
    beep()
