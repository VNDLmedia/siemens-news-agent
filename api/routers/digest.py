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
    
    # Siemens logo SVG as base64 data URI
    logo_base64 = "data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iaXNvLTg4NTktMSI/Pg0KPCEtLSBHZW5lcmF0b3I6IEFkb2JlIElsbHVzdHJhdG9yIDE2LjAuNCwgU1ZHIEV4cG9ydCBQbHVnLUluIC4gU1ZHIFZlcnNpb246IDYuMDAgQnVpbGQgMCkgIC0tPg0KPCFET0NUWVBFIHN2ZyBQVUJMSUMgIi0vL1czQy8vRFREIFNWRyAxLjEvL0VOIiAiaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkIj4NCjxzdmcgdmVyc2lvbj0iMS4xIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB4PSIwcHgiIHk9IjBweCIgd2lkdGg9IjEwMDBweCINCgkgaGVpZ2h0PSIxNTlweCIgdmlld0JveD0iMCAwIDEwMDAgMTU5IiBzdHlsZT0iZW5hYmxlLWJhY2tncm91bmQ6bmV3IDAgMCAxMDAwIDE1OTsiIHhtbDpzcGFjZT0icHJlc2VydmUiPg0KPGcgaWQ9IkJvdW5kaW5nQm94Ij4NCgk8cG9seWdvbiBzdHlsZT0iZmlsbDpub25lOyIgcG9pbnRzPSIwLDE1OSAxMDAwLDE1OSAxMDAwLDAgMCwwIDAsMCAJIi8+DQo8L2c+DQo8ZyBpZD0iU0lFTUVOUyI+DQoJPGc+DQoJCTxwYXRoIHN0eWxlPSJmaWxsLXJ1bGU6ZXZlbm9kZDtjbGlwLXJ1bGU6ZXZlbm9kZDtmaWxsOiMwMDk5OTk7IiBkPSJNMy4wODYsMTUyLjUzN1YxMjIuNDYNCgkJCWMxNy4xMTksNS4zODgsMzIuMjY3LDguMDgyLDQ1LjQ0NCw4LjA4MmMxOC4xOTMsMCwyNy4yOTEtNC44MDksMjcuMjkxLTE0LjQyYzAtMy41ODMtMS4zMjQtNi41OTQtMy45NzgtOS4wMzINCgkJCWMtMi43MTQtMi41ODYtOS42NjUtNi4xNzEtMjAuODM1LTEwLjc2NGMtMjAuMDQyLTguMjQxLTMzLjExMS0xNS4yNjktMzkuMTktMjEuMDgyQzMuOTM5LDY3LjU3MSwwLDU3Ljg5NSwwLDQ2LjIwMg0KCQkJQzAsMzEuMTQ0LDUuNzQsMTkuNjY3LDE3LjIxMiwxMS43OEMyOC41NTcsMy45NjIsNDMuMzMsMC4wNTcsNjEuNTU0LDAuMDU3YzEwLjA0MSwwLDI0LjU3NCwxLjg0OCw0My41ODMsNS41NDl2MjguOTMzDQoJCQljLTE0LjE0NC01LjY1LTI3LjI3My04LjQ2OS0zOS40MDMtOC40NjljLTE3LjA4MSwwLTI1LjYyMSw0LjY5LTI1LjYyMSwxNC4wOTFjMCwzLjUxNCwxLjcyLDYuMzgsNS4xNjUsOC42MDINCgkJCWMyLjg2NSwxLjc5OCwxMC43NTksNS41OTYsMjMuNjY1LDExLjQwNmMxOC41ODMsOC4yNTMsMzAuOTU0LDE1LjQyNywzNy4xMTgsMjEuNTI5YzcuMzE0LDcuMjM4LDEwLjk3OCwxNi42MDQsMTAuOTc4LDI4LjA4NA0KCQkJYzAsMTYuNTAxLTcuMTc3LDI5LjA4OC0yMS41MjEsMzcuNzYxYy0xMS42MjEsNy4wMzMtMjYuNjksMTAuNTM1LTQ1LjE5OCwxMC41MzVDMzQuNjksMTU4LjA3OCwxOC45NDIsMTU2LjIzNywzLjA4NiwxNTIuNTM3DQoJCQlMMy4wODYsMTUyLjUzN3oiLz4NCgkJPHBvbHlnb24gc3R5bGU9ImZpbGwtcnVsZTpldmVub2RkO2NsaXAtcnVsZTpldmVub2RkO2ZpbGw6IzAwOTk5OTsiIHBvaW50cz0iMTQxLjA2MywyLjcwNCAxNDEuMDYzLDIuNzA0IDE4My42MDMsMi43MDQgDQoJCQkxODMuNjAzLDE1NS4wMDEgMTQxLjA2MywxNTUuMDAxIAkJIi8+DQoJCTxwb2x5Z29uIHN0eWxlPSJmaWxsLXJ1bGU6ZXZlbm9kZDtjbGlwLXJ1bGU6ZXZlbm9kZDtmaWxsOiMwMDk5OTk7IiBwb2ludHM9IjIyMi42MTYsMTU1LjAwMSAyMjIuNjE2LDIuNzA0IDMzMS43MjEsMi43MDQgDQoJCQkzMzEuNzIxLDMwLjI1IDI2My42MTYsMzAuMjUgMjYzLjYxNiw2NC42MzkgMzIyLjg5OCw2NC42MzkgMzIyLjg5OCw4OS43NjUgMjYzLjYxNiw4OS43NjUgMjYzLjYxNiwxMjUuOTA2IDMzMy40NzYsMTI1LjkwNiANCgkJCTMzMy40NzYsMTU1LjAwMSAyMjIuNjE2LDE1NS4wMDEgCQkiLz4NCgkJPHBvbHlnb24gc3R5bGU9ImZpbGwtcnVsZTpldmVub2RkO2NsaXAtcnVsZTpldmVub2RkO2ZpbGw6IzAwOTk5OTsiIHBvaW50cz0iMzYxLjI0NywxNTUuMDAxIDM2MS4yNDcsMi43MDQgNDE2LjQwMiwyLjcwNCANCgkJCTQ1NC43MjEsMTAwLjAxNSA0OTQuMDAxLDIuNzA0IDU0Ni4zOSwyLjcwNCA1NDYuMzksMTU1LjAwMSA1MDYuMDU2LDE1NS4wMDEgNTA2LjA1Niw0Ny4xNzEgNDYxLjM5MiwxNTYuNTQ3IDQzNS4wMjMsMTU2LjU0NyANCgkJCTM5MS4yMTksNDcuMTcxIDM5MS4yMTksMTU1LjAwMSAzNjEuMjQ3LDE1NS4wMDEgCQkiLz4NCgkJPHBvbHlnb24gc3R5bGU9ImZpbGwtcnVsZTpldmVub2RkO2NsaXAtcnVsZTpldmVub2RkO2ZpbGw6IzAwOTk5OTsiIHBvaW50cz0iNTg1LjQxMSwxNTUuMDAxIDU4NS40MTEsMi43MDQgNjk0LjUxNCwyLjcwNCANCgkJCTY5NC41MTQsMzAuMjUgNjI2LjQxNSwzMC4yNSA2MjYuNDE1LDY0LjYzOSA2ODUuNjk1LDY0LjYzOSA2ODUuNjk1LDg5Ljc2NSA2MjYuNDE1LDg5Ljc2NSA2MjYuNDE1LDEyNS45MDYgNjk2LjI4LDEyNS45MDYgDQoJCQk2OTYuMjgsMTU1LjAwMSA1ODUuNDExLDE1NS4wMDEgCQkiLz4NCgkJPHBvbHlnb24gc3R5bGU9ImZpbGwtcnVsZTpldmVub2RkO2NsaXAtcnVsZTpldmVub2RkO2ZpbGw6IzAwOTk5OTsiIHBvaW50cz0iNzI0LjI3MSwxNTUuMDAxIDcyNC4yNzEsMi43MDQgNzczLjU3NSwyLjcwNCANCgkJCTgyNS44ODMsMTA0LjY1NSA4MjUuODgzLDIuNzA0IDg1NS44NDcsMi43MDQgODU1Ljg0NywxNTUuMDAxIDgwNy45NDMsMTU1LjAwMSA3NTQuMjQ3LDUxLjY3OCA3NTQuMjQ3LDE1NS4wMDEgNzI0LjI3MSwxNTUuMDAxIAkJDQoJCQkiLz4NCgkJPHBhdGggc3R5bGU9ImZpbGwtcnVsZTpldmVub2RkO2NsaXAtcnVsZTpldmVub2RkO2ZpbGw6IzAwOTk5OTsiIGQ9Ik04ODYuMDQ3LDE1Mi41MzdWMTIyLjQ2DQoJCQljMTYuOTc0LDUuMzg4LDMyLjEyLDguMDgyLDQ1LjQ1Miw4LjA4MmMxOC4xOTUsMCwyNy4yODItNC44MDksMjcuMjgyLTE0LjQyYzAtMy41ODMtMS4yODktNi41OTQtMy44NTQtOS4wMzINCgkJCWMtMi43MjgtMi41ODYtOS43MDgtNi4xNzEtMjAuOTQ1LTEwLjc2NGMtMTkuOTgyLTguMTczLTMzLjA2NC0xNS4xOTgtMzkuMTk5LTIxLjA4MmMtNy44NzUtNy42MDUtMTEuODA3LTE3LjMxNy0xMS44MDctMjkuMTQ2DQoJCQljMC0xNC45OTMsNS43MjYtMjYuNDMyLDE3LjIxLTM0LjMxOWMxMS4zMjgtNy44MTgsMjYuMTE4LTExLjcyMyw0NC4zNDQtMTEuNzIzYzEwLjI0NywwLDIzLjUyNSwxLjYyNywzOS44MSw0Ljg5NmwzLjc2MSwwLjY1Mw0KCQkJdjI4LjkzM2MtMTQuMTQ2LTUuNjUtMjcuMzEzLTguNDY5LTM5LjUwOC04LjQ2OWMtMTcuMDE2LDAtMjUuNTAzLDQuNjktMjUuNTAzLDE0LjA5MWMwLDMuNTE0LDEuNzExLDYuMzgsNS4xNDcsOC42MDINCgkJCWMyLjczLDEuNzI5LDEwLjY1Niw1LjUyOSwyMy43NzgsMTEuNDA2YzE4LjQ0Miw4LjI1MywzMC43ODcsMTUuNDI3LDM3LjAwNSwyMS41MjljNy4zMjUsNy4yMzgsMTAuOTgsMTYuNjA0LDEwLjk4LDI4LjA4NA0KCQkJYzAsMTYuNTAxLTcuMTM1LDI5LjA4OC0yMS40MDYsMzcuNzYxYy0xMS42ODksNy4wMzMtMjYuNzk2LDEwLjUzNS00NS4zMDEsMTAuNTM1DQoJCQlDOTE3LjY0NiwxNTguMDc4LDkwMS44OTEsMTU2LjIzNyw4ODYuMDQ3LDE1Mi41MzdMODg2LjA0NywxNTIuNTM3eiIvPg0KCTwvZz4NCjwvZz4NCjwvc3ZnPg0K"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: Arial, Helvetica, sans-serif; line-height: 1.6; color: #66667e; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f3f3f0; }}
    .header {{ margin-bottom: 30px; padding-top: 30px; padding-bottom: 30px; border-bottom: 2px solid #009999; }}
    .logo {{ max-width: 200px; height: auto; margin-top: 20px; margin-bottom: 25px; }}
    h1 {{ color: #000028; font-weight: 700; margin: 0; padding-top: 10px; font-size: 1.5em; }}
    .article {{ margin-bottom: 30px; padding: 20px; background: #ebebee; border-left: 4px solid #009999; }}
    .article h2 {{ margin-top: 0; color: #000028; font-weight: 700; }}
    .article-meta {{ color: #9999a9; font-size: 0.9em; margin-bottom: 10px; }}
    .summary {{ margin: 15px 0; }}
    .summary-short {{ font-weight: 700; color: #000028; margin-bottom: 10px; }}
    .summary-long {{ color: #66667e; }}
    .read-more {{ display: inline-block; margin-top: 10px; color: #009999; text-decoration: none; font-weight: 600; }}
    .read-more:hover {{ color: #00c1b6; }}
    .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccccd4; color: #9999a9; font-size: 0.85em; text-align: center; }}
    .no-articles {{ text-align: center; padding: 40px; color: #9999a9; }}
  </style>
</head>
<body>
  <div class="header">
    <img src="{logo_base64}" alt="Siemens" class="logo">
    <h1>Dein News Digest - {date}</h1>
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
      {published_date} | {source}
    </div>
    <div class="summary">
      <div class="summary-short">{summary_short}</div>
      <div class="summary-long">{summary_long}</div>
    </div>
    <a href="{url}" class="read-more" target="_blank">Weiterlesen</a>
  </div>
"""

    html += """
  <div class="footer">
    <p>Dieser Digest wurde automatisch von deinem News AI Agent generiert.</p>
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
