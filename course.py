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
        return iter(self.courses) if self.is_bundle else iter(self["curriculum"])
