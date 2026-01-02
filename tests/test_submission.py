from playwright.sync_api import expect, Page
import toml
import pytest
import re
import os
from loguru import logger

if os.environ.get("CI", "false").lower() == "true":
    ci = True
else:
    ci = False

data = toml.load("config/config.toml")


# This allows us to autologin with a cookie in all tests instead of having to login each time
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    browser_context_args.update(
        storage_state="config/state.json",
    )
    return browser_context_args


def run_tests(page, competition, submission) -> None:
    page.goto("/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files(competition)
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files(submission)
    expect(page.locator(".ui.indicating")).to_be_visible()
    expect(page.locator(".ui.indicating")).not_to_be_visible()
    # Wait for Finished to show. If it does not, catch the error and reload the page in case the page didn't update automatically
    try:
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=25000)
    except:
        page.reload()
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=2000)
    # Add to leaderboard and see if shows
    text = page.locator(".submission_row").first.inner_text()
    submission_Id = text.split(None, 1)
    try:
        page.locator("td:nth-child(6) > span > .icon").first.click(timeout=300)
    except:
        page.locator("td:nth-child(7) > span > .icon").first.click(timeout=300)
    page.locator("div").filter(has_text=re.compile(r"^Results$")).click()
    expect(
        page.locator("#leaderboardTable").get_by_role(
            "link", name=data["default_user"]["username"]
        )
    ).to_be_visible()
    expect(page.get_by_role("cell", name=submission_Id[0], exact=True)).to_be_visible()


def test_basic(page: Page):
    run_tests(
        page,
        competition="test_files/competitions/competition.zip",
        submission="test_files/submissions/submission.zip",
    )


def test_v15(page: Page):
    run_tests(
        page,
        competition="test_files/competitions/competition_15.zip",
        submission="test_files/submissions/submission_15.zip",
    )


def test_irisV15_code(page: Page):
    run_tests(
        page,
        competition="test_files/competitions/competition_15_iris.zip",
        submission="test_files/submissions/submission_15_iris_code.zip",
    )


def test_irisV15_result(page: Page):
    run_tests(
        page,
        competition="test_files/competitions/competition_15_iris.zip",
        submission="test_files/submissions/submission_15_iris_result.zip",
    )


def test_v18(page: Page):
    run_tests(
        page,
        competition="test_files/competitions/competition_18.zip",
        submission="test_files/submissions/submission_18.zip",
    )


# Skip this test if in the CI
@pytest.mark.skipif(ci, reason="Works locally but fails in the CI because of CELERY_TASK_ALWAYS_EAGER = True")
def test_v2_multiTask(page: Page) -> None:
    page.goto("/")
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
    expect(page.locator(".ui.indicating")).to_be_visible()
    expect(page.locator(".ui.indicating")).not_to_be_visible()
    # Wait for Finished to show. If it does not, catch the error and reload the page in case the page didn't update automatically
    try:
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=35000)
    except:
        page.reload()
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=2000)
    # Add to leaderboard and see if shows
    text = page.locator(".submission_row").first.inner_text()
    submission_Id = text.split(None, 1)
    try:
        page.locator("td:nth-child(6) > span > .icon").first.click(timeout=300)
    except:
        page.locator("td:nth-child(7) > span > .icon").first.click(timeout=300)
    page.locator("div").filter(has_text=re.compile(r"^Results$")).click()
    expect(
        page.locator("#leaderboardTable").get_by_role(
            "link", name=data["default_user"]["username"]
        )
    ).to_be_visible()
    # The ID on the leaderboard can be one of the children instead of the parent so we try them all
    found = False
    for count in range(0, 5):
        try:
            submission_ID_str = int(submission_Id[0]) + count
            logger.info("Looked for ID : " + str(submission_ID_str))
            expect(
                page.get_by_role("cell", name=str(submission_ID_str), exact=True)
            ).to_be_visible()
            found = True
            break
        except:
            pass
    if not found:
        assert 0, "Submission not found in the leaderboard"


# Skip this test if in the CI
@pytest.mark.skipif(ci, reason="Works locally but fails in the CI because of CELERY_TASK_ALWAYS_EAGER = True")
def test_v2_multiTaskFactSheet(page: Page) -> None:
    page.goto("/")
    page.get_by_role("link", name=" Benchmarks/Competitions").click()
    page.get_by_role("link", name=" Upload").click()
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files(
        "test_files/competitions/competition_v2_multi_task_fact_sheet.zip"
    )
    page.get_by_role("link", name="View").click()
    page.get_by_text("My Submissions").click()
    page.locator('input[name="text"]').click()
    page.locator('input[name="text"]').fill("test")
    page.locator('input[name="text_required"]').click()
    page.locator('input[name="text_required"]').fill("test")
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="").click()
    file_chooser = fc_info.value
    file_chooser.set_files("test_files/submissions/submission.zip")
    expect(page.locator(".ui.indicating")).to_be_visible()
    expect(page.locator(".ui.indicating")).not_to_be_visible()
    # Wait for Finished to show. If it does not, catch the error and reload the page in case the page didn't update automatically
    try:
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=35000)
    except:
        page.reload()
        expect(page.get_by_role("cell", name="Finished")).to_be_visible(timeout=2000)
    # Add to leaderboard and see if shows
    text = page.locator(".submission_row").first.inner_text()
    submission_Id = text.split(None, 1)
    try:
        page.locator("td:nth-child(6) > span > .icon").first.click(timeout=300)
    except:
        page.locator("td:nth-child(7) > span > .icon").first.click(timeout=300)
    page.locator("div").filter(has_text=re.compile(r"^Results$")).click()
    expect(
        page.locator("#leaderboardTable").get_by_role(
            "link", name=data["default_user"]["username"]
        )
    ).to_be_visible()
    # The ID on the leaderboard can be one of the children instead of the parent so we try them all
    found = False
    for count in range(0, 5):
        try:
            submission_ID_str = int(submission_Id[0]) + count
            logger.debug("Looked for ID : " + str(submission_ID_str))
            expect(
                page.get_by_role("cell", name=str(submission_ID_str), exact=True)
            ).to_be_visible()
            found = True
            break
        except:
            pass
    if not found:
        assert 0, "Submission not found in the leaderboard"
