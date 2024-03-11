from pathlib import Path
from zipfile import ZipFile
from typing import List
import shutil

from natsort import natsorted

from course import Course


class FileWizard:
    """Class to organize files locally"""

    def __init__(self, source: Path, course: Course):
        self.source = source
        self.course = course
        self.root = Path("/sdcard/Programming Videos")
        self.target = self.root / course.dirname
        self.cache = self.target / ".cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.assembled = False

    def assemble(self):
        """Moves source to destination.
        If source is a zip file, extracts it.
        If source is a folder file, simply moves it."""

        if self.source.is_dir():
            shutil.move(self.source, self.target)
        elif self.source.suffix == ".zip":
            ZipFile(self.source).extractall(self.target)
            ZipFile(self.source).close()
        files = list(self.target.iterdir())
        if len(files) == 1:
            shutil.move(files[0], self.cache)
        else:
            for file in files:
                shutil.move(file, self.cache)
        self.assembled = True

    def get_names(self, ext: str = "mp4") -> List[Path]:
        """Returns a sorted list of Path objects for all files by extension."""

        if not self.assembled:
            self.assemble()
        return natsorted(self.cache.rglob(f"*.{ext}"))

    def dry_move(self):
        """Moves all the video files to thier final destination."""

        files = self.get_names()
        names = self.course.get_filenames()
        for file, name in zip(files, names):
            name = self.target / name
            name.parent.mkdir(parents=True, exist_ok=True)
            file.rename(f"{name}.mp4")

    def __eq__(self, other: Course):
        return True if len(self.get_names()) == len(other.get_filenames()) else False
