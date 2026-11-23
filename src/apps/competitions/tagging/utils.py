from django.utils.html import strip_tags

ALLOWED_PAGE_TITLES = {"overview", "description", "tasks", "evaluation", "competition", "participation"}


def build_competition_text(competition=None, title="", description="", pages=None):
    """Aggregate title, description, and relevant pages into plain text."""
    if competition is not None:
        title = title or competition.title or ""
        description = description or competition.description or ""
        if pages is None:
            pages = competition.pages.all()

    parts = [p for p in (title, description) if p]
    for page in pages or ():
        page_title = (page.get("title") if isinstance(page, dict) else page.title) or ""
        page_content = (page.get("content") if isinstance(page, dict) else page.content) or ""
        if page_content and any(k in page_title.lower() for k in ALLOWED_PAGE_TITLES):
            parts.append(page_content)

    return strip_tags("\n".join(parts))
