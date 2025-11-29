from pathlib import Path
import httpx

page_url_template = "https://web.archive.org/web/http://www.iicm.org.tw/term/termb_%s.htm"
letters = ['0'] + [chr(i) for i in range(ord('A'), ord('Z') + 1)]

def main():
    dist = Path("iicm-glossary")
    dist.mkdir(exist_ok=True)

    client = httpx.Client(follow_redirects=True)

    for letter in letters:
        # check if we have already downloaded this letter
        if (dist / f"termb_{letter}.htm").exists():
            print(f"Letter {letter} already downloaded, skipping...")
            continue

        page_url = page_url_template % letter
        print(f"Downloading page for letter {letter}...")
        response = client.get(page_url)
        response.raise_for_status()
        html = response.content.decode("big5", errors="replace")

        # save html to file
        with open(dist / f"termb_{letter}.htm", "w", encoding="utf8") as f:
            f.write(html)

if __name__ == "__main__":
    main()
