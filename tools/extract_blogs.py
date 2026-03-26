import os
import json
import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "blogs", "documents.json")

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ✅ Step 1: Get real blog URLs from Dev.to API
def fetch_blog_urls():
    api_url = "https://dev.to/api/articles?per_page=5"

    try:
        response = requests.get(api_url, headers=HEADERS)
        data = response.json()

        urls = [article["url"] for article in data]
        return urls

    except Exception as e:
        print(f"❌ API Error: {e}")
        return []


# ✅ Step 2: Extract content from each blog
def extract_article(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"❌ Status {response.status_code}: {url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string.strip() if soup.title else "No Title"

        # Dev.to main content
        article_body = soup.find("div", {"class": "crayons-article__body"})

        if not article_body:
            print(f"⚠️ No content found: {url}")
            return None

        paragraphs = article_body.find_all("p")
        content = " ".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

        if len(content) < 300:
            print(f"⚠️ Weak content skipped: {url}")
            return None

        return {
            "title": title,
            "content": content,
            "source": url
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    data = {"documents": []}

    urls = fetch_blog_urls()

    if not urls:
        print("❌ No URLs fetched")
        return

    for i, url in enumerate(urls, start=1):
        print(f"📥 Fetching: {url}")
        article = extract_article(url)

        if article:
            article["id"] = i
            data["documents"].append(article)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Blogs saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()