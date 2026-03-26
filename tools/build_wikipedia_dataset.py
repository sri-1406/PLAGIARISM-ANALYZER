import requests
import json
import time

# Topics (normal names, no underscores needed)
TOPICS = [
    "Artificial intelligence",
    "Machine learning",
    "Deep learning",
    "Cloud computing",
    "Data science",
    "Neural network",
    "Computer vision",
    "Natural language processing",
    "Blockchain",
    "Computer security"
]

OUTPUT_FILE = "documents.json"


def fetch_wikipedia_content(title):
    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": title
    }

    # 🔥 IMPORTANT: Add User-Agent header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, params=params, headers=headers)

        # Debug status
        print(f"Status for '{title}': {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Failed: {title}")
            return None

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page_id in pages:
            page = pages[page_id]

            content = page.get("extract")

            if not content:
                print(f"⚠️ No content: {title}")
                return None

            return {
                "title": title,
                "content": content,
                "source_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "source_type": "wikipedia"
            }

    except Exception as e:
        print(f"❌ Error: {title} -> {e}")
        return None


def build_dataset():
    dataset = []
    doc_id = 1

    for topic in TOPICS:
        print(f"\n🔍 Fetching: {topic}")

        article = fetch_wikipedia_content(topic)

        if article:
            dataset.append({
                "id": doc_id,
                "title": article["title"],
                "content": article["content"],
                "source_url": article["source_url"],
                "source_type": article["source_type"]
            })
            doc_id += 1

        time.sleep(1)  # avoid rate limiting

    # Save dataset
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Dataset saved to {OUTPUT_FILE} with {len(dataset)} articles.")


if __name__ == "__main__":
    build_dataset()