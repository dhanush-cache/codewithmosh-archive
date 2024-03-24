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
        self.is_derived = derived
        self.is_bundle = True if self["type"] != "single" else False
        self.dirname = self.dirfmt_name()
        self.sections = [Section(section, self, index)
                         for index, section in enumerate(self["curriculum"], start=1)]
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

    def get_all(self) -> List["Course"]:
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

    def get_lessons(self, pdf: bool = False) -> List["Lesson"]:
        """Returns a list of all the lessons of a particular type."""

        return [
            lesson
            for course in self.courses
            for section in course
            for lesson in section
            if (lesson.is_pdf if pdf else lesson.is_video)
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
        return iter(self.sections)


class Section:
    """Class that represents a single section from courses on codewithmosh.com."""

    def __init__(self, sinfo: dict, parent: Course, index: int):
        self.raw = sinfo
        self.parent = parent
        self.name = self["name"]
        self.dirname = f"{self.parent.dirname}/{index:02}- {self}" if self.parent.is_derived else f"{index:02}- {self}"
        self.lessons = [Lesson(lesson, self, index)
                        for index, lesson in enumerate(self["lessons"], start=1)]
        self.duration = self.get_time()

    def get_time(self) -> int:
        """Returns the total duration of a section in seconds."""

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


class Lesson:
    """Class that represents a single lesson from courses on codewithmosh.com."""

    def __init__(self, linfo: dict, parent: Section, index: int):
        self.raw = linfo
        self.parent = parent
        self.name = self["name"]
        self.is_video = True if self["type"] == 1 else False
        self.is_pdf = self.check_pdf()
        self.is_crap = True if not (self.is_video or self.is_pdf) else False
        self.duration = self.get_time()
        self.dirname = f"{self.parent.dirname}/{index:02}- {self}"

    def check_pdf(self) -> bool:
        """Returns true if a lesson is (likely to be) a pdf."""

        if "cheat sheet" in self.name.lower():
            return True
        if self.is_video:
            return False
        whitelist = ["summary", "exercise"]
        for text in whitelist:
            if text in self.name.lower():
                return True
        return False

    def get_time(self) -> int:
        """Returns the duration of the lesson in seconds."""

        if not self.raw["duration"]:
            return 0
        time = self.raw["duration"]
        minutes, seconds = map(int, re.findall(r"\d+", time))
        return minutes * 60 + seconds

    def __str__(self):
        return self.name

    def __getitem__(self, key):
        return self.raw[key]

    def __len__(self):
        self.duration
