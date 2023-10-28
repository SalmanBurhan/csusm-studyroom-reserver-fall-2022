from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import logging
import constants


class Browser(webdriver.Chrome):

    def __init__(self):

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument('--headless')
        options.add_argument("--window-size=800,600")
        options.binary_location = constants.CHROMEAPP_PATH + \
            '/Contents/MacOS/Google Chrome'

        self.logger = logging.getLogger('Browser')
        self.logger.setLevel(level=logging.INFO)
        self.logger.info('Initializing ChromeDriver Service')

        service = Service(constants.CHROMEDRIVER_PATH)

        self.logger.info(
            f'Initializing Chrome Instance with Options: {options.arguments}')
        super().__init__(service=service, options=options)

        self.wait = WebDriverWait(self, 10)

    def get(self, url):
        self.logger.info(f'Navigating To URL ==> {url}')
        super().get(url)

    def element(self, css_selector: str):
        try:
            e = self.wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, css_selector)))
        except TimeoutException:
            e = None
        return e

    def elements(self, css_selector: str):
        try:
            e = self.wait.until(EC.visibility_of_all_elements_located(
                (By.CSS_SELECTOR, css_selector)))
        except TimeoutException:
            e = []
        return e
