import re
import unicodedata

import ftfy
from bs4 import BeautifulSoup, Comment
from google import genai
from dotenv import load_dotenv

load_dotenv()

REMOVE_TAGS = {"script", "style", "noscript", "svg", "head", "iframe"}
BOILERPLATE_TAGS = {"nav", "footer", "header", "aside"}
BOILERPLATE_PATTERNS = re.compile(
    r"sidebar|menu|advert|cookie|popup|banner|promo|newsletter|social",
    re.IGNORECASE,
)

BLOCK_TAGS = {
    "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "article", "section", "main", "ul", "ol", "table", "tr",
}

def get_gemini_client():
    client = genai.Client()
    return client

def strip_html_tags(text):
    stripped_html = BeautifulSoup(text, "html.parser").get_text()
    return stripped_html.strip()


def _fix_encoding(raw_html):
    return ftfy.fix_text(raw_html)


def _remove_non_content(soup):
    for tag in soup.find_all(REMOVE_TAGS):
        tag.decompose()

    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()


def _remove_hidden(soup):
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")):
        tag.decompose()

    for tag in soup.find_all(attrs={"aria-hidden": "true"}):
        tag.decompose()

    for tag in soup.find_all("img"):
        width = tag.get("width", "")
        height = tag.get("height", "")
        if str(width) in ("0", "1") and str(height) in ("0", "1"):
            tag.decompose()


def _remove_boilerplate(soup):
    for tag in soup.find_all(BOILERPLATE_TAGS):
        tag.decompose()

    for tag in soup.find_all(True):
        if tag.attrs is None:
            continue
        classes = " ".join(tag.get("class", []))
        tag_id = tag.get("id", "")
        if BOILERPLATE_PATTERNS.search(classes) or BOILERPLATE_PATTERNS.search(tag_id):
            tag.decompose()


def _convert_structure(soup):
    for br in soup.find_all("br"):
        br.replace_with("\n")

    for li in soup.find_all("li"):
        li.insert_before("\n")

    for tag in soup.find_all(BLOCK_TAGS):
        tag.insert_before("\n\n")
        tag.insert_after("\n\n")

    for td in soup.find_all(["td", "th"]):
        td.insert_after(" ")


def _normalize_whitespace(text):
    text = re.sub(r"[^\S\n]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def _llm_text_processing(text):
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""
                You are a text extraction assistant. Given the following raw text scraped from a webpage, extract only the main article content.
                Remove all of the following:
                - Advertisements and promotional content
                - Navigation menus and footers
                - Cookie notices and popups
                - Sidebar content and related links
                - Any other boilerplate text

                Return the cleaned main content as the original paragraph. Preserve the original structure with headings and paragraphs. Do not add any commentary or explanation — output only the extracted content.

                ```
                {text}
                ```
        """
    )
    return response.text

def clean_text(raw_html):
    if not raw_html or not raw_html.strip():
        return ""

    fixed = _fix_encoding(raw_html)
    soup = BeautifulSoup(fixed, "lxml")

    _remove_non_content(soup)
    _remove_hidden(soup)
    _remove_boilerplate(soup)
    _convert_structure(soup)

    text = soup.get_text()
    text = unicodedata.normalize("NFC", text)
    text = _normalize_whitespace(text)
    text = _llm_text_processing(text)

    return text