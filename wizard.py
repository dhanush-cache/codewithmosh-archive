from pathlib import Path
from zipfile import ZipFile
from typing import List
import shutil
import subprocess

from natsort import natsorted
import requests

from course import Course, Lesson
from video import Video


class FileWizard:
    """Class to organize files locally"""

    def __init__(self, source: str, course: Course):
        self.source = Path(source)
        self.course = course
        self.root = Path("/sdcard/Programming Videos")
        self.target = self.root / course.dirname
        self.cache = self.target / ".cache"
        self.assembled = False

    def assemble(self):
        """Assemble files at destination."""

        if self.source.is_dir():
            shutil.move(self.source, self.target)
        elif self.source.suffix == ".zip":
            ZipFile(self.source).extractall(self.target)
            ZipFile(self.source).close()
        files = list(self.target.iterdir())
        if len(files) == 1:
            shutil.move(files[0], self.cache)
        else:
            self.cache.mkdir(parents=True, exist_ok=True)
            for file in files:
                shutil.move(file, self.cache)
        self.assembled = True

    def cleanup(self, *suffixes):
        """Removes all unwanted files and folders"""

        exceptions = [".mp4", ".mkv", ".zip", ".pdf", ".jpeg", ".jpg"]
        whitelist = [ext for ext in exceptions if ext not in suffixes]
        for path in sorted(self.cache.rglob("*"), reverse=True):
            if path.is_file() and path.suffix not in whitelist:
                path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
        if self.cache.is_dir() and not any(self.cache.iterdir()):
            self.cache.rmdir()

    def dl_thumb(self) -> List[Path]:
        """Downloads all thumbnails from the course and it's children."""

        self.cache.mkdir(parents=True, exist_ok=True)
        thumbnails = []
        for course in self.course.courses:
            url = course["imageUrl"]
            name = course["id"]
            response = requests.get(url)
            (self.cache / f"{name}.jpeg").write_bytes(response.content)
            thumbnails.append(self.cache / f"{name}.jpeg")
        return thumbnails

    def get_names(self, ext: str = "mp4") -> List[Path]:
        """Returns a sorted list of Path objects for all files by extension."""

        if not self.assembled:
            self.assemble()
        return natsorted(self.cache.rglob(f"*.{ext}"))

    def dry_move(self):
        """Moves all the video files to thier final destination."""

        files = self.get_names()
        names = self.course.get_lessons()
        for file, name in zip(files, names):
            name = self.target / name.dirname
            name.parent.mkdir(parents=True, exist_ok=True)
            file.rename(f"{name}.mp4")

    def ffprocess(self, raw: Path, lesson: Lesson):
        """Processes a given raw file as per the lesson attributes."""

        inp = Video(raw)
        out = Video(self.target / f"{lesson.dirname}.mkv")

        command = ["ffmpeg", "-y"]
        inputs = ["-i", inp]
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
            f"title={lesson}",
            "-metadata",
            f"comment={lesson.parent.name}",
            "-metadata:s:a:0",
            "language=en",
        ]
        th_name = lesson.parent.parent["id"]
        th_file = self.cache / f"{th_name}.jpeg"

        thumbnail = [
            "-attach",
            th_file if self.thumb else inp.with_suffix(".jpeg"),
            "-metadata:s:t",
            f"filename={lesson}",
            "-metadata:s:t",
            "mimetype=image/jpeg",
        ]
        output = [out]

        if not self.thumb:
            frame = str(self.intro if out.name.startswith(
                "01") else self.other)
            extract = ["-ss", frame, "-vframes", "1", inp.with_suffix(".jpeg")]
            extract = command + inputs + extract
            subprocess.run(extract, capture_output=True)

        out.parent.mkdir(parents=True, exist_ok=True)
        embeded = inp.has_subs()
        srt_file = inp.sub_file()
        if embeded:
            selection += ["-map", "0:s"]
            metadata += ["-metadata:s:s:0", "language=en"]
            codec += ["-c:s", "srt"]
        elif srt_file:
            inputs += ["-i", srt_file]
            selection += ["-map", "1:s"]
            metadata += ["-metadata:s:s:0", "language=en"]
        command += (
            inputs + selection + codec + _metadata + metadata + thumbnail + output
        )
        subprocess.run(command, capture_output=True)

    def ffmove(self, intro=0, other=0, thumb=False):
        """Processes all files and places them in their final destination."""

        files = self.get_names()
        names = self.course.get_lessons()
        self.intro = intro
        self.other = other
        self.thumb = thumb
        if self.thumb:
            self.dl_thumb()
        if len(files) != len(names):
            print(f"Local:  {len(files)}")
            print(f"Remote: {len(names)}")
            raise ValueError("Not enough local files!!!")
        for file, lesson in zip(files, names):
            print(lesson.dirname)
            self.ffprocess(file, lesson)

    def extract_zips(self):
        """Moves zips to final destination after extracting zips from them"""

        archives = self.target / "Files" / "Archives"
        files = self.get_names(ext="zip")
        if files:
            archives.mkdir(parents=True, exist_ok=True)
        for index, file in enumerate(files, start=1):
            print(f"extracting {file}")
            target_name = f"code.zip" if len(
                files) <= 1 else f"code-{index:02}.zip"
            target_path = archives / target_name

            with ZipFile(file) as source, ZipFile(target_path, "w") as target:
                for file_info in source.infolist():
                    if file_info.filename.endswith(".pdf"):
                        source.extract(file_info, path=file.parent)
                    else:
                        file_content = source.read(file_info.filename)
                        target.writestr(file_info.filename, file_content)

    def pdfmove(self, organize=True):
        """Move pdfs to final destination"""

        files = self.get_names(ext="pdf")
        names = self.course.get_lessons(pdf=True)
        documents = self.target / "Files" / "Documents"
        if files and not organize:
            documents.mkdir(parents=True, exist_ok=True)
        for file, name in zip(enumerate(files), names):
            index, file = file
            if organize:
                name = self.target / name.dirname
                name.parent.mkdir(parents=True, exist_ok=True)
                file.rename(f"{name}.pdf")
            else:
                file.rename(documents / f"{index:02}- {file.name}")

    def __eq__(self, other: Course):
        return True if len(self.get_names()) == len(other.get_lessons()) else False
