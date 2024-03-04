import json
import re
from typing import Union, Dict, List

import requests
from bs4 import BeautifulSoup


class Course:
    """Class to work with data from courses on codewithmosh.com."""

    def __init__(self, slug: str):
        self.url = f"https://codewithmosh.com/p/{slug}/"
        self.course_info = self.get_data(self.url)

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
