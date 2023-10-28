CHROMEDRIVER_PATH = 'browser/chromedriver'
CHROMEAPP_PATH = 'browser/Google Chrome.app'

CSUSM_EMAIL = 'lname001@csusm.edu'
CSUSM_PASSWORD = None

DUO_SECRET_PATH = "duo/base32_secret.hotp"

PREFERRED_ROOM = 4001
ATTENDEES_COUNT = 2

'''
TARGET_TIMES: dict where
    k: int              day of the week, where Monday == 0 ... Sunday == 6.
    v: tuple[int, int]  ISO 8601 formatted hour and minute.
'''
TARGET_TIMES = {
    0: (17, 30),
    2: (13, 30),
    4: (17, 30)
}
