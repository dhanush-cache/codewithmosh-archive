from pathlib import Path
from zipfile import ZipFile
from typing import List
import shutil
import subprocess

from natsort import natsorted

from course import Course
from video import Video


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

    def cleanup(self, *suffixes):
        """Removes all unwanted files and folders"""

        suffixes += ".mp4", ".mkv", ".zip", ".pdf"
        for path in sorted(self.cache.rglob("*"), reverse=True):
            if path.is_file() and path.suffix not in suffixes:
                path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()

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

    def ffprocess(self, raw: Path, name: str):
        raw = Video(raw)
        out = Video(self.target / f"{name}.mkv")

        frame = self.intro if out.name.startswith("01") else self.other
        frame = str(frame)

        command = ["ffmpeg", "-y"]
        inputs = ["-i", raw]
        selection = ["-map", "0:v", "-map", "0:a"]
        codec = ["-c", "copy"]
        _metadata = [
            "-map_metadata",
            "-1",
            "-map_metadata:s",
            "-1",
            "-map_metadata:g",
            "-1",
            "-map_chapters",
            "-1",
            "-map_chapters:s",
            "-1",
            "-map_chapters:g",
            "-1",
        ]
        metadata = [
            "-metadata",
            f"title={out.stem[4:]}",
            "-metadata:s:a:0",
            "language=en",
        ]
        thumbnail = [
            "-attach",
            raw.with_suffix(".jpeg"),
            "-metadata:s:t",
            f"filename={out.stem[4:]}",
            "-metadata:s:t",
            "mimetype=image/jpeg",
        ]
        output = [out]

        extract = ["-ss", frame, "-vframes", "1", raw.with_suffix(".jpeg")]
        extract = command + inputs + extract
        subprocess.run(extract)

        out.parent.mkdir(parents=True, exist_ok=True)
        embeded = raw.has_subs()
        srt_file = raw.sub_file()
        if embeded:
            selection += ["-map", "0:s"]
            metadata += ["-metadata:s:s:0", "language=en"]
        elif srt_file:
            inputs += ["-i", srt_file]
            selection += ["-map", "1:s"]
            metadata += ["-metadata:s:s:0", "language=en"]
        command += (
            inputs + selection + codec + _metadata + metadata + thumbnail + output
        )
        subprocess.run(command, text=True)

    def ffmove(self, intro, other):
        files = self.get_names()
        names = self.course.get_filenames()
        self.intro = intro
        self.other = other
        for file, name in zip(files, names):
            self.ffprocess(file, name)

    def __eq__(self, other: Course):
        return True if len(self.get_names()) == len(other.get_filenames()) else False
