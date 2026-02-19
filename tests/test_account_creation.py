import psycopg
import toml
from loguru import logger
from playwright.sync_api import expect, Page
import random


def randomNumber():
    return str(random.randint(0, 1000))


data = toml.load("config/config.toml")
test_user = data["test_user"]["username"] + randomNumber()
test_password = data["test_user"]["password"] + randomNumber()
test_email = test_user + "@email.com"
test_failed_user = data["test_failed_user"]["username"]
db_host = data["database"]["host"]
db_user = data["database"]["user"]
db_name = data["database"]["name"]
db_password = data["database"]["password"]


def test_FailedAccountCreationUsername(page: Page):
    page.goto("/")
    page.get_by_role("link", name="Sign-up").click()
    page.get_by_role("textbox", name="username").click()
    page.get_by_role("textbox", name="username").fill(test_failed_user)
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill(test_failed_user + test_email)
    page.get_by_role("textbox", name="password", exact=True).click()
    page.get_by_role("textbox", name="password", exact=True).fill(test_password)
    page.get_by_role("textbox", name="confirm password").click()
    page.get_by_role("textbox", name="confirm password").fill(test_password)
    page.get_by_role("checkbox", name="I accept the terms and").check()
    page.get_by_role("button", name="Sign Up").click()
    expect(
        page.get_by_text("Username can only contain lowercase letters,")
    ).to_be_visible()


def test_account_creation(page: Page):
    page.goto("/")
    page.get_by_role("link", name="Sign-up").click()
    page.get_by_role("textbox", name="username").click()
    page.get_by_role("textbox", name="username").fill(test_user)
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill(test_email)
    page.get_by_role("textbox", name="password", exact=True).click()
    page.get_by_role("textbox", name="password", exact=True).fill(test_password)
    page.get_by_role("textbox", name="confirm password").click()
    page.get_by_role("textbox", name="confirm password").fill(test_password)
    page.get_by_role("checkbox", name="I accept the terms and").check()
    page.get_by_role("button", name="Sign Up").click()
    expect(page.get_by_text(f"Dear {test_user}, please go to")).to_be_visible()

    found = "false"
    with psycopg.connect(
        f"dbname={db_name} user={db_user} host={db_host} password={db_password}"
    ) as conn:
        # Open a cursor to perform database operations
        with conn.cursor() as cur:
            # Execute a command: this creates a new table
            cur.execute("SELECT username FROM profiles_user;")
            for row in cur:
                logger.debug(row[0])
                if row[0] == test_user:
                    assert row[0] == test_user
                    found = "true"
                    break
            if found != "true":
                assert 0, "Username not found in database"


def activate_account():
    with psycopg.connect(
        f"dbname={db_name} user={db_user} host={db_host} password={db_password}"
    ) as conn:
        # Open a cursor to perform database operations
        with conn.cursor() as cur:
            # Execute a command: this creates a new table
            cur.execute(
                f"UPDATE profiles_user SET is_active = 't' WHERE username = '{test_user}';"
            )
            cur.execute(
                f"SELECT is_active FROM profiles_user WHERE username = '{test_user}';"
            )
            for row in cur:
                logger.debug(str(row))
                if str(row) not in "(True,)":
                    assert 0, "Activation unsuccesful"


def test_loginIntoActivatedAccount(page: Page):
    activate_account()
    page.goto("/")
    page.get_by_role("link", name="Login").click()
    page.get_by_role("textbox", name="username or email").click()
    page.get_by_role("textbox", name="username or email").fill(test_user)
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill(test_password)
    page.get_by_role("button", name="Log In").click()
    expect(page.get_by_text(test_user)).to_be_visible()
