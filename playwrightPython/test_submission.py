from playwright.sync_api import expect, Page
import toml
import pytest

data = toml.load("config/config.toml")


# This allows us to autologin with a cookie in all tests instead of having to login each time
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """  """
    browser_context_args.update(storage_state="config/state.json",)
    return browser_context_args


def wait_for_finished(page, time_out):
    try:
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=time_out)
        return True
    except:
        return False


def test_submission_basic(page: Page) -> None:
    page.set_default_timeout(300000)
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)
    

def test_submission_irisV15_code(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition_15_iris.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission_15_iris_code.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)


def test_submission_irisV15_result(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition_15_iris.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission_15_iris_result.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)


def test_submission_v15(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition_15.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission_15.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)


def test_submission_v18(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition_18.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission_18.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)


def test_submission_v2_multiTaskFactSheet(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition_v2_multi_task_fact_sheet.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    page.locator("input[name=\"text\"]").click()
    page.locator("input[name=\"text\"]").fill("test")
    page.locator("input[name=\"text_required\"]").click()
    page.locator("input[name=\"text_required\"]").fill("test")
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)


def test_submission_v2_multiTask(page: Page) -> None:
    page.goto("http://localhost/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/competitions/competition_v2_multi_task.zip")
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission.zip")
    expect(page.locator('.ui.indicating')).to_be_visible()
    expect(page.locator('.ui.indicating')).not_to_be_visible()
    # Reload the page until the finished status is visible or the count is reached
    count = 0
    while not wait_for_finished(page, 5000) and count < 5:
        page.reload()
        count += 1
    expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=1)