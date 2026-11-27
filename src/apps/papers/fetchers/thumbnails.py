import io
import logging
from urllib.parse import urlparse

import pypdfium2 as pdfium
import requests
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

USER_AGENT = "Codabench/1.0 (https://www.codabench.org)"
REQUEST_TIMEOUT = 15  # seconds
MAX_PDF_BYTES = 15 * 1024 * 1024  # cap downloads to avoid exhausting worker memory
THUMBNAIL_WIDTH = 240  # px (2x Retina for ~120-140px card thumbnails)


def generate_pdf_thumbnail(pdf_url):
    """Download an open-access PDF and render its first page to a WebP thumbnail."""
    if not pdf_url or urlparse(pdf_url).scheme not in ('http', 'https'):
        return None

    try:
        with requests.get(pdf_url, headers={'User-Agent': USER_AGENT}, stream=True, timeout=REQUEST_TIMEOUT) as resp:
            resp.raise_for_status()
            chunks = []
            total = 0
            for chunk in resp.iter_content(chunk_size=65536):
                total += len(chunk)
                if total > MAX_PDF_BYTES:
                    return None
                chunks.append(chunk)
            pdf_bytes = b''.join(chunks)
    except requests.RequestException as exc:
        logger.warning(f"Failed to download PDF {pdf_url}: {exc}")
        return None

    # Publishers often return an HTML paywall/login page with 200 OK
    if not pdf_bytes.startswith(b'%PDF'):
        return None

    # Render page 1 only at target width, then encode to WebP
    try:
        doc = pdfium.PdfDocument(pdf_bytes)
        try:
            page = doc[0]
            width_pt, _ = page.get_size()
            pil_img = page.render(scale=THUMBNAIL_WIDTH / width_pt).to_pil()
        finally:
            doc.close()
    except (pdfium.PdfiumError, IndexError) as exc:
        logger.warning(f"Failed to render PDF {pdf_url}: {exc}")
        return None

    buf = io.BytesIO()
    pil_img.save(buf, format='WEBP', quality=82)
    return ContentFile(buf.getvalue())
