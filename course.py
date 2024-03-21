import json
import re
from typing import Union, Dict, List

import requests
from bs4 import BeautifulSoup


class Course:
    """Class to work with data from courses on codewithmosh.com."""

    def __init__(self, slug: str, derived: bool = False):
        self.url = f"https://codewithmosh.com/p/{slug}/"
        self.course_info = self.get_data(self.url)
        self.sections = [Section(section) for section in self["curriculum"]]
        self.is_derived = derived
        self.is_bundle = True if self["type"] != "single" else False
        self.dirname = self.dirfmt_name()
        self.courses = self.get_all()

    def get_data(self, url) -> Union[Dict, List[Dict]]:
        """Returns appropriate data from a url.
        Only returns the useful data reguarding course or courses."""

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        pattern = re.compile(".*json.*")
        tag = soup.find("script", type=pattern)
        if tag:
            data = json.loads(tag.get_text())["props"]["pageProps"]
        if "courses" in data:
            return data["courses"]
        course = data["course"]
        course["curriculum"] = data["curriculum"]
        return course

    def get_all(self) -> List['Course']:
        """Returns the list of all courses in a bundle."""

        if not self.is_bundle:
            return [self]
        url = "https://codewithmosh.com/courses"
        data = self.get_data(url)
        return [
            Course(course["slug"], derived=True)
            for course in data
            if course["id"] in self["bundleContents"]
        ]

    def dirfmt_name(self) -> str:
        """Returns the ideal name for naming directories from the name of the course."""

        name = self["name"]
        keywords = [
            "The Ultimate",
            "Ultimate",
            "The Complete",
            "Complete",
            "Mastering",
            "Mastery",
            "Series",
            "Course",
            "Bundle",
        ]
        replace = [(r"\s+", " "), (r":", "-")]
        for text in keywords:
            name = name.replace(text, "")
        for old, new in replace:
            name = re.sub(old, new, name)
        if self.is_derived and "part" in name.lower():
            name = name[name.lower().find("part"):]
        return name.strip()

    def get_filenames(self, pdf: bool = False) -> List[str]:
        if self.is_bundle:
            return [
                f"{course.dirname}/{dirname}"
                for course in self.courses
                for dirname in course.get_filenames(pdf=pdf)
            ]
        return [
            f"{s:02}- {section['name']}/{l:02}- {lesson['name']}"
            for s, section in enumerate(self, start=1)
            for l, lesson in enumerate(section["lessons"], start=1)
            if lesson["type"] == pdf + 1
        ]

    def __str__(self):
        return self["name"]

    def __getitem__(self, key):
        return self.course_info[key]

    def __len__(self):
        count = 0
        if self.is_bundle:
            for course in self.courses:
                count += len(course)
            return count
        for section in self:
            count += len(section["lessons"])
        return count

    def __iter__(self):
        return iter(self.courses) if self.is_bundle else iter(self.sections)


class Lesson:
    """Class that represents a single lesson from courses on codewithmosh.com."""

    def __init__(self, linfo: dict):
        self.raw = linfo
        self.name = self['name']
        self.is_video = True if self['type'] == 1 else False
        self.is_pdf = not self.is_video and self.check_pdf()
        self.is_crap = True if not (self.is_video or self.is_pdf) else False
        self.duration = self.get_time()

    def check_pdf(self) -> bool:
        whitelist = []
        for text in whitelist:
            if text in self.name:
                return True
        return False

    def get_time(self) -> int:
        if not self.raw["duration"]:
            return 0
        time = self.raw["duration"]
        minutes, seconds = map(int, re.findall(r'\d+', time))
        return minutes * 60 + seconds

    def __str__(self):
        return self.name

    def __getitem__(self, key):
        return self.raw[key]

    def __len__(self):
        self.duration


class Section:
    """Class that represents a single section from courses on codewithmosh.com."""

    def __init__(self, sinfo: dict):
        self.raw = sinfo
        self.name = self['name']
        self.lessons = [Lesson(lesson) for lesson in self["lessons"]]
        self.duration = self.get_time()

    def get_time(self) -> int:
        time = 0
        for lesson in self.lessons:
            time += lesson.duration
        return time

    def __str__(self):
        return self.name

    def __getitem__(self, key):
        return self.raw[key]

    def __len__(self):
        self.duration

    def __iter__(self):
        return iter(self.lessons)
