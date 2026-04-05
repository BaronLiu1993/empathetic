import pytest
from unittest.mock import patch
from service.text_processing import clean_text, strip_html_tags


@pytest.fixture(autouse=True)
def mock_llm():
    """Mock the Gemini LLM call so no API calls are made."""
    with patch("service.text_processing._llm_text_processing", side_effect=lambda text: text):
        yield


class TestStripHtmlTags:
    def test_basic(self):
        assert strip_html_tags("<p>hello</p>") == "hello"

    def test_nested(self):
        assert strip_html_tags("<div><p>hello</p></div>") == "hello"

class TestCleanText:
    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""
        assert clean_text("   ") == ""

    def test_script_style_removal(self):
        html = "<p>content</p><script>alert('xss')</script><style>.x{}</style>"
        result = clean_text(html)
        assert "alert" not in result
        assert ".x{}" not in result
        assert "content" in result

    def test_comment_removal(self):
        html = "<p>visible</p><!-- hidden comment -->"
        result = clean_text(html)
        assert "visible" in result
        assert "hidden comment" not in result

    def test_html_entity_decoding(self):
        html = "<p>rock &amp; roll</p>"
        assert "rock & roll" in clean_text(html)

    def test_nbsp_handling(self):
        html = "<p>hello&nbsp;world</p>"
        result = clean_text(html)
        assert "hello" in result
        assert "world" in result

    def test_boilerplate_removal(self):
        html = """
        <nav><a href="/">Home</a></nav>
        <main><p>Main content here</p></main>
        <footer>Copyright 2024</footer>
        """
        result = clean_text(html)
        assert "Main content here" in result
        assert "Home" not in result
        assert "Copyright" not in result

    def test_boilerplate_class_removal(self):
        html = """
        <div class="sidebar">sidebar stuff</div>
        <div class="content"><p>Real content</p></div>
        """
        result = clean_text(html)
        assert "Real content" in result
        assert "sidebar stuff" not in result

    def test_hidden_elements(self):
        html = """
        <p>visible</p>
        <div style="display: none">hidden</div>
        <span aria-hidden="true">also hidden</span>
        """
        result = clean_text(html)
        assert "visible" in result
        assert "hidden" not in result
        assert "also hidden" not in result

    def test_tracking_pixel_removal(self):
        html = '<p>text</p><img width="1" height="1" src="track.gif">'
        result = clean_text(html)
        assert "text" in result

    def test_block_tags_to_newlines(self):
        html = "<p>first</p><p>second</p>"
        result = clean_text(html)
        assert "first" in result
        assert "second" in result
        assert "\n" in result

    def test_br_to_newline(self):
        html = "<p>line one<br>line two</p>"
        result = clean_text(html)
        assert "line one" in result
        assert "line two" in result

    def test_whitespace_normalization(self):
        html = "<p>  too   many    spaces  </p>"
        result = clean_text(html)
        assert "too many spaces" in result

    def test_excessive_newlines_collapsed(self):
        html = "<p>a</p><p></p><p></p><p></p><p>b</p>"
        result = clean_text(html)
        assert "\n\n\n" not in result
        assert "a" in result
        assert "b" in result

    def test_unicode_normalization(self):
        html = "<p>caf\u0065\u0301</p>"
        result = clean_text(html)
        assert "caf\u00e9" in result

    def test_encoding_fix(self):
        html = "<p>curly \u00e2\u0080\u009cquotes\u00e2\u0080\u009d</p>"
        result = clean_text(html)
        assert "\u201c" in result or "quotes" in result

    def test_real_world_page(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test</title><style>body{margin:0}</style></head>
        <body>
            <nav><ul><li><a href="/">Home</a></li></ul></nav>
            <script>var x = 1;</script>
            <main>
                <article>
                    <h1>Article Title</h1>
                    <p>First paragraph with <b>bold</b> text.</p>
                    <p>Second paragraph.</p>
                </article>
            </main>
            <aside><div class="advertisement">Buy stuff</div></aside>
            <footer><p>Copyright 2024</p></footer>
            <!-- tracking -->
            <img width="1" height="1" src="pixel.gif">
        </body>
        </html>
        """
        result = clean_text(html)
        assert "Article Title" in result
        assert "First paragraph with bold text." in result
        assert "Second paragraph." in result
        assert "var x" not in result
        assert "margin" not in result
        assert "Home" not in result
        assert "Copyright" not in result
        assert "Buy stuff" not in result
        assert "tracking" not in result
