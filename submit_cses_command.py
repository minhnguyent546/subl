"""
What does this plugin do?
-> Submit your solution to CSES via command palette

How to set up?
- Install selenium: pip install selenium
- Install chromedriver (assume you are using Google Chrome): https://chromedriver.chromium.org/downloads
- Add these commands below to your User/Default.sublime-commands:
    {
      "caption": "Submit CSES Solution",
      "command": "submit_cses",
      "args": {
        "username": "YOUR_CSES_USERNAME",
        "password": "YOUR_CSES_PASSWORD",
        "chromedriver_path": "/path/to/chromedriver",
      },
    },
- Change the path below (line 36) to where you installed selenium

Open command palette (Ctrl+shift+P) and type "Submit CSES Solution" to start submitting.

When submitting, problem ID will be inferred from the file name if possible.
After your solution is submitted, you should see the status in the status bar
(bottom left corner in Sublime Text), including submitting, submitted, verdict, etc.
"""

import sublime
import sublime_plugin
from enum import Enum

import os
import re
import sys
from typing import Union

if '/usr/lib/python3.12/site-packages' not in sys.path:
    sys.path.append('/usr/lib/python3.12/site-packages')  # change to where you installed selenium

import selenium.common.exceptions
import selenium.webdriver as webdriver
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


class CsesVerdict(Enum):
    AC = 'ACCEPTED'
    TLE = 'TIME LIMIT EXCEEDED'
    WA = 'WRONG ANSWER'
    OLE = 'OUTPUT LIMIT EXCEEDED'
    MLE = 'MEMORY LIMIT EXCEEDED'

class SubmitCsesCommand(sublime_plugin.TextCommand):
    def run(
        self,
        edit: sublime.Edit,
        username: str,
        password: str,
        problem_id: int,
        chromedriver_path: str,
    ):
        self.username = username
        self.password = password
        self.problem_id = problem_id
        self.chromedriver_path = chromedriver_path

        file_name = self.view.file_name()
        assert file_name is not None

        sublime.set_timeout_async(self.submit_solution)

    def is_enabled(self) -> bool:
        return self.view.file_name() is not None

    def input(self, args) -> Union[sublime_plugin.TextInputHandler, None]:
        if 'problem_id' not in args:
            return ProblemIdInputHandler(self.view)
        return None

    def submit_solution(self) -> None:
        solution_path = self.view.file_name()
        assert solution_path is not None
        problem_id = self.problem_id

        submit_path = f'https://cses.fi/problemset/submit/{problem_id}'
        self.view.window().status_message(f'Submitting solution...')

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1080,1080")
        service = Service(executable_path=self.chromedriver_path)  # change to your chromedriver path
        driver = webdriver.Chrome(options=chrome_options, service=service)

        driver.get(submit_path)
        driver.implicitly_wait(3)

        # get problem name
        problem_title = driver.find_element(By.CSS_SELECTOR, '.navigation .title-block h1').text
        self.view.window().status_message(f'Found problem: {problem_title}')

        # login
        login_button = driver.find_element(By.CSS_SELECTOR, '.controls .account[href="/login"]')
        login_button.click()
        driver.implicitly_wait(1)

        username_input = driver.find_element(By.CSS_SELECTOR, '#nick')
        username_input.send_keys(self.username)
        password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"][name="pass"]')
        password_input.send_keys(self.password)
        login_button = driver.find_element(By.CSS_SELECTOR, 'form input[type="submit"]')
        login_button.click()

        # submit solution
        choose_file_button = driver.find_element(By.CSS_SELECTOR, 'input[type="file"][name="file"]')
        lang = driver.find_element(By.CSS_SELECTOR, '#lang')
        cpp_version = driver.find_element(By.CSS_SELECTOR, '#option')
        submit_solution_button = driver.find_element(By.CSS_SELECTOR, 'form input[type="submit"]')
        choose_file_button.send_keys(solution_path)
        lang.send_keys('C++')
        cpp_version.send_keys('C++20')
        submit_solution_button.click()
        self.view.window().status_message(f'Submitted to problem {problem_id}: {problem_title}')

        try:
            verdict = WebDriverWait(driver, timeout=5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".summary-table .inline-score.verdict")
                )
            ).text
            if verdict == CsesVerdict.AC.value:
                code_time = -1.0
                code_times = driver.find_elements(By.CSS_SELECTOR, 'table td.verdict.ac + td')
                for item in code_times:
                    test_code_time = item.text
                    if test_code_time.endswith('s'):
                        test_code_time = test_code_time[:-1].strip()
                    test_code_time = float(test_code_time)
                    code_time = max(code_time, test_code_time)
                self.view.window().status_message(f'Verdict: {verdict} | Time: {code_time} s')
            else:
                self.view.window().status_message(f'Verdict: {verdict}')
        except selenium.common.exceptions.TimeoutException as e:
            self.view.window().status_message(f'Could not get verdict for problem {problem_title}: {e}')


class ProblemIdInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, view: sublime.View) -> None:
        self.view = view
        file_name = self.view.file_name()
        assert file_name is not None
        self.problem_id = extract_id_from_file_path(file_name)

    def name(self) -> str:
        return 'problem_id'
    
    def placeholder(self) -> str:
        return 'Problem id. E.g. 1739'

    def initial_text(self) -> str:
        if self.problem_id is None:
            return ''
        return str(self.problem_id)

    def validate(self, text: str) -> bool:
        return len(text) > 0 and text.isdigit()

def extract_id_from_file_path(file_path: str) -> Union[int, None]:
    file_basename = os.path.basename(file_path)
    numbers = re.findall(r'\d+', file_basename)
    if not numbers:
        return None
    return int(numbers[0])
