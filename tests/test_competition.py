from playwright.sync_api import expect, Page
import toml
import pytest
import random

data = toml.load("config/config.toml")

titleNum = random.randint(0, 1000)


# This allows us to autologin with a cookie in all tests instead of having to login each time
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """ """
    browser_context_args.update(
        storage_state="config/state.json",
    )
    return browser_context_args


def test_competition_upload(page: Page):
    page.goto("/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition.zip")
    expect(page.get_by_text("Competition created!")).to_be_visible()


def task_creation(page):
    page.goto("/")
    page.get_by_text("codabench Admin management").click()
    page.get_by_role("link", name=" Resources").click()
    page.get_by_text("Datasets and programs").first.click()
    page.get_by_role("button", name=" Add Dataset/Program").click()
    page.get_by_role("textbox", name="Name").click()
    page.get_by_role("textbox", name="Name").fill(
        str(titleNum) + "Playwright Scoring Program"
    )
    page.get_by_role("textbox", name="Description").click()
    page.get_by_role("textbox", name="Description").fill("Test Dataset Description")
    page.locator(".ui.form > div > .ui").click()
    page.get_by_text("Scoring Program", exact=True).nth(5).click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/Task/Scoring Program/scoring_program.zip")
    page.get_by_role("button", name=" Upload").click()
    page.get_by_text("Tasks", exact=True).click()
    page.get_by_text("Create Task").first.click()
    page.get_by_role("textbox", name="Name", exact=True).click()
    page.get_by_role("textbox", name="Name", exact=True).fill(
        str(titleNum) + "Playwright Task"
    )
    page.get_by_role("textbox", name="Description").click()
    page.get_by_role("textbox", name="Description").fill("Test Descirption Task")
    page.get_by_text("Datasets and programs").nth(3).click()
    page.locator("#scoring_program").click()
    page.locator("#scoring_program").fill("test")
    page.locator("a").filter(
        has_text=str(titleNum) + "Playwright Scoring Program"
    ).click()
    page.get_by_text("Create", exact=True).click()


def test_manual_competition_creation(page: Page):
    task_creation(page)
    page.goto("/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Create").click()
    page.get_by_role("textbox").nth(1).click()
    page.get_by_role("textbox").nth(1).fill("Test Title")
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competition/test_logo.png")
    page.locator(".CodeMirror-scroll").first.click()
    page.get_by_role("application").get_by_role("textbox").fill("Test Description ")
    page.get_by_role("textbox", name="Example: $1000 for the top").click()
    page.get_by_role("textbox", name="Example: $1000 for the top").fill("1000€")
    page.get_by_role("textbox", name="Example: email@example.com").click()
    page.get_by_role("textbox", name="Example: email@example.com").fill(
        "organizer@email.com"
    )
    page.get_by_text("Auto-run submissions").click()
    page.get_by_text("Enable Competition Forum").click()
    page.get_by_text("Make Programs Available").click()
    page.get_by_text("Make Input Data Available").click()
    page.get_by_role("textbox", name="Example: codalab/codalab-").click()
    page.get_by_role("textbox", name="Example: codalab/codalab-").fill(
        "codalab/codalab-legacy:py37"
    )
    page.get_by_text("Participation").click()
    page.locator("pre").nth(3).click()
    page.get_by_role("application").filter(has_text="|||xxxxxxxxxx 101:").get_by_role(
        "textbox"
    ).fill("Test Terms")
    page.locator('input[name="registration_auto_approve"]').check()
    page.locator("a").filter(has_text="Pages").click()
    page.get_by_role("button", name=" Add page").click()
    page.get_by_role("textbox").nth(1).fill("Test Title")
    page.locator(
        "div:nth-child(2) > .EasyMDEContainer > .CodeMirror > .CodeMirror-scroll"
    ).click()
    page.get_by_role("application").get_by_role("textbox").fill("Test Content")
    page.get_by_text("Save").nth(1).click()
    page.locator("a").filter(has_text="Phases").click()
    page.get_by_role("button", name=" Add phase").click()
    page.locator('input[name="name"]').click()
    page.locator('input[name="name"]').fill(str(titleNum) + "Playwright Task")
    page.locator('input[name="start_date"]').click()
    page.get_by_role("cell", name="12").first.click()
    page.locator('input[name="start_time"]').click()
    page.get_by_role("cell", name="10:").click()
    page.get_by_role("cell", name=":00").click()
    page.locator('input[name="end_date"]').click()
    page.locator('input[name="end_date"]').fill("")
    page.locator(
        "div:nth-child(7) > .EasyMDEContainer > .CodeMirror > .CodeMirror-scroll"
    ).click()
    page.locator(
        ".CodeMirror.cm-s-easymde.CodeMirror-wrap.CodeMirror-focused > div > textarea"
    ).fill("This is a phase Test")
    page.locator(".ui.search.selection.dropdown.multiple").first.click()
    page.locator(".ui.search.selection.dropdown.multiple > .search").first.fill(
        str(titleNum) + "Playwright Task"
    )
    page.get_by_text(str(titleNum) + "Playwright Task").nth(1).click()
    page.locator(".title > .dropdown").click()
    page.locator('input[name="execution_time_limit"]').click()
    page.locator('input[name="execution_time_limit"]').fill("100")
    page.locator('input[name="max_submissions_per_day"]').click()
    page.locator('input[name="max_submissions_per_day"]').fill("2")
    page.locator('input[name="max_submissions_per_person"]').click()
    page.locator('input[name="max_submissions_per_person"]').fill("3")
    page.get_by_text("Save").nth(3).click()
    page.get_by_text("Leaderboard", exact=True).click()
    page.get_by_role("button", name=" Add leaderboard").click()
    page.locator('input[name="title"]').click()
    page.locator('input[name="title"]').fill("Test title Leaderboard")
    page.locator('input[name="key"]').click()
    page.locator('input[name="key"]').fill("Test Key")
    page.locator(".ui.plus").click()
    page.locator('input[name="column_key_0"]').click()
    page.locator('input[name="column_key_0"]').fill("Test Key")
    page.locator('input[name="key"]').click()
    page.locator('input[name="key"]').press("ControlOrMeta+a")
    page.locator('input[name="key"]').fill("Key")
    page.locator('input[name="column_key_0"]').click()
    page.get_by_text("Save").nth(4).click()
    page.get_by_role("button", name="Save").click()
    expect(page.get_by_text("Test Content")).to_be_visible()
    expect(page.locator(".reward-container")).to_be_visible()
    expect(page.get_by_text("1000€")).to_be_visible()
    page.get_by_text("Terms", exact=True).click()
    expect(page.get_by_text("Test Terms")).to_be_visible()
    page.get_by_text("Phases").click()
    expect(page.locator("comp-tabs")).to_contain_text(str(titleNum) + "Playwright Task")
    expect(page.get_by_text("This is a phase Test")).to_be_visible()
    page.get_by_text("My Submissions").click()
    expect(page.get_by_text("out of 2")).to_be_visible()
    expect(page.get_by_text("out of 3")).to_be_visible()
    page.get_by_role("link", name="Forum").click()
    expect(page.get_by_role("heading", name="Test Title Forum")).to_be_visible()
