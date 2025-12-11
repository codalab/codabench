# To run the tests locally
Install uv : [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

Run the following commands: 
```bash
cd tests
uv sync --frozen
uv run playwright install
docker compose exec -e DJANGO_SUPERUSER_PASSWORD=codabench django python manage.py createsuperuser --username codabench --email codabench@test.mail --no-input
uv run pytest test_auth.py test_account_creation.py test_competition.py test_submission.py
```

# Adding Tests
First, read the [documentation](https://playwright.dev/python/docs/writing-tests) on Playwright if you haven't used the tool before.
Since we are using pytest, you should also try to get more familiar with it by reading some of its [documentation](https://docs.pytest.org/en/stable/getting-started.html).


Once you are done, you can start adding tests. Playwright allows us to generate code with the following command :
```bash
uv run playwright codegen -o test.py
```

This will open two windows:
- A window containing the generated code
- A browser that is used by playwright to generate the code. Every action you take there will generate new lines of the code.

Once you are done, close the browser and open the file that playwright created containing the code it generated. Make sure to test it to make it sure it works.

Since we are passing custom commands to pytest, we need to remove some of the generated lines. Spawning a new browser and/or context will make them not take into the commands we have added in the `pytest.ini` file :
```python title="Original file created by codegen"
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost/")
    page.get_by_text("Benchmarks/Competitions Datasets Login Sign-up").click()
    page.get_by_role("link", name="Login").click()

    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
```

The previous file becomes :
```python title="Modified file"
from playwright.sync_api import Page, expect


def test_run(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_text("Benchmarks/Competitions Datasets Login Sign-up").click()
    page.get_by_role("link", name="Login").click()
```

