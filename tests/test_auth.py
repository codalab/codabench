from playwright.sync_api import Browser
import toml
import pytest

data = toml.load("config/config.toml")


@pytest.mark.only_browser("firefox")
def test_auth(browser: Browser) -> None:
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:8000")
    page.get_by_role("link", name="Login").click()
    page.get_by_role("textbox", name="username or email").click()
    page.get_by_role("textbox", name="username or email").fill(
        data["default_user"]["username"]
    )
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill(data["default_user"]["password"])
    page.get_by_role("button", name="Log In").click()
    context.storage_state(path="config/state.json")
    # ---------------------
    context.close()
