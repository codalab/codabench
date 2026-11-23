from django.utils.html import strip_tags

ALLOWED_PAGE_TITLES = ("overview", "description", "tasks", "competition", "evaluation", "participation")
MAX_TEXT_LENGTH = 4000


def build_competition_text(competition=None, title="", description="", pages=None):
    """Aggregate title, description, and prioritized pages into plain text up to MAX_TEXT_LENGTH."""
    if competition is not None:
        title = title or competition.title or ""
        description = description or competition.description or ""
        if pages is None:
            pages = competition.pages.all()

    parts = [strip_tags(p).strip() for p in (title, description) if p]
    length = sum(len(p) for p in parts)

    if length < MAX_TEXT_LENGTH and pages:
        extracted = [
            (
                ((p.get("title") if isinstance(p, dict) else p.title) or "").lower(),
                strip_tags((p.get("content") if isinstance(p, dict) else p.content) or "").strip(),
            )
            for p in pages
        ]
        used = set()
        for keyword in ALLOWED_PAGE_TITLES:
            for idx, (page_title, content) in enumerate(extracted):
                if idx not in used and content and keyword in page_title:
                    used.add(idx)
                    parts.append(content)
                    length += len(content)
                    if length >= MAX_TEXT_LENGTH:
                        break
            if length >= MAX_TEXT_LENGTH:
                break

    return "\n".join(parts)[:MAX_TEXT_LENGTH]
