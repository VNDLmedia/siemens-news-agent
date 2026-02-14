"""
Digest endpoints.

- /preview: Returns HTML as it would appear in the email
- /data: Returns raw JSON article data for the digest
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from security import verify_api_key
from database import get_pool

router = APIRouter(prefix="/api/digest", tags=["Digest"])

# Standard error responses for contract documentation
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}


def generate_digest_html(articles: list, include_sent: bool = False) -> str:
    """
    Generate HTML email content from articles.
    
    This replicates the exact HTML generation from the n8n workflow
    to ensure consistent preview.
    """
    # Format date in German
    try:
        date = datetime.now().strftime("%A, %d. %B %Y")
    except:
        date = datetime.now().strftime("%Y-%m-%d")
    
    article_count = len(articles)
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
    h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
    .article {{ margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-left: 4px solid #3498db; }}
    .article h2 {{ margin-top: 0; color: #2c3e50; }}
    .article-meta {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }}
    .summary {{ margin: 15px 0; }}
    .summary-short {{ font-weight: bold; color: #34495e; margin-bottom: 10px; }}
    .summary-long {{ color: #555; }}
    .read-more {{ display: inline-block; margin-top: 10px; color: #3498db; text-decoration: none; }}
    .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.85em; text-align: center; }}
    .preview-banner {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px 20px; margin-bottom: 20px; border-radius: 4px; }}
    .preview-banner strong {{ color: #856404; }}
    .no-articles {{ text-align: center; padding: 40px; color: #7f8c8d; }}
  </style>
</head>
<body>
  <div class="preview-banner">
    <strong>📧 Preview Mode</strong> - This is how the email digest would look.
    {"(Including already sent articles)" if include_sent else "(Only unsent articles)"}
  </div>
  <h1>📰 Dein News Digest - {date}</h1>
"""

    if article_count == 0:
        html += """
  <div class="no-articles">
    <p>Keine Artikel zum Anzeigen.</p>
    <p>Es gibt aktuell keine ungesendeten Artikel mit Zusammenfassungen.</p>
  </div>
"""
    else:
        html += f"  <p>Hier sind deine {article_count} wichtigsten Nachrichten von heute:</p>\n"
        
        for article in articles:
            published_date = "Datum unbekannt"
            if article.get("published_at"):
                try:
                    pub_dt = article["published_at"]
                    if hasattr(pub_dt, "strftime"):
                        published_date = pub_dt.strftime("%d.%m.%Y")
                    else:
                        published_date = str(pub_dt)[:10]
                except:
                    pass
            
            title = article.get("title", "Kein Titel")
            source = article.get("source", "Unbekannte Quelle")
            summary_short = article.get("summary_short") or "Keine Kurzzusammenfassung verfügbar"
            summary_long = article.get("summary_long") or "Keine ausführliche Zusammenfassung verfügbar"
            url = article.get("url", "#")
            
            html += f"""
  <div class="article">
    <h2>{title}</h2>
    <div class="article-meta">
      📅 {published_date} | 📰 {source}
    </div>
    <div class="summary">
      <div class="summary-short">⚡ {summary_short}</div>
      <div class="summary-long">{summary_long}</div>
    </div>
    <a href="{url}" class="read-more" target="_blank">→ Weiterlesen</a>
  </div>
"""

    html += """
  <div class="footer">
    <p>Dieser Digest wurde automatisch von deinem News AI Agent generiert.</p>
    <p>Powered by n8n + OpenAI</p>
  </div>
</body>
</html>
"""
    return html


@router.get(
    "/preview",
    response_class=HTMLResponse,
    responses={**AUTH_RESPONSES},
    summary="Preview Email Digest",
    description="""Returns the HTML content that would be sent via email digest.

**Query Parameters:**
- `include_sent=false` (default): Only show unsent articles
- `include_sent=true`: Include already sent articles

This is useful for:
- Testing the email template
- Previewing content before sending
- Debugging digest generation
"""
)
async def preview_digest(
    include_sent: bool = Query(
        default=False,
        description="Include articles that were already sent"
    ),
    api_key: str = Depends(verify_api_key)
):
    """Generate and return the digest HTML without sending email."""
    pool = await get_pool()
    
    if include_sent:
        # All processed articles
        query = """
            SELECT id, url, title, content, source, published_at, 
                   summary_short, summary_long, fetched_at, sent
            FROM articles 
            WHERE processed = TRUE 
            ORDER BY fetched_at DESC
        """
    else:
        # Only unsent articles (what would actually be emailed)
        query = """
            SELECT id, url, title, content, source, published_at, 
                   summary_short, summary_long, fetched_at, sent
            FROM articles 
            WHERE processed = TRUE AND sent = FALSE 
            ORDER BY fetched_at DESC
        """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    
    articles = [dict(row) for row in rows]
    html = generate_digest_html(articles, include_sent)
    
    return HTMLResponse(content=html)


# Response model for digest data
class DigestArticle(BaseModel):
    """Article data as it appears in the digest."""
    id: str
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    summary_short: Optional[str] = None
    summary_long: Optional[str] = None
    sent: bool

    class Config:
        from_attributes = True


class DigestDataResponse(BaseModel):
    """Response for digest data endpoint."""
    article_count: int
    include_sent: bool
    generated_at: str
    articles: List[DigestArticle]


@router.get(
    "/data",
    response_model=DigestDataResponse,
    responses={**AUTH_RESPONSES},
    summary="Get Digest Data",
    description="""Returns the raw JSON data for articles that would be included in the digest.

**Query Parameters:**
- `include_sent=false` (default): Only unsent articles
- `include_sent=true`: Include already sent articles

This is useful for:
- Building custom digest templates
- Integration with other systems
- Data analysis
"""
)
async def get_digest_data(
    include_sent: bool = Query(
        default=False,
        description="Include articles that were already sent"
    ),
    api_key: str = Depends(verify_api_key)
):
    """Return raw article data for the digest."""
    pool = await get_pool()
    
    if include_sent:
        query = """
            SELECT id, url, title, source, published_at, 
                   summary_short, summary_long, sent
            FROM articles 
            WHERE processed = TRUE 
            ORDER BY fetched_at DESC
        """
    else:
        query = """
            SELECT id, url, title, source, published_at, 
                   summary_short, summary_long, sent
            FROM articles 
            WHERE processed = TRUE AND sent = FALSE 
            ORDER BY fetched_at DESC
        """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
    
    articles = []
    for row in rows:
        article = dict(row)
        # Convert UUID and datetime to strings
        article["id"] = str(article["id"])
        if article.get("published_at"):
            article["published_at"] = article["published_at"].isoformat()
        articles.append(DigestArticle(**article))
    
    return DigestDataResponse(
        article_count=len(articles),
        include_sent=include_sent,
        generated_at=datetime.now().isoformat(),
        articles=articles
    )
