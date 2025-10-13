import requests
from bs4 import BeautifulSoup
import pandas as pd

def crawl_discussions(keywords: list[str], limit: int = 20) -> pd.DataFrame:
    """Tìm kiếm bài viết / bình luận về các keyword."""
    data = []
    for kw in keywords:
        query = f"https://www.google.com/search?q={kw}+thảo+luận+dự+thảo+luật+khoa+học+công+nghệ+và+đổi+mới+sáng+tạo"
        res = requests.get(query, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        for g in soup.select("div.g"):
            link = g.find("a", href=True)
            title = g.get_text(" ", strip=True)
            if link:
                data.append({"keyword": kw, "title": title[:150], "url": link["href"]})
            if len(data) >= limit:
                break
    return pd.DataFrame(data)
