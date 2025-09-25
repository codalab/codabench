
## What and Why
It's useful to test various parts of the system with lots of data or many intricate actions. The selenium tests do this generally and are used as a guide for this tutorial. One problem is that Selenium needs to launch an instance of a browser to control. Our tests do this inside a docker container and uses a test database that doesn't persist as it cleans up after itself. We need to be able to control a live codabench session that is running. To do that we install a driver locally which is normally only inside the selenium docker container during tests. It is specific to your browser so keep that in mind.

## Virtualenv
You'll need a python virtual env as you don't want to be inside Django or you won't be able to launch a browser. 

### Virtualenv
I used 3.8.
```bash
python3 -m venv codabench
source ./codabench/bin/activate
```

### Pyenv
```bash
pyenv install 3.8
pyenv virtualenv 3.8 codabench
pyenv activate codabench
```

## Requirements
We have a couple extra things like `webdriver-manager` for getting a driver programmatically and `selenium` needs to be upgraded to use modern client interface.
```bash
pip install -r requitements.txt
pip install -r requitements.dev.txt
pip install webdriver-manager
pip install --upgrade selenium
```

## Automate competition creation
[Main Selenium Docs](https://selenium-python.readthedocs.io/)  
[Install](https://selenium-python.readthedocs.io/installation.html)  
[Getting Started](https://selenium-python.readthedocs.io/getting-started.html)  

```python
import os, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Use `ChromeDriverManager` to ensure the `chromedriver` is installed and in PATH
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# ... now use `driver` to control the local Chrome instance
driver.get("http://localhost/accounts/login")

# Use CSS selectors to find the input fields and button
username_input = driver.find_element(By.CSS_SELECTOR, 'input[name="username"]')
password_input = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
submit_button = driver.find_element(By.CSS_SELECTOR, '.submit.button')

# Type the credentials into the fields
username_input.send_keys('bbearce')
password_input.send_keys('testtest')

# Click the submit button
submit_button.click()

comp_path = "/home/bbearce/Documents/codabench/src/tests/functional/test_files/competition_v2_multi_task.zip"
def upload_competition(competition_zip_path):
    driver.get("http://localhost/competitions/upload")
    file_input = driver.find_element(By.CSS_SELECTOR, 'input[ref="file_input"]')
    file_input.send_keys(os.path.join(competition_zip_path))


for i in range(30):
    upload_competition(comp_path)
    time.sleep(5) # tune for your system

```