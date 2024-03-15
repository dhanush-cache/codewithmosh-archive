from pathlib import Path
from typing import Union

from ffmpeg import probe


class Video(Path):
    """Extention of Path class for video files."""

    def __init__(self, *args, **kwargs):
        Path().__init__(*args, **kwargs)

    _flavour = type(Path())._flavour  # type: ignore

    def has_subs(self) -> bool:
        """Returns true if the video has embeded subs."""

        return "subtitle" in {i["codec_type"] for i in probe(self)["streams"]}

    def sub_file(self) -> Union[Path, None]:
        """Returns the Path to the subtitle file in the same directory(if exists)."""

        if list(self.parent.glob(f"{self.stem}*.srt")):
            return next(self.parent.glob(f"{self.stem}*.srt"))
