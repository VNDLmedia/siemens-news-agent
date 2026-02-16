"""
Digest endpoints.

- /preview: Returns HTML as it would appear in the email
- /data: Returns raw JSON article data for the digest
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
import locale
import html as html_escape

from security import verify_api_key
from database import get_pool

router = APIRouter(prefix="/api/digest", tags=["Digest"])

# Standard error responses for contract documentation
AUTH_RESPONSES = {
    401: {"description": "Missing API key"},
    403: {"description": "Invalid API key"},
}

def _format_digest_date() -> str:
    """Return date formatted like the digest email header."""
    try:
        locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
        return datetime.now().strftime("%A, %d. %B %Y")
    except Exception:
        try:
            locale.setlocale(locale.LC_TIME, "de_DE")
            return datetime.now().strftime("%A, %d. %B %Y")
        except Exception:
            weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
            months = [
                "",
                "Januar",
                "Februar",
                "März",
                "April",
                "Mai",
                "Juni",
                "Juli",
                "August",
                "September",
                "Oktober",
                "November",
                "Dezember",
            ]
            now = datetime.now()
            return f"{weekdays[now.weekday()]}, {now.day}. {months[now.month]} {now.year}"


def generate_digest_html(articles: list, total_candidates: int = 0, usecase: str = "daily_newsletter") -> str:
    """
    Generate HTML email content from articles.
    
    This replicates the exact HTML generation from the n8n workflow
    to ensure consistent preview with full corporate identity.
    """
    
    date = _format_digest_date()
    
    article_count = len(articles)

    # Priority badge helper function
    def get_priority_badge(priority):
        if priority == "high":
            return '<span style="background: #e74c3c; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; margin-left: 10px;">HIGH</span>'
        elif priority == "medium":
            return '<span style="background: #000028; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; margin-left: 10px;">MEDIUM</span>'
        return ""
    
    # Logo hosted on CDN for email compatibility
    # TODO: Change to internal Siemens CDN after project handover
    logo_url = "https://povlib.b-cdn.net/siemens/sie-logo-petrol-rgb.png"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #66667e; margin: 0; padding: 0; background-color: #f3f3f0; }}
    .wrapper {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .header {{ margin-bottom: 30px; padding-top: 30px; padding-bottom: 30px; border-bottom: 2px solid #009999; }}
    .logo {{ max-width: 200px; height: auto; margin-top: 20px; margin-bottom: 25px; }}
    h1 {{ color: #000028; font-weight: 700; margin: 0; padding-top: 10px; font-size: 1.5em; }}
    .subtitle {{ color: #9999a9; font-size: 0.9em; margin-top: 5px; }}
    .article {{ margin-bottom: 30px; padding: 20px; background: #ebebee; border-left: 4px solid #00c1b6; }}
    .article.high-priority {{ border-left-color: #00c1b6; }}
    .article.medium-priority {{ border-left-color: #00c1b6; }}
    .article h2 {{ margin-top: 0; color: #000028; font-weight: 700; font-size: 1.1em; }}
    .article-meta {{ color: #9999a9; font-size: 0.85em; margin-bottom: 10px; }}
    .summary {{ margin: 15px 0; color: #66667e; }}
    .keywords {{ margin-top: 10px; }}
    .keyword {{ display: inline-block; background: #ccccd4; color: #000028; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; margin-right: 5px; margin-bottom: 5px; }}
    .read-more {{ display: inline-block; margin-top: 10px; color: #00c1b6; text-decoration: none; font-weight: 600; }}
    .read-more:hover {{ text-decoration: underline; }}
    .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccccd4; color: #9999a9; font-size: 0.85em; text-align: center; }}
    .stats {{ background: #000028; color: white; padding: 15px 20px; border-radius: 5px; margin-bottom: 25px; }}
    .stats-item {{ display: inline-block; margin-right: 20px; }}
    .stats-number {{ font-size: 1.5em; font-weight: 700; color: #009999; }}
    .no-articles {{ text-align: center; padding: 40px; color: #9999a9; }}
  </style>
</head>
<body>
  <!--[if mso]>
  <table role="presentation" width="600" align="center" cellpadding="0" cellspacing="0" border="0">
  <tr><td>
  <![endif]-->
  <div class="wrapper" style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <div class="header">
      <img src="{logo_url}" alt="Siemens" class="logo" width="180" style="max-width: 200px; height: auto;">
      <h1 style="color: #000028; font-weight: 700; margin: 0; padding-top: 10px; font-size: 1.5em;">Dein News Digest - {date}</h1>
      <div class="subtitle" style="color: #9999a9; font-size: 0.9em; margin-top: 5px;">KI-kuratierte Auswahl der wichtigsten Nachrichten</div>
    </div>
"""
    
    if article_count == 0:
        html += """
  <div class="no-articles">
    <p>Keine Artikel zum Anzeigen.</p>
    <p>Es gibt aktuell keine ungesendeten Artikel mit Zusammenfassungen.</p>
  </div>
"""
    else:
        # Stats box (matching workflow)
        html += f"""
  <div class="stats">
    <span class="stats-item"><span class="stats-number">{article_count}</span> Artikel ausgewählt</span>
    <span class="stats-item">aus <span class="stats-number">{total_candidates if total_candidates > 0 else article_count}</span> Kandidaten</span>
  </div>
  
  <p>Hier sind deine {article_count} wichtigsten Nachrichten von heute, intelligent kuratiert für maximale Relevanz und Vielfalt:</p>
"""
        
        for article in articles:
            # Format published date
            published_date = "Datum unbekannt"
            if article.get("published_at"):
                try:
                    pub_dt = article["published_at"]
                    if hasattr(pub_dt, "strftime"):
                        published_date = pub_dt.strftime("%d.%m.%Y")
                    elif isinstance(pub_dt, str):
                        # Try to parse ISO format
                        try:
                            dt = datetime.fromisoformat(pub_dt.replace('Z', '+00:00'))
                            published_date = dt.strftime("%d.%m.%Y")
                        except:
                            published_date = pub_dt[:10] if len(pub_dt) >= 10 else pub_dt
                    else:
                        published_date = str(pub_dt)[:10]
                except:
                    pass
            
            title = html_escape.escape(article.get("title") or "Kein Titel")
            source = html_escape.escape(article.get("source") or "Unbekannte Quelle")
            summary = html_escape.escape(article.get("summary") or "Keine Zusammenfassung verfügbar")
            url = html_escape.escape(article.get("url") or "#")
            priority = (article.get("priority") or "").lower()
            category = html_escape.escape(article.get("category") or "")
            
            # Priority class for border color
            priority_class = ""
            if priority == "high":
                priority_class = "high-priority"
            elif priority == "medium":
                priority_class = "medium-priority"
            
            # Build keywords/topics display (max 5 tags)
            keywords_html = ""
            topics = article.get("topics") or []
            keywords = article.get("keywords") or []
            all_tags = (topics + keywords)[:5]
            if all_tags:
                tags_html = "".join([f'<span class="keyword">{html_escape.escape(str(tag))}</span>' for tag in all_tags])
                keywords_html = f'<div class="keywords">{tags_html}</div>'
            
            # Priority badge
            priority_badge = get_priority_badge(priority)
            
            # Category in meta
            category_str = f" | {category}" if category else ""
            
            html += f"""
  <div class="article {priority_class}">
    <h2>{title}{priority_badge}</h2>
    <div class="article-meta">
      {published_date} | {source}{category_str}
    </div>
    <div class="summary">
      {summary}
    </div>
    {keywords_html}
    <a href="{url}" class="read-more" style="color: #00c1b6 !important; text-decoration: none !important; font-weight: 600;" target="_blank">Weiterlesen →</a>
  </div>
"""

    html += """
    <div class="footer" style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccccd4; color: #9999a9; font-size: 0.85em; text-align: center;">
      <p>Dieser Digest wurde automatisch von deinem AI News Agent generiert.</p>
    </div>
  </div>
  <!--[if mso]>
  </td></tr>
  </table>
  <![endif]-->
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
            SELECT id, url, title, content, source, source_type, published_at, 
                   summary, priority, topics, keywords, category, fetched_at, sent
            FROM articles 
            WHERE processed = TRUE 
            ORDER BY fetched_at DESC
        """
        count_query = """
            SELECT COUNT(*) as total FROM articles WHERE processed = TRUE
        """
    else:
        # Only unsent articles (what would actually be emailed)
        query = """
            SELECT id, url, title, content, source, source_type, published_at, 
                   summary, priority, topics, keywords, category, fetched_at, sent
            FROM articles 
            WHERE processed = TRUE AND sent = FALSE 
            ORDER BY fetched_at DESC
        """
        count_query = """
            SELECT COUNT(*) as total FROM articles WHERE processed = TRUE AND sent = FALSE
        """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)
        count_row = await conn.fetchrow(count_query)
    
    articles = [dict(row) for row in rows]
    total_candidates = count_row["total"] if count_row else len(articles)
    html = generate_digest_html(articles, total_candidates=total_candidates)
    
    return HTMLResponse(content=html)


# Request/response models for shared digest rendering (single source of truth)
class DigestRenderRequest(BaseModel):
    """Payload for rendering digest HTML from a specific curated article set."""

    articles: List[dict[str, Any]] = Field(default_factory=list)
    total_candidates: int = 0
    usecase: str = "daily_newsletter"
    recipient_emails: List[str] = Field(default_factory=list)


class DigestRenderResponse(BaseModel):
    """Rendered digest payload used by n8n email sending."""

    html_content: str
    article_count: int
    article_ids: List[str]
    recipient_emails: List[str]
    recipient_count: int
    subject: str


@router.post(
    "/render",
    response_model=DigestRenderResponse,
    responses={**AUTH_RESPONSES},
    summary="Render Digest HTML",
    description=(
        "Render digest HTML for a provided article list. "
        "Used by n8n send workflow and serves as single source of truth "
        "for digest email generation."
    ),
)
async def render_digest(
    payload: DigestRenderRequest,
    api_key: str = Depends(verify_api_key),
):
    """Render digest email from curated items and return HTML + metadata."""
    # Normalize article IDs to strings for downstream SQL update in n8n.
    article_ids = [str(a.get("id")) for a in payload.articles if a.get("id")]
    article_count = len(payload.articles)
    html = generate_digest_html(
        payload.articles,
        total_candidates=payload.total_candidates if payload.total_candidates > 0 else article_count,
        usecase=payload.usecase,
    )
    date = _format_digest_date()

    return DigestRenderResponse(
        html_content=html,
        article_count=article_count,
        article_ids=article_ids,
        recipient_emails=payload.recipient_emails,
        recipient_count=len(payload.recipient_emails),
        subject=f"News Digest - {date} ({article_count} kuratierte Artikel)",
    )


# Response model for digest data
class DigestArticle(BaseModel):
    """Article data as it appears in the digest."""
    id: str
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    summary: Optional[str] = None
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
                   summary, sent
            FROM articles 
            WHERE processed = TRUE 
            ORDER BY fetched_at DESC
        """
    else:
        query = """
            SELECT id, url, title, source, published_at, 
                   summary, sent
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
