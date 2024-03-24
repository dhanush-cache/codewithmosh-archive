from course import Course
from wizard import FileWizard
from input_data import raw_data, slug, intro, others, organize

source = raw_data
course = Course(slug)

wizard = FileWizard(source, course)
wizard.assemble()
wizard.extract_zips()
wizard.cleanup()

try:
    wizard.ffmove(intro, others) if intro and others else wizard.ffmove(
        thumb=True)
except ValueError as ex:
    print(ex)

wizard.pdfmove(organize)
wizard.cleanup(".mp4", ".jpeg", ".jpg", ".zip")
