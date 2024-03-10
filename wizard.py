from pathlib import Path

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
