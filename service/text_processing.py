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
        contents=f"""You are a text extraction assistant. Given the following raw text scraped from a webpage, extract only the main article content.
Remove all of the following:
- Advertisements and promotional content
- Navigation menus and footers
- Cookie notices and popups
- Sidebar content and related links
- Any other boilerplate text

Return the cleaned main content as the original paragraph. Preserve the original structure with headings and paragraphs. Do not add any commentary or explanation — output only the extracted content.

<input>
{text}
</input>"""
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

test = """
<body data-site-id="bi" data-id="elon-musk-xai-cofounder-exits-spacex-ipo-2026-4" class="" data-cm-theme="old">

  

  
    
    <div class="breaking-news component-loaded" data-component-type="breaking-news" data-load-strategy="disable-lazy" data-url="/ajax/breaking-news" style="--scroll-duration: 5s"></div>

  
    <header class="masthead" data-component-type="masthead" data-load-strategy="exclude" style="--scroll: 0; --main-height: 73px; --dropdown-height: 49px; --masthead-bottom: 0px;">
      <section class="top-section full-width-section">
        
        
        
        <div class="masthead-ad as-post-page is-tall is-disabled" data-component-type="masthead-ad" data-load-strategy="exclude" data-ad-subnav="" data-ad-refresher-expand="" data-can-stick="5000" data-hide-when="[data-is-interscroller]">
          <div class="masthead-ad-wrapper">
              
              
              <div data-bi-ad="" id="gpt-post-tech-sub_nav-desktop-1" class="ad ad-wrapper fluid only-desktop is-collapsible height-250" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/sub-nav/tech" data-region="sub-nav" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[3,1],[320,50],[300,50]]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[320,50],[3,1]]},{&quot;browserLimit&quot;:[970,0],&quot;slotSize&quot;:[[970,250],[970,90],[728,90],[3,1]]}]" data-tile-order="tile-0" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/sub-nav/tech&quot;,&quot;region&quot;:&quot;sub-nav&quot;,&quot;dvp_spos&quot;:&quot;sub-nav&quot;}" data-not-lazy="" data-disable-super-zoomer="true" data-enable-ad-refresher="true" data-refresh-count="1" data-ad-adjusted="" data-loaded-method="non-lazy" data-flow="doubleverify.success,amazon.success,rubicon.success,gam.requested" data-google-query-id="CMDkvIzz1JMDFdkGpAYdfdgHIg" data-ad-refresher-config="{&quot;isEmpty&quot;:false,&quot;curSize&quot;:[970,250],&quot;region&quot;:&quot;sub-nav&quot;}" data-viewable="true" data-timer="19"><div id="google_ads_iframe_/4442842/businessinsider.desktop/post/sub-nav/tech_0__container__" style="border: 0pt none;"><iframe id="google_ads_iframe_/4442842/businessinsider.desktop/post/sub-nav/tech_0" name="google_ads_iframe_/4442842/businessinsider.desktop/post/sub-nav/tech_0" title="3rd party ad content" width="970" height="250" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" aria-label="Advertisement" tabindex="0" allow="private-state-token-redemption;attribution-reporting" data-load-complete="true" data-google-container-id="1" style="border: 0px; vertical-align: bottom; width: 970px; height: 250px;"></iframe></div></div>
            <div class="close-icon-wrapper" aria-label="Close this ad">
              <div class="close-icon-circle"><svg class="svg-icon close-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
          <path fill="currentColor" d="M21 5.394 18.606 3 12 9.606 5.394 3 3 5.394 9.606 12 3 18.606 5.394 21 12 14.394 18.606 21 21 18.606 14.394 12 21 5.394Z"></path>
        </svg></div>
            </div>
          </div>
        </div>
      </section>
    
      <section class="main-section grid-lines masthead-animation main-animated ">
    
        <a href="/" class="logo-link masthead-animation logo-animated" data-track-click="{&quot;product_field&quot;:&quot;logo&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;masthead&quot;,&quot;click_text&quot;:&quot;Business Insider&quot;}">
          <svg class="svg-icon logo-inline " xmlns="http://www.w3.org/2000/svg" width="1365" height="120" viewBox="0 0 1365 120">
            <title>Business Insider</title>
          
            <g class="logo-inline-path" fill="#0a0a0a" fill-rule="evenodd">
              <path d="M0 2.46h49.1c27.31 0 41.59 14.12 41.59 31.46 0 11.97-6.75 20.1-16.11 24.4v.31c11.97 4.3 18.72 13.81 18.72 25.93 0 17.34-13.35 32.53-42.2 32.53H0V2.46Zm47.57 45.42c8.13 0 11.82-4.14 11.82-8.75s-3.68-8.9-11.82-8.9H33.15v17.65h14.42Zm.46 41.43c8.59 0 12.74-4.14 12.74-9.51s-4.3-9.51-12.58-9.51H33.15v19.03h14.88Zm52.32-18.87V2.46h33.45v67.67c0 12.74 6.29 19.49 17.03 19.49s17.49-6.75 17.49-19.64V2.46h33.61v67.98c0 28.85-19.33 49.57-51.1 49.57s-50.49-20.72-50.49-49.57ZM287.1 7.98v29.46c-7.21-5.06-19.49-8.59-29.46-8.59-9.05 0-13.66 2.92-13.66 6.75s5.06 5.83 14.12 9.05c15.35 5.37 36.21 12.58 36.21 36.98 0 21.79-16.42 37.9-45.27 37.9-14.88 0-28.54-4.3-36.98-9.97v-31c8.29 6.75 20.87 12.12 32.99 12.12 10.28 0 15.04-3.84 15.04-8.13 0-5.52-7.83-7.98-17.19-11.36-12.28-4.45-31.76-12.43-31.76-34.68 0-20.1 15.81-36.52 44.04-36.52 12.43 0 23.63 3.22 31.92 7.98Zm15.8-5.52h33.45v114.63H302.9V2.46Zm152.38 114.63h-31.92l-41.28-61.53h-.15v61.53h-31.76V2.46h31.92l41.28 60.46h.15V2.46h31.76v114.63ZM469.09 2.46h79.18v29.77h-45.73v13.81h41.12v27.01h-41.12v14.27h45.73v29.77h-79.18V2.46Zm163.12 5.52v29.46c-7.21-5.06-19.49-8.59-29.46-8.59-9.05 0-13.66 2.92-13.66 6.75s5.06 5.83 14.12 9.05c15.35 5.37 36.21 12.58 36.21 36.98 0 21.79-16.42 37.9-45.27 37.9-14.88 0-28.54-4.3-36.98-9.97v-31c8.29 6.75 20.87 12.12 32.99 12.12 10.28 0 15.04-3.84 15.04-8.13 0-5.52-7.83-7.98-17.19-11.36-12.28-4.45-31.76-12.43-31.76-34.68 0-20.1 15.81-36.52 44.04-36.52 12.43 0 23.63 3.22 31.92 7.98Zm88.54 0v29.46c-7.21-5.06-19.49-8.59-29.46-8.59-9.05 0-13.66 2.92-13.66 6.75s5.06 5.83 14.12 9.05c15.35 5.37 36.21 12.58 36.21 36.98 0 21.79-16.42 37.9-45.27 37.9-14.88 0-28.54-4.3-36.98-9.97v-31c8.29 6.75 20.87 12.12 32.99 12.12 10.28 0 15.04-3.84 15.04-8.13 0-5.52-7.83-7.98-17.19-11.36-12.28-4.45-31.76-12.43-31.76-34.68 0-20.1 15.81-36.52 44.04-36.52 12.43 0 23.63 3.22 31.92 7.98Zm45.97 109.33h33.45V2.69h-33.45v114.63ZM919.08 2.69h-31.76v60.46h-.15L845.89 2.69h-31.92v114.63h31.76V55.79h.15l41.28 61.53h31.92V2.69ZM972.92.23c-28.24 0-44.04 16.42-44.04 36.52 0 22.25 19.49 30.23 31.76 34.68 9.36 3.38 17.19 5.83 17.19 11.36 0 4.3-4.76 8.13-15.04 8.13-12.12 0-24.71-5.37-32.99-12.12v31c8.44 5.68 22.1 9.97 36.98 9.97 28.85 0 45.27-16.11 45.27-37.9 0-24.4-20.87-31.61-36.21-36.98-9.05-3.22-14.12-5.06-14.12-9.05s4.6-6.75 13.66-6.75c9.97 0 22.25 3.53 29.46 8.59V8.21C996.55 3.45 985.35.23 972.92.23Zm46.94 117.08h33.45V2.69h-33.45v114.63Zm80.71-30.23h6.45c17.34 0 28.54-9.82 28.54-27.01s-11.2-27.16-28.54-27.16h-6.45v54.17Zm68.75-27.01c0 34.53-26.09 57.24-63.53 57.24h-38.67V2.69h38.67c37.44 0 63.53 22.86 63.53 57.39Zm9.07 57.24h79.18V87.54h-45.73V73.27h41.12V46.26h-41.12V32.45h45.73V2.69h-79.18v114.63Zm131.83-60.46c8.44 0 15.04-3.99 15.04-11.97s-6.6-11.97-15.19-11.97h-7.06v23.94h7.21Zm54.78 60.46h-39.44l-21.79-35.45h-.77v35.45h-33.45V2.69h40.82c28.7 0 48.64 12.74 48.64 39.9 0 10.74-4.76 26.39-23.79 34.37l29.77 40.36Z"></path>
            </g>
          </svg></a>
        
          <div class="cta-wrapper">
        
              <a class="label-md-strong subscribe-link hide-if-subscribed" href="https://www.businessinsider.com/subscription" data-track-click="{&quot;product_field&quot;:&quot;subscribe&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;masthead&quot;}">
                <svg class="svg-icon brand-arrow-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
          <path fill="currentColor" d="M3 3v5.252h8.631L3 16.883V21h4.117l8.63-8.631V21H21V3H3Z"></path>
        </svg> Subscribe
              </a>
              <a class="label-md-strong newsletters-link" href="https://www.businessinsider.com/subscription/newsletter" data-track-click="{&quot;product_field&quot;:&quot;newsletters&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;masthead&quot;}">
                Newsletters
              </a>
        
              <button class="menu-button" title="Open menu" data-menu-toggle="" data-interaction-trigger="hamburger-menu,account-icon,my-insider,ai-search-box" data-interaction-click-trigger="hamburger-menu" data-track-click="{&quot;product_field&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;masthead&quot;,&quot;click_text&quot;:&quot;bi_value_unassigned&quot;,&quot;click_path&quot;:&quot;bi_value_unassigned&quot;}">
                <svg class="svg-icon menu-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-hidden="true">
                  <path fill="currentColor" stroke="currentColor" d="M2.5 5.5h19v1.414h-19V5.5Zm0 5.793h19v1.414h-19v-1.414Zm0 7.207v-1.414h19V18.5h-19Z"></path>
                </svg>      </button>
          </div>
    
      </section>
    
    
        <section class="dropdown-section grid-lines">
          
        <div class="series-dropdown component-loaded" data-component-type="series-dropdown" data-load-strategy="lazy" data-track-view="{&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;dropdown&quot;,&quot;event&quot;:&quot;module_in_view&quot;,&quot;element_name&quot;:&quot;edit_series_recirc&quot;}">
          <header class="series-dropdown-header">
            <div class="series-dropdown-stamp">
              
              
              <div class="stamp as-packaged-content">
                  <a href="https://www.businessinsider.com/inside-business" data-track-click="{&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;edit_series&quot;,&quot;product_field&quot;:&quot;inside_business&quot;}">
                  <span class="label headline-semibold">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
                <g>
                  <path d="M9.10407 1.83073L2.31716 3.95695V10.2111L1.20691 10.5595V3.0645L9.10407 0.591309V1.83073Z" fill="currentColor"></path>
                  <path fill-rule="evenodd" clip-rule="evenodd" d="M12.7931 10.9352L5.19735 13.3138L4.89593 13.4085V5.91327L12.7931 3.44001V10.9352ZM6.10252 6.78109V11.7842L11.5861 10.0669V5.06341L6.10252 6.78109Z" fill="currentColor"></path>
                  <path d="M10.9385 3.26204L9.73156 3.64014V3.63872L4.24819 5.35666V5.35761L4.17182 5.38165V11.6292L3.0413 11.9838V4.48874L10.9385 2.01554V3.26204Z" fill="currentColor"></path>
                </g>
                <defs>
                  <clipPath id="clip0_285_1472">
                  <rect width="14" height="14" fill="white"></rect>
                  </clipPath>
                </defs>
              </svg>
                    Inside Business
                  </span>
                </a></div>
        
            </div>
        
            <div class="series-dropdown-options">
                <div class="series-dropdown-description body-xs-subtle">The inner workings of companies shaping our world today.</div>
            </div>
        
            <button class="series-dropdown-more label-md js-toggle" aria-expanded="false" aria-controls="series-dropdown" data-track-click="{&quot;click_path&quot;:&quot;bi_value_unassigned&quot;,&quot;click_text&quot;:&quot;More stories&quot;,&quot;product_field&quot;:&quot;inside_business&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;edit_series_recirc&quot;}">More stories <svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
          <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
        </svg></button>
          </header>
          <section class="series-dropdown-dropdown js-dropdown" id="series-dropdown" inert="" aria-hidden="true">
              <div class="series-dropdown-description body-xs-subtle">The inner workings of companies shaping our world today.</div>
        
            <div class="series-dropdown-posts" data-track-click-shared="{&quot;product_field&quot;:&quot;dropdown&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;element_name&quot;:&quot;edit_series_recirc&quot;}">
                
                
                
                <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal with-ungrouped-text" data-post-id="vibe-coding-side-hustle-creativity-2026-4">
                 
                    
                      <a class="tout-image" href="/vibe-coding-side-hustle-creativity-2026-4" aria-label="Everyone now has the keys to the side hustle kingdom. Now comes the great leveler: Creativity." data-track-click="{&quot;index&quot;:1}" tabindex="-1">        <div class="lazy-holder">
                          
                          
                          <img class="lazy-image js-rendered" src="https://i.insider.com/69ce9cf6e762ed6cfe449ac1?width=600&amp;format=jpeg&amp;auto=webp" data-content-type="image/jpeg" data-srcs="{&quot;https://i.insider.com/69ce9d12c02a678bd7e47627&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:1024,&quot;aspectRatioH&quot;:512},&quot;https://i.insider.com/69ce9cf6e762ed6cfe449ac1&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:1024,&quot;aspectRatioH&quot;:768}}" alt="Priscilla, Tina, and Priyanshi Bansal with their vibe-coded apps.">
                          
                          <noscript>
                              <img class="no-script" src="https://i.insider.com/69ce9d12c02a678bd7e47627?width=600&format=jpeg&auto=webp" />
                          </noscript>
                          
                          </div>    </a>
                  
                
                
                    <h3 class="tout-title font-weight-garnett-500">
                      <a class="tout-title-link" href="/vibe-coding-side-hustle-creativity-2026-4" data-track-click="{&quot;index&quot;:1}">Everyone now has the keys to the side hustle kingdom. Now comes the great leveler: Creativity.</a>
                    </h3>
                
                
                
                </article>        
                
                
                <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal with-ungrouped-text" data-post-id="claude-code-leak-what-happened-recreated-python-features-revealed-2026-4">
                 
                    
                      <a class="tout-image" href="/claude-code-leak-what-happened-recreated-python-features-revealed-2026-4" aria-label="A 4 a.m. scramble turned Anthropic's leak into a 'workflow revelation'" data-track-click="{&quot;index&quot;:2}" tabindex="-1">        <div class="lazy-holder">
                          
                          
                          <img class="lazy-image js-rendered" src="https://i.insider.com/69cd89d26a864f6fcd7bc883?width=600&amp;format=jpeg&amp;auto=webp" data-content-type="image/jpeg" data-srcs="{&quot;https://i.insider.com/69cd89e5c02a678bd7e4724c&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:2000,&quot;aspectRatioH&quot;:1000},&quot;https://i.insider.com/69cd89d26a864f6fcd7bc883&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:2000,&quot;aspectRatioH&quot;:1500}}" alt="Dario Amodei">
                          
                          <noscript>
                              <img class="no-script" src="https://i.insider.com/69cd89e5c02a678bd7e4724c?width=600&format=jpeg&auto=webp" />
                          </noscript>
                          
                          </div>    </a>
                  
                
                
                    <h3 class="tout-title font-weight-garnett-500">
                      <a class="tout-title-link" href="/claude-code-leak-what-happened-recreated-python-features-revealed-2026-4" data-track-click="{&quot;index&quot;:2}">A 4 a.m. scramble turned Anthropic's leak into a 'workflow revelation'</a>
                    </h3>
                
                
                
                </article>        
                
                
                <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal with-ungrouped-text" data-post-id="meta-google-jpmorgan-make-ai-performance-reviews-goals-raises-promotions-2026-3">
                 
                    
                      <a class="tout-image" href="/meta-google-jpmorgan-make-ai-performance-reviews-goals-raises-promotions-2026-3" aria-label="Big companies are turning AI into a scoreboard — and everyone's being ranked" data-track-click="{&quot;index&quot;:3}" tabindex="-1">        <div class="lazy-holder">
                          
                          
                          <img class="lazy-image js-rendered" src="https://i.insider.com/69cc2ad16a864f6fcd7bc15d?width=600&amp;format=jpeg&amp;auto=webp" data-content-type="image/jpeg" data-srcs="{&quot;https://i.insider.com/69cc2adce762ed6cfe448fe1&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:5700,&quot;aspectRatioH&quot;:2850},&quot;https://i.insider.com/69cc2ad16a864f6fcd7bc15d&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:5067,&quot;aspectRatioH&quot;:3800}}" alt="Person at a computer seen from behind">
                          
                          <noscript>
                              <img class="no-script" src="https://i.insider.com/69cc2adce762ed6cfe448fe1?width=600&format=jpeg&auto=webp" />
                          </noscript>
                          
                          </div>    </a>
                  
                
                
                    <h3 class="tout-title font-weight-garnett-500">
                      <a class="tout-title-link" href="/meta-google-jpmorgan-make-ai-performance-reviews-goals-raises-promotions-2026-3" data-track-click="{&quot;index&quot;:3}">Big companies are turning AI into a scoreboard — and everyone's being ranked</a>
                    </h3>
                
                
                
                </article>        
                
                
                <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal with-ungrouped-text" data-post-id="oracle-offers-us-workers-up-to-26-weeks-severance-2026-3">
                 
                    
                      <a class="tout-image" href="/oracle-offers-us-workers-up-to-26-weeks-severance-2026-3" aria-label="Here's the severance package Oracle offered laid-off US employees" data-track-click="{&quot;index&quot;:4}" tabindex="-1">        <div class="lazy-holder">
                          
                          
                          <img class="lazy-image js-rendered" src="https://i.insider.com/69cc156de762ed6cfe448ee4?width=600&amp;format=jpeg&amp;auto=webp" data-content-type="image/jpeg" data-srcs="{&quot;https://i.insider.com/69cc157de762ed6cfe448ee5&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:4000,&quot;aspectRatioH&quot;:2000},&quot;https://i.insider.com/69cc156de762ed6cfe448ee4&quot;:{&quot;contentType&quot;:&quot;image/jpeg&quot;,&quot;aspectRatioW&quot;:3556,&quot;aspectRatioH&quot;:2667}}" alt="Clay Magouyrk">
                          
                          <noscript>
                              <img class="no-script" src="https://i.insider.com/69cc157de762ed6cfe448ee5?width=600&format=jpeg&auto=webp" />
                          </noscript>
                          
                          </div>    </a>
                  
                
                
                    <h3 class="tout-title font-weight-garnett-500">
                      <a class="tout-title-link" href="/oracle-offers-us-workers-up-to-26-weeks-severance-2026-3" data-track-click="{&quot;index&quot;:4}">Here's the severance package Oracle offered laid-off US employees</a>
                    </h3>
                
                
                
                </article>    </div>
          </section>
        </div>
        </section>
    
    
      
    
    </header>
    
      
        
        <nav class="component my-insider
          with-banner
           style-loading" data-my-insider="" data-component-type="my-insider" data-require-auth="true" data-load-markup="my-insider/template" data-load-strategy="interaction">
            <div class="my-insider-header"></div>
            <div class="my-insider-nav-and-content"></div>
            
            
        </nav>
    
      
      
      
      <nav class="hamburger-menu" data-component-type="hamburger-menu" data-load-strategy="interaction">
        <section class="hamburger-menu-content">
          <div class="hamburger-menu-top">
            <a class="monogram-tap-target" href="/" title="Business Insider" data-track-click="{&quot;click_text&quot;:&quot;Business Insider&quot;,&quot;product_field&quot;:&quot;other&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;}">
              <svg class="svg-icon logo-monogram " xmlns="http://www.w3.org/2000/svg" width="147.4" height="120" viewBox="0 0 147.4 120">
                <g class="logo-monogram-path" fill="currentColor" fill-rule="evenodd">
                  <path d="M0 0h51.4C80 0 94.9 14.8 94.9 32.9s-7.1 21-16.9 25.5v.3c12.5 4.5 19.6 14.5 19.6 27.2 0 18.2-14 34.1-44.2 34.1H0V0Zm49.8 47.6c8.5 0 12.4-4.3 12.4-9.2s-3.9-9.3-12.4-9.3H34.7v18.5h15.1Zm.5 43.3c9 0 13.3-4.3 13.3-10s-4.5-10-13.2-10H34.7v19.9h15.6ZM112.4 0h35v120h-35V0Z"></path>
                </g>
              </svg>      </a>
            <button class="close-button" title="Close menu" data-menu-toggle="" data-track-click="{&quot;product_field&quot;:&quot;close&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;click_text&quot;:&quot;bi_value_unassigned&quot;,&quot;click_path&quot;:&quot;bi_value_unassigned&quot;}">
              <span class="close-button-background">
                <svg class="svg-icon close-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M21 5.394 18.606 3 12 9.606 5.394 3 3 5.394 9.606 12 3 18.606 5.394 21 12 14.394 18.606 21 21 18.606 14.394 12 21 5.394Z"></path>
                </svg>        </span>
            </button>
          </div>
      
          
          <div class="ai-search-box" data-component-type="ai-search-box" data-load-strategy="interaction" data-tracking-area="hamburger">
            <form class="input-holder" method="get" action="/answers">
              <div class="input-holder-inner">
                <input type="text" class="js-search-input" placeholder="Search Business Insider">
                <button class="inline-button" title="Search BI"><svg class="svg-icon ai-search-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
            <path fill="currentColor" d="M19.475 9.275a8.415 8.415 0 0 1-2.058 6.82L21 20.414 19.064 22l-3.568-4.3a8.53 8.53 0 0 1-4.466 1.253c-4.711 0-8.53-3.795-8.53-8.477C2.5 5.795 6.319 2 11.03 2c.396 0 .786.027 1.167.079l-.549 1.069-2.716 1.395c-.335.173-.6.41-.794.684a5.977 5.977 0 0 0-3.13 5.25c0 3.304 2.697 5.983 6.022 5.983a6.025 6.025 0 0 0 5.298-3.138c.251-.19.468-.441.629-.754l1.395-2.716 1.123-.577Z"></path>
          
            <path fill="#002AFF" d="M14.822 1.346a.2.2 0 0 1 .356 0l1.66 3.23a.2.2 0 0 0 .086.087l3.23 1.66a.2.2 0 0 1 0 .355l-3.23 1.66a.2.2 0 0 0-.087.086l-1.66 3.23a.2.2 0 0 1-.355 0l-1.66-3.23a.2.2 0 0 0-.086-.087l-3.23-1.66a.2.2 0 0 1 0-.355l3.23-1.66a.2.2 0 0 0 .087-.086l1.66-3.23Z"></path>
          </svg></button>
              </div>
              <button class="big-button">Search</button>
            </form>
          </div>
          <section class="hamburger-menu-vertical-lists" data-track-click-shared="{&quot;product_field&quot;:&quot;vertical&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;}">
            
            
            
            
            <div class="accordion level-0" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="0" data-track-click-shared="{&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;product_field&quot;:&quot;vertical&quot;}" data-type="post">
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://www.businessinsider.com/business" data-track-click="">Business</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/strategy" data-track-click="">Strategy</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/economy" data-track-click="">Economy</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/finance" data-track-click="">Finance</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/retail" data-track-click="">Retail</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/advertising" data-track-click="">Advertising</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/careers" data-track-click="">Careers</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/law" data-track-click="">Law</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/media" data-track-click="">Media</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/real-estate" data-track-click="">Real Estate</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/smallbusiness" data-track-click="">Small Business</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/sc/introducing-the-better-work-project-hub" data-track-click="">The Better Work Project</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/personal-finance" data-track-click="">Personal Finance</a>
                              </span>
                      
                          </div>
                      </div>    </div>
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://www.businessinsider.com/tech" data-track-click="">Tech</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/science" data-track-click="">Science</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/artificial-intelligence" data-track-click="">AI</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/enterprise" data-track-click="">Enterprise</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/transportation" data-track-click="">Transportation</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/startups" data-track-click="">Startups</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/innovation" data-track-click="">Innovation</a>
                              </span>
                      
                          </div>
                      </div>    </div>
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://markets.businessinsider.com" data-track-click="">Markets</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://markets.businessinsider.com/stocks" data-track-click="">Stocks</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://markets.businessinsider.com/indices" data-track-click="">Indices</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://markets.businessinsider.com/commodities" data-track-click="">Commodities</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://markets.businessinsider.com/cryptocurrencies" data-track-click="">Crypto</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://markets.businessinsider.com/currencies" data-track-click="">Currencies</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://markets.businessinsider.com/etfs" data-track-click="">ETFs</a>
                              </span>
                      
                          </div>
                      </div>    </div>
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://www.businessinsider.com/lifestyle" data-track-click="">Lifestyle</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/entertainment" data-track-click="">Entertainment</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/culture" data-track-click="">Culture</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/travel" data-track-click="">Travel</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/food" data-track-click="">Food</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/health" data-track-click="">Health</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/education" data-track-click="">Education</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/parenting" data-track-click="">Parenting</a>
                              </span>
                      
                          </div>
                      </div>    </div>
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://www.businessinsider.com/defense" data-track-click="">Military &amp; Defense</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/politics" data-track-click="">Politics</a>
                              </span>
                      
                          </div>
                      </div>    </div>
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://www.businessinsider.com/guides" data-track-click="">Reviews</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/home" data-track-click="">Home</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/kitchen" data-track-click="">Kitchen</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/style" data-track-click="">Style</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/streaming" data-track-click="">Streaming</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/pets" data-track-click="">Pets</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/tech" data-track-click="">Tech</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/deals" data-track-click="">Deals</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/gifts" data-track-click="">Gifts</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="/guides/tickets" data-track-click="">Tickets</a>
                              </span>
                      
                          </div>
                      </div>    </div>
                <div class="accordion-row">
                    <span class="accordion-item headline-medium ">
                        <button class="accordion-button headline-medium" title="Expand menu"><svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
            
                        <a class="accordion-link headline-medium  with-nested-accordion" href="https://www.businessinsider.com/video" data-track-click="">Video</a>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="menu" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/big-business" data-track-click="">Big Business</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/so-expensive" data-track-click="">So Expensive</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/view-from-above" data-track-click="">View From Above</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/small-business" data-track-click="">Small Business</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/authorized-account" data-track-click="">Authorized Account</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/risky-business" data-track-click="">Risky Business</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/boot-camp" data-track-click="">Boot Camp</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/still-standing" data-track-click="">Still Standing</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/how-crime-works" data-track-click="">How Crime Works</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com/show/life-lessons" data-track-click="">Life Lessons</a>
                              </span>
                      
                          </div>
                      </div>    </div>
            </div>    </section>
      
          <section class="hamburger-menu-account-links">
            <a href="/subscription" class="headline-semibold subscribe-link hide-if-subscribed" data-track-click="{&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;product_field&quot;:&quot;other&quot;}">
              <svg class="svg-icon brand-arrow-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                <path fill="currentColor" d="M3 3v5.252h8.631L3 16.883V21h4.117l8.63-8.631V21H21V3H3Z"></path>
              </svg>        Subscribe
            </a>
      
            <div class="account-btn account-icon-component headline-semibold hide-if-logged-out account-btn-logged-in" data-menu-toggle="" data-component-type="account-icon" data-load-strategy="interaction" data-interaction-trigger="my-insider" data-accounts-list-icon="" data-track-click="{&quot;click_text&quot;:&quot;bi_value_unassigned&quot;,&quot;click_path&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;account_button&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;}" title="XAI's cofounder chaos, rebuilding is vintage Elon Musk - Business Insider" style="display: none;">
              
              <div class="account-icon-loader"></div>
                <a class="account-text" role="button">My account</a>
            
            </div>
            <div class="account-btn account-icon-component headline-semibold hide-if-logged-in account-btn-not-logged-in" data-menu-toggle="" data-component-type="account-icon" data-load-strategy="interaction" data-accounts-list-icon="" data-track-click="{&quot;click_text&quot;:&quot;bi_value_unassigned&quot;,&quot;click_path&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;login&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;}" title="Log in">
              
              <div class="account-icon-loader"></div>
                <a class="account-text" role="button">Log in</a>
            
            </div>
            <a href="/subscription/newsletter" class="headline-semibold newsletter-link" data-track-click="{&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;product_field&quot;:&quot;other&quot;}">
              Newsletters
            </a>
      
            
            
            
            
            <div class="accordion level-0" data-component-type="accordion" data-load-strategy="exclude" data-group="editions" data-level="0" data-track-click-shared="{&quot;click_path&quot;:&quot;bi_value_unassigned&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;product_field&quot;:&quot;other&quot;}" data-type="post">
                <div class="accordion-row">
                    <span class="accordion-item headline-medium without-link">
            
                        <button class="accordion-button headline-medium" title="Expand menu">US edition <svg class="svg-icon chevron-down-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m19.44 5.5-7.486 7.72L4.56 5.594 2 8.234 11.954 18.5 22 8.14 19.44 5.5Z"></path>
            </svg></button>
                    </span>
            
                      
                      
                      
                      
                      <div class="accordion level-1" data-component-type="accordion" data-load-strategy="exclude" data-group="editions" data-level="1">
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.de?IR=C" data-track-click="">Deutschland &amp; Österreich</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://businessinsider.es" data-track-click="">España</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.jp" data-track-click="">Japan</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.com.pl/?IR=C" data-track-click="">Polska</a>
                              </span>
                      
                          </div>
                          <div class="accordion-row">
                              <span class="accordion-item headline-medium ">
                      
                                  <a class="accordion-link headline-medium " href="https://www.businessinsider.tw" data-track-click="">TW 全球中文版</a>
                              </span>
                      
                          </div>
                      </div>    </div>
            </div>    </section>
        </section>
      
        <footer class="hamburger-menu-footer">
          <a href="/app" class="app-cta-wrapper" title="Get the Business Insider app" data-track-click="{&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;product_field&quot;:&quot;other&quot;}">
            <div class="logo-wrapper"><svg class="svg-icon app-monogram-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
        <path fill="currentColor" d="M11.068 10.2c0 .401-.315.763-1.009.763H8.83v-1.54h1.23c.694 0 1.009.375 1.009.777ZM11.185 13.747c0 .469-.354.83-1.087.83h-1.27v-1.66h1.284c.706 0 1.073.361 1.073.83Z"></path>
        <path fill="currentColor" fill-rule="evenodd" d="M6 2a4 4 0 0 0-4 4v12a4 4 0 0 0 4 4h12a4 4 0 0 0 4-4V6a4 4 0 0 0-4-4H6Zm4.19 5H6v10h4.36c2.462 0 3.601-1.325 3.601-2.838 0-1.057-.576-1.887-1.597-2.262v-.027c.799-.375 1.375-1.084 1.375-2.128C13.739 8.232 12.52 7 10.19 7Zm7.826 0H15.16v10h2.855V7Z"></path>
      </svg></div>
            <span class="headline-semibold cta-text">Get the app</span>
          </a>
          
          <div class="social-media-follow" data-e2e-name="social-links" data-track-click-shared="{&quot;click_type&quot;:&quot;owned_socials&quot;,&quot;element_name&quot;:&quot;hamburger_menu&quot;,&quot;event&quot;:&quot;outbound_click&quot;}">
              <a class="social-link as-facebook" href="https://www.facebook.com/businessinsider" label="facebook" title="Follow us on Facebook" aria-label="Click to visit us on Facebook" data-track-click="{&quot;click_text&quot;:&quot;facebook&quot;}" data-e2e-name="facebook" target="_blank" rel="noopener nofollow">
                <svg class="svg-icon social-facebook-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Facebook">
                  <path fill="currentColor" d="M22 12.037C22 6.494 17.523 2 12 2S2 6.494 2 12.037c0 4.707 3.229 8.656 7.584 9.741v-6.674H7.522v-3.067h2.062v-1.322c0-3.416 1.54-5 4.882-5 .634 0 1.727.125 2.174.25v2.78a12.807 12.807 0 0 0-1.155-.037c-1.64 0-2.273.623-2.273 2.244v1.085h3.266l-.561 3.067h-2.705V22C18.163 21.4 22 17.168 22 12.037Z"></path>
                </svg>    </a>
              <a class="social-link as-x" href="https://x.com/businessinsider" label="x" title="Follow us on X" aria-label="Click to visit us on X" data-track-click="{&quot;click_text&quot;:&quot;x&quot;}" data-e2e-name="x" target="_blank" rel="noopener nofollow">
                <svg class="svg-icon social-x-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="X">
                  <path fill="currentColor" d="M17.751 3h3.067l-6.7 7.625L22 21h-6.172l-4.833-6.293L5.464 21h-3.07l7.167-8.155L2 3h6.328l4.37 5.752L17.75 3Zm-1.076 16.172h1.7L7.404 4.732H5.58l11.094 14.44Z"></path>
                </svg>    </a>
              <a class="social-link as-linkedin" href="https://www.linkedin.com/company/businessinsider/" label="linkedin" title="Follow us on LinkedIn" aria-label="Click to visit us on LinkedIn" data-track-click="{&quot;click_text&quot;:&quot;linkedin&quot;}" data-e2e-name="linkedin" target="_blank" rel="noopener nofollow">
                <svg class="svg-icon social-linkedin-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="LinkedIn">
                  <path fill="currentColor" fill-rule="evenodd" d="M4 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H4Zm4.339 4.606a1.627 1.627 0 1 1-3.254 0 1.627 1.627 0 0 1 3.254 0Zm-.221 2.867H5.13v9.335h2.988V9.473Zm4.517 0H9.662v9.335h2.943V13.91c0-2.729 3.461-2.982 3.461 0v4.9h2.849v-5.914c0-4.6-5.07-4.43-6.31-2.17l.03-1.252Z"></path></svg>
                    </a>
              <a class="social-link as-youtube" href="https://www.youtube.com/user/businessinsider" label="youtube" title="Follow us on YouTube" aria-label="Click to visit us on YouTube" data-track-click="{&quot;click_text&quot;:&quot;youtube&quot;}" data-e2e-name="youtube" target="_blank" rel="noopener nofollow">
                <svg class="svg-icon social-youtube-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="YouTube">
                  <path fill="currentColor" d="M11.732 5.5c.508.003 1.777.014 3.126.064l.478.019c1.358.06 2.715.16 3.388.333.898.232 1.604.91 1.842 1.77.38 1.364.427 4.026.433 4.67l.001.134v.153c-.007.644-.054 3.307-.434 4.671-.242.862-.947 1.54-1.842 1.77-.673.172-2.03.273-3.388.332l-.478.02c-1.349.05-2.618.06-3.126.063l-.223.001h-.242c-1.074-.006-5.564-.05-6.992-.417-.898-.232-1.603-.91-1.842-1.769-.38-1.364-.427-4.027-.433-4.671v-.286c.006-.645.053-3.307.433-4.672.242-.862.947-1.54 1.842-1.769 1.428-.366 5.918-.41 6.992-.416h.465ZM9.6 9.937v5.125l5.2-2.562-5.2-2.563Z"></path></svg>
                    </a>
              <a class="social-link as-instagram" href="https://www.instagram.com/businessinsider/" label="instagram" title="Follow us on Instagram" aria-label="Click to visit us on Instagram" data-track-click="{&quot;click_text&quot;:&quot;instagram&quot;}" data-e2e-name="instagram" target="_blank" rel="noopener nofollow">
                <svg class="svg-icon social-instagram-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Instagram">
                  <path fill="currentColor" d="M7.858 2.07c-1.064.05-1.79.22-2.425.47-.658.256-1.215.6-1.77 1.156a4.899 4.899 0 0 0-1.15 1.772c-.246.637-.413 1.364-.46 2.429-.047 1.064-.057 1.407-.052 4.122.005 2.716.017 3.056.069 4.123.05 1.064.22 1.79.47 2.426.256.657.6 1.214 1.156 1.769a4.894 4.894 0 0 0 1.774 1.15c.636.245 1.363.413 2.428.46 1.064.046 1.407.057 4.122.052 2.715-.005 3.056-.017 4.123-.068 1.067-.05 1.79-.221 2.425-.47a4.901 4.901 0 0 0 1.769-1.156 4.9 4.9 0 0 0 1.15-1.774c.246-.636.413-1.363.46-2.427.046-1.067.057-1.408.052-4.123-.005-2.715-.018-3.056-.068-4.122-.05-1.067-.22-1.79-.47-2.427a4.91 4.91 0 0 0-1.156-1.769 4.88 4.88 0 0 0-1.773-1.15c-.637-.245-1.364-.413-2.428-.46-1.065-.045-1.407-.057-4.123-.052-2.716.005-3.056.017-4.123.069Zm.117 18.078c-.975-.043-1.504-.205-1.857-.34-.467-.18-.8-.398-1.152-.746a3.08 3.08 0 0 1-.75-1.149c-.137-.352-.302-.881-.347-1.856-.05-1.054-.06-1.37-.066-4.04-.006-2.67.004-2.986.05-4.04.042-.974.205-1.504.34-1.857.18-.468.397-.8.746-1.151a3.087 3.087 0 0 1 1.15-.75c.351-.138.88-.302 1.855-.348 1.054-.05 1.37-.06 4.04-.066 2.67-.006 2.986.004 4.041.05.974.043 1.505.204 1.857.34.467.18.8.397 1.151.746.352.35.568.682.75 1.15.138.35.302.88.348 1.855.05 1.054.062 1.37.066 4.04.005 2.669-.004 2.986-.05 4.04-.043.975-.205 1.504-.34 1.857a3.1 3.1 0 0 1-.747 1.152c-.349.35-.681.567-1.148.75-.352.137-.882.301-1.855.347-1.055.05-1.371.06-4.041.066-2.67.006-2.986-.005-4.04-.05m8.152-13.493a1.2 1.2 0 1 0 2.4-.003 1.2 1.2 0 0 0-2.4.003ZM6.865 12.01a5.134 5.134 0 1 0 10.27-.02 5.134 5.134 0 0 0-10.27.02Zm1.802-.004a3.334 3.334 0 1 1 6.667-.013 3.334 3.334 0 0 1-6.667.013Z"></path>
                </svg>    </a>
              <a class="social-link as-snapchat" href="https://www.snapchat.com/p/6f1c2e77-0539-4e08-a90c-7bdd4b3f1da9/3298916208531456" label="snapchat" title="Follow us on Snapchat" aria-label="Click to visit us on Snapchat" data-track-click="{&quot;click_text&quot;:&quot;snapchat&quot;}" data-e2e-name="snapchat" target="_blank" rel="noopener nofollow">
                <svg class="svg-icon social-snapchat-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Snapchat">
                  <path fill="currentColor" d="M21.928 16.396c-.139-.364-.403-.56-.705-.721a1.757 1.757 0 0 0-.153-.078c-.09-.045-.182-.088-.273-.134-.94-.48-1.674-1.087-2.183-1.805a4.065 4.065 0 0 1-.374-.64c-.044-.12-.042-.189-.01-.25a.413.413 0 0 1 .12-.122c.161-.103.328-.207.44-.278.202-.125.361-.225.464-.295.386-.26.656-.537.824-.846a1.64 1.64 0 0 0 .087-1.399c-.256-.648-.891-1.051-1.66-1.051a2.368 2.368 0 0 0-.61.078c.007-.444-.003-.912-.044-1.373-.145-1.62-.733-2.47-1.346-3.147a5.337 5.337 0 0 0-1.37-1.062C14.206 2.76 13.15 2.5 12 2.5c-1.15 0-2.2.26-3.132.773-.515.28-.978.639-1.371 1.064-.614.678-1.202 1.528-1.347 3.147-.04.46-.051.932-.044 1.373a2.367 2.367 0 0 0-.609-.078c-.77 0-1.406.402-1.66 1.051a1.632 1.632 0 0 0 .084 1.4c.169.31.439.586.824.846.103.07.262.169.464.296l.423.267c.055.034.101.079.136.132.033.064.034.134-.014.262a4.02 4.02 0 0 1-.369.627c-.498.703-1.21 1.298-2.12 1.775-.481.246-.982.41-1.194.965-.16.419-.055.895.35 1.296.15.15.322.276.511.373.395.21.815.371 1.25.483.09.022.176.059.253.108.148.125.127.313.324.588.098.142.224.265.37.363.412.275.876.292 1.368.31.444.017.947.035 1.522.218.238.076.486.223.772.395.689.408 1.631.966 3.208.966 1.577 0 2.526-.561 3.22-.971.284-.169.53-.314.761-.388.575-.183 1.078-.201 1.522-.218.492-.018.956-.035 1.369-.31.172-.116.316-.268.42-.444.142-.232.139-.394.272-.508a.796.796 0 0 1 .237-.104 5.677 5.677 0 0 0 1.267-.487c.202-.104.383-.241.537-.405l.005-.006c.38-.392.475-.855.32-1.263Zm-1.401.727c-.855.455-1.423.406-1.865.68-.376.234-.154.737-.426.918-.336.223-1.326-.016-2.607.392-1.055.337-1.729 1.305-3.628 1.305-1.898 0-2.556-.966-3.63-1.308-1.277-.407-2.27-.168-2.605-.391-.273-.182-.051-.684-.426-.918-.443-.274-1.011-.225-1.866-.678-.544-.29-.235-.47-.054-.554 3.097-1.446 3.591-3.68 3.613-3.845.027-.2.056-.358-.173-.562-.22-.197-1.203-.783-1.475-.967-.45-.303-.649-.606-.503-.979.102-.258.352-.355.613-.355.083 0 .166.01.246.027.495.103.975.342 1.253.407a.457.457 0 0 0 .102.013c.148 0 .2-.072.19-.235-.032-.522-.108-1.54-.023-2.49.117-1.309.554-1.957 1.073-2.53.25-.275 1.421-1.47 3.662-1.47 2.24 0 3.415 1.19 3.665 1.464.52.573.957 1.222 1.073 2.53.085.95.011 1.968-.023 2.49-.012.172.042.235.19.235a.457.457 0 0 0 .102-.013c.278-.065.758-.304 1.253-.407a1.18 1.18 0 0 1 .246-.027c.263 0 .51.099.613.355.146.373-.051.676-.502.98-.273.183-1.254.768-1.475.966-.23.204-.2.362-.173.562.022.168.515 2.401 3.613 3.845.182.088.491.268-.053.56Z"></path>
                </svg>    </a>
          </div>
        </footer>
      </nav>
    


  <section class="post-page-container" data-content-container="">

  
    
  
    <section class="post-top grid-lines as- with-lead-image with-follow-topic component-loaded" data-component-type="post-top" data-load-strategy="disable-lazy">
  
      <div class="post-top-text-wrapper">
        
          <section class="post-headline" id="post-headline">
            <h1 class="headline heading-xl ">The cofounder shakeup at xAI is vintage Elon Musk</h1>
        
          </section>
          
          
          
            <section class="post-byline subtle component-loaded" data-component-type="post-byline" data-track-marfeel="post-byline" data-mrf-recirculation="post byline">
              <div class="byline-content">
                    
                    
                    <div class="byline-wrapper as-byline" data-e2e-name="byline">
                      <div class="byline-author-container">
                              
                              By
                              
                              
                              
                                <span class="byline-author " data-e2e-name="Grace Kay">
                              
                                  <span class="byline-author-text">
                                    <a class="byline-link byline-author-name font-weight-600" data-e2e-name="byline-author-name" href="https://www.businessinsider.com/author/grace-kay" data-mrf-link="https://www.businessinsider.com/author/grace-kay" cmp-ltrk="post byline" cmp-ltrk-idx="0" mrfobservableid="2558f036-69fa-4ded-9554-acfd0badc864">Grace Kay</a>          
                                        
                                        <span class="component rich-tooltip cta-follow-button-rich-tooltip" role="tooltip" data-tooltip-position="middle" data-tooltip-active="false" data-track-view="{&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;byline&quot;,&quot;element_name&quot;:&quot;follow_author&quot;,&quot;event&quot;:&quot;module_in_view&quot;}">
                                            <div class="rich-tooltip-wrapper">
                                              <div class="rich-tooltip-message label-md">
                                                  You're currently following this author!
                                       Want to unfollow? Unsubscribe via the link in your email.
                                              </div>
                                            </div>
                                            <button class="cta-follow-button label-md follow-topic cta-follow-button--icon-only component-loaded" data-component-type="cta-follow-button" data-state="" data-topic-type="author" data-topic-slug="grace-kay" title="Follow author" data-track-click="{&quot;click_text&quot;:&quot;&quot;,&quot;newsletter_name&quot;:&quot;author_grace_kay&quot;,&quot;action&quot;:&quot;follow_click&quot;,&quot;product_field&quot;:&quot;byline&quot;,&quot;element_name&quot;:&quot;follow_author&quot;,&quot;event&quot;:&quot;newsletter_flow&quot;}">
                                              <span class="cta-follow-button-icon">
                                                  <svg class="svg-icon plus-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                                                    <path fill="currentColor" d="M14.006 2H9.994v7.994H2v4.012h7.994V22h4.012v-7.994H22V9.994h-7.994V2Z"></path>
                                                  </svg>        </span>
                                              
                                            </button>
                                        </span>
                                      
                                        
                                        
                              </span>
                                </span>  </div>
                    </div>
                    
          
                
                
              </div>
            </section>
      </div>
    </section>

  <section class="post-page-grid">
    
    
    
    
      <section id="post-body" class="post-body grid-area-post-body" data-component-type="post-body" data-load-strategy="exclude" data-lock-content="">
            
            
            
            <div class="post-hero" data-component-type="post-hero" data-load-strategy="exclude">
                  <figure class="figure image-figure-image    as-notched" data-type="img" data-e2e-name="image-figure-image" data-media-container="image" itemscope="" itemtype="https://schema.org/ImageObject">
                      <div class="aspect-ratio" style="padding-top: calc(100% / (5616 / 3744))">
                        <meta itemprop="contentUrl" content="https://i.insider.com/68132d97a466d2b74ab4ae56?width=700">
                        <img src="https://i.insider.com/68132d97a466d2b74ab4ae56?width=700" srcset="https://i.insider.com/68132d97a466d2b74ab4ae56?width=400&amp;format=jpeg&amp;auto=webp 400w, https://i.insider.com/68132d97a466d2b74ab4ae56?width=500&amp;format=jpeg&amp;auto=webp 500w, https://i.insider.com/68132d97a466d2b74ab4ae56?width=700&amp;format=jpeg&amp;auto=webp 700w, https://i.insider.com/68132d97a466d2b74ab4ae56?width=1000&amp;format=jpeg&amp;auto=webp 1000w, https://i.insider.com/68132d97a466d2b74ab4ae56?width=1300&amp;format=jpeg&amp;auto=webp 1300w, https://i.insider.com/68132d97a466d2b74ab4ae56?width=2000&amp;format=jpeg&amp;auto=webp 2000w" sizes="(min-width: 1280px) 900px" alt="Elon Musk" decoding="sync">
                      </div>
                  
                    <span class="image-source-only ">
                      <span class="image-source label-md g-test" data-e2e-name="image-source" itemprop="creditText">Andrew Harnik/Getty Images</span>  </span>
                  </figure>
            </div>
    
    
    
            
      
              <div class="underline">
                
                
                
                  <div class="timestamp label-md" data-component-type="timestamp" data-load-strategy="exclude">
                    <time class="timestamp js-date-format js-rendered" data-timestamp="2026-04-04T09:22:01.236Z" data-disable-relative-formatting="">Apr 4, 2026, 5:22 AM ET</time>
                  </div>
                
                
                <div class="share-bar component-loaded" data-component-type="share-bar" data-load-strategy="lazy">
                  
                  
                  
                    <div class="share component-loaded" data-component-type="share" data-load-strategy="lazy">
                      <button class="dropdown-toggle label-md-strong" aria-label="Show sharing options">
                        <svg class="svg-icon share-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0.5 24 24">
                          <path fill="currentColor" d="m15.76 8.064-4.333-4.178L13.383 2 21 9.344l-7.617 7.344-1.956-1.886 4.223-4.07H5.766V22H3V8.064h12.76Z"></path>
                        </svg>      <span class="d-none d-md-block">Share</span>
                      </button>
                      <div class="share-dropdown hidden" data-track-click-shared="{&quot;event&quot;:&quot;share&quot;}">
                          <span class="dropdown-item label-md" data-copy="" title="Copy link" aria-label="Click to copy link" data-href-share="" data-utm-term="" target="_blank" data-track-click="{&quot;click_url&quot;:&quot;bi_value_unassigned&quot;,&quot;share_type&quot;:&quot;copy_link&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon link-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M3.554 12.536c-2.118 2.118-2.064 5.606.12 7.79s5.672 2.238 7.79.12l3.088-3.088-1.737-1.736-3.087 3.087c-1.188 1.189-3.145 1.159-4.37-.067-1.226-1.225-1.256-3.181-.067-4.37l3.087-3.087-1.736-1.737-3.088 3.088ZM12.536 3.554 9.448 6.642l1.737 1.736 3.087-3.087c1.188-1.189 3.145-1.159 4.37.067 1.226 1.225 1.256 3.182.067 4.37l-3.087 3.087 1.736 1.737 3.088-3.088c2.118-2.118 2.064-5.606-.12-7.79s-5.672-2.238-7.79-.12Z"></path>
                            <path fill="currentColor" d="m14.551 7.712-6.839 6.84 1.737 1.736 6.839-6.84-1.737-1.736Z"></path>
                          </svg></span>
                            <span class="dropdown-icon display-copied"><svg class="svg-icon check-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M21.985 6.289 19.19 3.277 8.383 14.222 4.117 9.895l-2.813 3.013 7.082 7.044L21.985 6.289Z"></path>
                          </svg></span>
                            <span class="label-md dropdown-label">Copy link</span>
                          </span>        <a class="dropdown-item label-md" data-email="" href="mailto:?subject=The cofounder shakeup at xAI is vintage Elon Musk&amp;body=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk%0D%0A%0D%0Ahttps%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;" title="Email" aria-label="Click to email" data-utm-term="" data-track-click="{&quot;click_url&quot;:&quot;mailto:?subject=The cofounder shakeup at xAI is vintage Elon Musk&amp;body=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk%0D%0A%0D%0Ahttps%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;&quot;,&quot;share_type&quot;:&quot;email&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon email-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                            <path fill="currentColor" fill-rule="evenodd" d="M2 4h20v16H2V4Zm2.5 13.5V8.09l7.455 7.455L19.5 8v9.5h-15Zm13.672-11H5.738l6.217 6.217L18.172 6.5Z"></path>
                          </svg></span>
                            <span class="label-md dropdown-label">Email</span>
                          </a>        <span class="dropdown-item label-md" data-facebook="" title="Share on Facebook" aria-label="Click to share on Facebook" data-href-share="https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;utmSource=facebook&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=facebook" data-utm-term="" target="_blank" data-track-click="{&quot;click_text&quot;:&quot;Share on Facebook&quot;,&quot;click_url&quot;:&quot;https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;utmSource=facebook&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=facebook&quot;,&quot;share_type&quot;:&quot;facebook&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon social-facebook-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Facebook">
                            <path fill="currentColor" d="M22 12.037C22 6.494 17.523 2 12 2S2 6.494 2 12.037c0 4.707 3.229 8.656 7.584 9.741v-6.674H7.522v-3.067h2.062v-1.322c0-3.416 1.54-5 4.882-5 .634 0 1.727.125 2.174.25v2.78a12.807 12.807 0 0 0-1.155-.037c-1.64 0-2.273.623-2.273 2.244v1.085h3.266l-.561 3.067h-2.705V22C18.163 21.4 22 17.168 22 12.037Z"></path>
                          </svg></span>
                            <span class="label-md dropdown-label">Facebook</span>
                          </span>        <span class="dropdown-item label-md" data-whatsapp="" title="Share on WhatsApp" aria-label="Click to share on WhatsApp" data-href-share="https://api.whatsapp.com/send?text=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;utmSource=whatsapp&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=whatsapp" target="_blank" data-popup-size="550|625" data-track-click="{&quot;click_text&quot;:&quot;Share on WhatsApp&quot;,&quot;click_url&quot;:&quot;https://api.whatsapp.com/send?text=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;utmSource=whatsapp&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=whatsapp&quot;,&quot;share_type&quot;:&quot;whatsapp&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon social-whatsapp-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="WhatsApp">
                            <path fill="currentColor" fill-rule="evenodd" d="M18.802 5.19A9.52 9.52 0 0 0 12.04 2.4c-5.27 0-9.558 4.268-9.56 9.513 0 1.677.44 3.314 1.276 4.757L2.4 21.6l5.068-1.323a9.584 9.584 0 0 0 4.568 1.158h.004c5.269 0 9.558-4.268 9.56-9.514a9.433 9.433 0 0 0-2.798-6.73ZM12.04 19.828h-.003a7.964 7.964 0 0 1-4.044-1.102l-.29-.171-3.008.785.803-2.919-.189-.299a7.86 7.86 0 0 1-1.215-4.208c.002-4.36 3.566-7.907 7.95-7.907 2.122 0 4.117.824 5.617 2.319a7.84 7.84 0 0 1 2.325 5.594c-.002 4.36-3.566 7.908-7.946 7.908Zm4.359-5.922c-.24-.12-1.414-.694-1.633-.773-.219-.08-.378-.12-.537.119-.159.238-.617.773-.756.932-.14.159-.279.178-.518.06-.239-.12-1.008-.37-1.92-1.18-.71-.631-1.19-1.41-1.33-1.648-.139-.238-.014-.366.105-.484.107-.107.239-.278.358-.417.12-.139.16-.238.24-.396.079-.16.039-.298-.02-.417-.06-.119-.538-1.289-.737-1.765-.194-.463-.391-.4-.537-.408a9.688 9.688 0 0 0-.458-.008c-.16 0-.418.059-.638.297-.219.238-.836.814-.836 1.983 0 1.17.856 2.3.976 2.46.12.158 1.684 2.56 4.08 3.59.57.244 1.015.39 1.362.5.572.181 1.093.156 1.505.095.458-.069 1.413-.576 1.612-1.13.199-.556.199-1.032.14-1.131-.06-.1-.22-.16-.459-.278v-.001Z" clip-rule="evenodd"></path>
                          </svg></span>
                            <span class="label-md dropdown-label">WhatsApp</span>
                          </span>        <span class="dropdown-item label-md" data-x="" title="Share on X" aria-label="Click to share on X" data-href-share="https://x.com/intent/tweet?text=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4%3FutmSource%3Dtwitter%26utmContent%3Dreferral%26utmTerm%3Dtopbar%26referrer%3Dtwitter&amp;via=businessinsider&amp;utmSource=twitter&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=twitter" data-utm-term="" target="_blank" data-track-click="{&quot;click_text&quot;:&quot;Share on X&quot;,&quot;click_url&quot;:&quot;https://x.com/intent/tweet?text=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4%3FutmSource%3Dtwitter%26utmContent%3Dreferral%26utmTerm%3Dtopbar%26referrer%3Dtwitter&amp;via=businessinsider&amp;utmSource=twitter&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=twitter&quot;,&quot;share_type&quot;:&quot;x&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon social-x-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="X">
                            <path fill="currentColor" d="M17.751 3h3.067l-6.7 7.625L22 21h-6.172l-4.833-6.293L5.464 21h-3.07l7.167-8.155L2 3h6.328l4.37 5.752L17.75 3Zm-1.076 16.172h1.7L7.404 4.732H5.58l11.094 14.44Z"></path>
                          </svg></span>
                            <span class="label-md dropdown-label">X</span>
                          </span>        <span class="dropdown-item label-md" data-linkedin="" title="Share on LinkedIn" aria-label="Click to share on LinkedIn" data-href-share="https://www.linkedin.com/shareArticle?url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;title=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;summary=xAI%20lost%20Ross%20Nordeen%2C%20its%20final%20non-Musk%20cofounder%2C%20this%20month.%20What%20does%20the%20turnover%20mean%20for%20the%20startup's%20looming%20IPO%20with%20SpaceX%3F&amp;mini=true&amp;utmSource=linkedIn&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=linkedIn" data-utm-term="" target="_blank" data-popup-size="975|720" data-track-click="{&quot;click_text&quot;:&quot;Share on LinkedIn&quot;,&quot;click_url&quot;:&quot;https://www.linkedin.com/shareArticle?url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;title=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;summary=xAI%20lost%20Ross%20Nordeen%2C%20its%20final%20non-Musk%20cofounder%2C%20this%20month.%20What%20does%20the%20turnover%20mean%20for%20the%20startup's%20looming%20IPO%20with%20SpaceX%3F&amp;mini=true&amp;utmSource=linkedIn&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=linkedIn&quot;,&quot;share_type&quot;:&quot;linkedin&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon social-linkedin-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="LinkedIn">
                            <path fill="currentColor" fill-rule="evenodd" d="M4 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H4Zm4.339 4.606a1.627 1.627 0 1 1-3.254 0 1.627 1.627 0 0 1 3.254 0Zm-.221 2.867H5.13v9.335h2.988V9.473Zm4.517 0H9.662v9.335h2.943V13.91c0-2.729 3.461-2.982 3.461 0v4.9h2.849v-5.914c0-4.6-5.07-4.43-6.31-2.17l.03-1.252Z"></path></svg>
                          </span>
                            <span class="label-md dropdown-label">LinkedIn</span>
                          </span>        <span class="dropdown-item label-md" data-bluesky="" title="Share on Bluesky" aria-label="Click to share on Bluesky" data-href-share="https://bsky.app/share?url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;title=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;utmSource=bluesky&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=bluesky" target="_blank" data-popup-size="550|625" data-track-click="{&quot;click_text&quot;:&quot;Share on Bluesky&quot;,&quot;click_url&quot;:&quot;https://bsky.app/share?url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;title=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;utmSource=bluesky&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=bluesky&quot;,&quot;share_type&quot;:&quot;bluesky&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon social-bluesky-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Bluesky">
                            <path fill="currentColor" d="M6.562 4.73C8.763 6.374 11.13 9.704 12 11.49c.87-1.787 3.237-5.117 5.438-6.76 1.588-1.184 4.162-2.101 4.162.817 0 .582-.336 4.894-.533 5.594-.686 2.434-3.183 3.055-5.405 2.68 3.884.656 4.871 2.832 2.738 5.007-4.052 4.131-5.823-1.037-6.277-2.36-.083-.244-.122-.357-.123-.26 0-.097-.04.016-.123.26-.454 1.323-2.225 6.491-6.277 2.36-2.133-2.175-1.146-4.35 2.738-5.008-2.222.376-4.72-.245-5.405-2.679-.197-.7-.533-5.012-.533-5.594 0-2.918 2.574-2.001 4.162-.816Z"></path></svg>
                          </span>
                            <span class="label-md dropdown-label">Bluesky</span>
                          </span>        <span class="dropdown-item label-md" data-threads="" title="Share on Threads" aria-label="Click to share on Threads" data-href-share="https://www.threads.com/intent/post?url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;text=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;utmSource=threads&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=threads" data-utm-term="" target="_blank" data-popup-size="550|625" data-track-click="{&quot;click_text&quot;:&quot;Share on Threads&quot;,&quot;click_url&quot;:&quot;https://www.threads.com/intent/post?url=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;text=The%20cofounder%20shakeup%20at%20xAI%20is%20vintage%20Elon%20Musk&amp;utmSource=threads&amp;utmContent=referral&amp;utmTerm=topbar&amp;referrer=threads&quot;,&quot;share_type&quot;:&quot;threads&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                            <span class="dropdown-icon"><svg class="svg-icon social-threads-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                            <g transform="matrix(1.5714285714 0 0 1.5714285714 2.5714285714 1)">
                              <path d="M6.106 13.5h-.004c-2.04-.014-3.61-.678-4.664-1.974C.5 10.372.016 8.766 0 6.756v-.01c.016-2.013.5-3.617 1.439-4.771C2.492.678 4.062.014 6.102 0h.008C7.675.01 8.984.408 10 1.18c.956.726 1.63 1.76 2 3.075l-1.163.32c-.629-2.227-2.221-3.365-4.732-3.383-1.658.012-2.912.527-3.728 1.528-.762.938-1.156 2.294-1.17 4.03.014 1.736.408 3.092 1.172 4.03.815 1.003 2.07 1.517 3.727 1.528 1.495-.01 2.484-.355 3.306-1.15.938-.907.922-2.021.621-2.699-.176-.4-.498-.732-.931-.984q-.166 1.142-.732 1.84c-.505.62-1.22.959-2.126 1.007-.685.037-1.346-.123-1.857-.45-.606-.388-.96-.98-.999-1.668a2.09 2.09 0 0 1 .758-1.733c.502-.428 1.208-.68 2.042-.727a8 8 0 0 1 1.72.08c-.07-.417-.213-.75-.426-.988-.293-.33-.745-.497-1.345-.501h-.016c-.481 0-1.135.13-1.551.742l-1.001-.662c.558-.819 1.463-1.27 2.552-1.27h.025c1.82.011 2.905 1.112 3.013 3.031q.093.04.183.08c.85.394 1.47.99 1.798 1.727.454 1.024.496 2.694-.883 4.027-1.054 1.018-2.333 1.478-4.147 1.49zm.572-6.576q-.206 0-.422.012c-1.046.058-1.698.532-1.661 1.206.038.706.827 1.034 1.586.993.698-.036 1.606-.305 1.76-2.087a6 6 0 0 0-1.263-.124"></path>
                            </g>
                          </svg></span>
                            <span class="label-md dropdown-label">Threads</span>
                          </span>        <span class="dropdown-item label-md" data-impact="" title="Copy impact link" aria-label="Click to copy impact link" hidden="">
                            <span class="dropdown-icon"><svg class="" width="6" height="16" viewBox="0 0 11 21" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <title>lighning bolt icon</title>
                            <desc>An icon in the shape of a lightning bolt.</desc>
                          
                            <path class="lightning-bolt" d="M4.1245 0L0.25 9.996H4.4395L0.25 21L10.729 6.25275H6.01975L9.1855 0H4.1245Z" fill="#002aff"></path>
                          </svg></span>
                            <span class="label-md dropdown-label">Impact Link</span>
                          </span>    </div>
                    </div>
                  
                  
                  
                  <span class="save-article label-md component-loaded" title="Save Article" aria-label="Save this article" data-location="top" data-component-type="save-article" data-load-strategy="lazy" data-track-element="story" data-e2e-name="share-link-save-article" role="button" data-track-element-name="saved_articles">
                      <svg class="svg-icon save-icon  " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 -0.5 24 24">
                        <defs>
                          <style>
                            .save-icon-fill {
                              display: none;
                            }
                            .save-icon.is-active .save-icon-fill,
                            .save-icon-fill.is-active {
                              display: block;
                              fill: currentColor;
                            }
                          </style>
                        </defs>
                        <path fill="currentColor" fill-rule="evenodd" d="M3 2h18v20l-9-6.567L3 22V2Zm2.432 2.413V17.23L12 12.437l6.568 4.793V4.413H5.432Z"></path>
                        <path class="save-icon-fill " fill-rule="evenodd" d="M21 2H3v20l9-6.567L21 22V2Z"></path>
                      </svg>    <span class="button-text font-weight-garnett-600 d-none d-md-block">
                        <span class="button-text-content">Save</span>
                        <span class="button-text-content display-saved">Saved</span>
                      </span>
                  </span>  
                  <a class="d-md-none app-button" data-app-button="" data-only-on="mobile" data-component-type="app-button" data-load-strategy="lazy" title="Download the app" aria-label="Click to download the app" target="_blank" href="https://insider-app.onelink.me/4cpG/?af_js_web=true&amp;af_ss_ver=2_3_0&amp;af_dp=insider%3A%2F%2Fbi%2Fpost%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;af_force_deeplink=true&amp;is_retargeting=true&amp;deep_link_value=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;pid=businessinsider&amp;c=post_page_share_bar_v2_smart_4.13.23" data-track-click="{&quot;event&quot;:&quot;app_cta&quot;,&quot;click_text&quot;:&quot;read_in_app&quot;,&quot;element_name&quot;:&quot;sharebar&quot;}">
                    <svg class="svg-icon app-monogram-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M11.068 10.2c0 .401-.315.763-1.009.763H8.83v-1.54h1.23c.694 0 1.009.375 1.009.777ZM11.185 13.747c0 .469-.354.83-1.087.83h-1.27v-1.66h1.284c.706 0 1.073.361 1.073.83Z"></path>
                      <path fill="currentColor" fill-rule="evenodd" d="M6 2a4 4 0 0 0-4 4v12a4 4 0 0 0 4 4h12a4 4 0 0 0 4-4V6a4 4 0 0 0-4-4H6Zm4.19 5H6v10h4.36c2.462 0 3.601-1.325 3.601-2.838 0-1.057-.576-1.887-1.597-2.262v-.027c.799-.375 1.375-1.084 1.375-2.128C13.739 8.232 12.52 7 10.19 7Zm7.826 0H15.16v10h2.855V7Z"></path>
                    </svg>  <span class="button-text label-md-strong">
                      Read in app
                    </span>
                  </a></div>        </div>
      
            <div class="inline-backup-paywall desktop" data-component-type="inline-backup-paywall" style="display:none">
              <span class="headline-semibold subscription-msg">This story is available exclusively to Business Insider
                subscribers. <a href="/subscription" class="subscription-link">Become an Insider</a>
                and start reading now.</span>
              <span class="headline-regular login-prompt">Have an account? <button class="login-prompt-btn">Log in</button>.</span>
            </div>
      
              
              
              
              <div class="ai-summary-questions__wrapper"><div class="post-summary-bullets" data-component-type="post-summary-bullets" data-load-strategy="exclude" data-track-marfeel="post-summary-bullets" data-mrf-recirculation="post summary bullets">
                <ul>
                    <li class="body-md">Elon Musk is following a familiar Tesla-era playbook for his rebuilding plans at xAI.</li>
                    <li class="body-md">The stakes are higher now, with a highly competitive AI environment and a looming SpaceX IPO.</li>
                    <li class="body-md">XAI's cofounder exodus raises red flags at a pivotal moment in the company's history, experts said.</li>
                </ul>
              </div><div class="ai-summary-questions component-loaded ai-summary-questions--chips-animate" data-component-type="ai-summary-questions" data-load-strategy="defer" data-post-id="elon-musk-xai-cofounder-exits-spacex-ipo-2026-4" data-track-view="{&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;event&quot;:&quot;module_in_view&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}" data-chips-revealed="true">
                <!-- Active question section (top row) -->
                <div class="ai-summary-questions__top-section" aria-hidden="true">
                  <div class="ai-summary-questions__active-question js-active-question"></div>
                  <div class="ai-summary-questions__header js-response-header">
                    <span class="ai-disclaimer ai-disclaimer--purple ai-disclaimer--single-bullet" data-ai-disclaimer="" data-alignment="responsive" role="button" tabindex="0" aria-label="AI Generated content disclaimer">
                        <span class="ai-disclaimer__icon" style="order: 1;"><svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4.60666 4.6H5.60791V6.94444H4.60666V4.6Z" fill="currentColor"></path><path fill-rule="evenodd" clip-rule="evenodd" d="M5 10C7.7615 10 10 7.76143 10 5C10 2.23857 7.7615 0 5 0C2.2385 0 0 2.23857 0 5C0 7.76143 2.2385 10 5 10ZM8.61111 5C8.61111 6.99436 6.99436 8.61111 5 8.61111C3.00564 8.61111 1.38889 6.99436 1.38889 5C1.38889 3.00564 3.00564 1.38889 5 1.38889C6.99436 1.38889 8.61111 3.00564 8.61111 5Z" fill="currentColor"></path><path d="M4.60703 2.85148H5.60828V3.8H4.60703V2.85148Z" fill="currentColor"></path></svg></span>
                        <span class="ai-disclaimer__label" style="order: 0;">AI-generated summary</span>
                        <span class="ai-disclaimer__tooltip">
                          <span class="ai-disclaimer__arrow"></span>
                          <ul class="ai-disclaimer__list">
                            <li>Summaries are generated by an AI model trained on Business Insider's articles. AI may make mistakes or provide inaccurate/incomplete information.</li>
                          </ul>
                        </span>
                      </span>      <button type="button" class="ai-summary-questions__close-btn js-close-btn" aria-label="Close AI summary" data-track-click="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;click_text&quot;:&quot;bi_value_unassigned&quot;,&quot;action&quot;:&quot;close&quot;,&quot;event&quot;:&quot;engagement_interaction&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}">
                      <svg class="svg-icon close-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M21 5.394 18.606 3 12 9.606 5.394 3 3 5.394 9.606 12 3 18.606 5.394 21 12 14.394 18.606 21 21 18.606 14.394 12 21 5.394Z"></path>
                      </svg>      </button>
                  </div>
                </div>
              
                <!-- Overlay container for bullets (floats above content below) -->
                <div class="ai-summary-questions__overlay js-overlay" aria-hidden="true">
                  <template class="ai-summary-questions__sparkle-template">
                    <svg class="svg-icon sparkle-filled-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                      <g transform="matrix(1 0 0 1 3 2.5)">
                        <path fill="currentColor" d="M5.3 4.632a.2.2 0 0 1 .355 0l1.732 3.372a.2.2 0 0 0 .087.086l3.371 1.733a.2.2 0 0 1 0 .355l-3.371 1.733a.2.2 0 0 0-.087.086l-1.732 3.371a.2.2 0 0 1-.356 0l-1.732-3.371a.2.2 0 0 0-.087-.086L.11 10.178a.2.2 0 0 1 0-.355L3.48 8.09a.2.2 0 0 0 .087-.086zM11.8 12.346a.2.2 0 0 1 .355 0l.981 1.909a.2.2 0 0 0 .087.086l1.908.981a.2.2 0 0 1 0 .356l-1.908.98a.2.2 0 0 0-.087.087l-.98 1.909a.2.2 0 0 1-.356 0l-.981-1.909a.2.2 0 0 0-.087-.086l-1.908-.981a.2.2 0 0 1 0-.356l1.909-.98a.2.2 0 0 0 .086-.087z"></path>
                      </g>
                    </svg>    </template>
                  <!-- Bullets container (inside overlay) -->
                  <div class="ai-summary-questions__bullets-container js-bullets-container">
                    <div class="ai-summary-questions__error js-error" role="alert" aria-hidden="true">
                      We're unable to load that answer right now. Please try again.
                    </div>
                    <ul class="ai-summary-questions__response-list js-response-list"></ul>
                  </div>
                </div>
              
                <!-- Other questions list (bottom rows) -->
              
                <div class="ai-summary-questions__chips-row">
              
              
              <div class="carousel-gradient as-ai-summary-questions component-loaded" data-component-type="carousel-gradient" data-load-strategy="defer">
                <div class="carousel with-gradient with-fade-right">
                        <span class="ai-summary-questions__sparkle" aria-hidden="true">
                          <svg class="svg-icon sparkle-filled-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                            <g transform="matrix(1 0 0 1 3 2.5)">
                              <path fill="currentColor" d="M5.3 4.632a.2.2 0 0 1 .355 0l1.732 3.372a.2.2 0 0 0 .087.086l3.371 1.733a.2.2 0 0 1 0 .355l-3.371 1.733a.2.2 0 0 0-.087.086l-1.732 3.371a.2.2 0 0 1-.356 0l-1.732-3.371a.2.2 0 0 0-.087-.086L.11 10.178a.2.2 0 0 1 0-.355L3.48 8.09a.2.2 0 0 0 .087-.086zM11.8 12.346a.2.2 0 0 1 .355 0l.981 1.909a.2.2 0 0 0 .087.086l1.908.981a.2.2 0 0 1 0 .356l-1.908.98a.2.2 0 0 0-.087.087l-.98 1.909a.2.2 0 0 1-.356 0l-.981-1.909a.2.2 0 0 0-.087-.086l-1.908-.981a.2.2 0 0 1 0-.356l1.909-.98a.2.2 0 0 0 .086-.087z"></path>
                            </g>
                          </svg>      </span>
                        <div class="ai-summary-questions__list-columns">
                          <ul class="ai-summary-questions__list js-questions-list">
                            <li class="ai-summary-questions__item" data-index="0" style="order: 0; --chip-delay: 0ms;">
                              <button type="button" class="ai-summary-questions__button js-question-btn label-md" data-question="What does Musk's &quot;playbook&quot; entail?" data-confidence="0.95" data-track-click="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;index&quot;:1,&quot;click_text&quot;:&quot;What does Musk's \&quot;playbook\&quot; entail?&quot;,&quot;action&quot;:&quot;question_click&quot;,&quot;event&quot;:&quot;engagement_interaction&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}">
                                What does Musk's "playbook" entail?
                              </button>
                            </li>
                            <li class="ai-summary-questions__item" data-index="2" style="order: 2; --chip-delay: 500ms;">
                              <button type="button" class="ai-summary-questions__button js-question-btn label-md" data-question="What are the IPO challenges for SpaceX?" data-confidence="0.96" data-track-click="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;index&quot;:3,&quot;click_text&quot;:&quot;What are the IPO challenges for SpaceX?&quot;,&quot;action&quot;:&quot;question_click&quot;,&quot;event&quot;:&quot;engagement_interaction&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}">
                                What are the IPO challenges for SpaceX?
                              </button>
                            </li>
                            <li class="ai-summary-questions__item" data-index="4" style="order: 4; --chip-delay: 1000ms;">
                              <button type="button" class="ai-summary-questions__button js-question-btn label-md" data-question="What drives talent retention in AI firms?" data-confidence="0.94" data-track-click="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;index&quot;:5,&quot;click_text&quot;:&quot;What drives talent retention in AI firms?&quot;,&quot;action&quot;:&quot;question_click&quot;,&quot;event&quot;:&quot;engagement_interaction&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}">
                                What drives talent retention in AI firms?
                              </button>
                            </li>
                          </ul>
                          <ul class="ai-summary-questions__list js-questions-list">
                            <li class="ai-summary-questions__item" data-index="1" style="order: 1; --chip-delay: 250ms;">
                              <button type="button" class="ai-summary-questions__button js-question-btn label-md" data-question="How do cofounder exits affect startups?" data-confidence="0.92" data-track-click="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;index&quot;:2,&quot;click_text&quot;:&quot;How do cofounder exits affect startups?&quot;,&quot;action&quot;:&quot;question_click&quot;,&quot;event&quot;:&quot;engagement_interaction&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}">
                                How do cofounder exits affect startups?
                              </button>
                            </li>
                            <li class="ai-summary-questions__item" data-index="3" style="order: 3; --chip-delay: 750ms;">
                              <button type="button" class="ai-summary-questions__button js-question-btn label-md" data-question="How does competition shape AI companies?" data-confidence="0.97" data-track-click="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;index&quot;:4,&quot;click_text&quot;:&quot;How does competition shape AI companies?&quot;,&quot;action&quot;:&quot;question_click&quot;,&quot;event&quot;:&quot;engagement_interaction&quot;,&quot;element_name&quot;:&quot;ai_summary_bullets&quot;}">
                                How does competition shape AI companies?
                              </button>
                            </li>
                          </ul>
                        </div>
                </div>
              </div>  </div>
              </div></div>
              
              
              
              
              
      
            
      
        <div class="image-modal component-loaded" data-component-type="image-modal" data-load-strategy="lazy">
                  
                  
                  
                  <section class="post-body-content post-story-body-content" data-component-type="post-body-content" data-load-strategy="exclude" data-track-content="" data-post-type="story" data-track-marfeel="post-body-content" data-mrf-recirculation="post body content" data-display="null">
                  
                      <p>Ross Nordeen didn't announce he was <a target="_self" href="https://www.businessinsider.com/xai-cofounder-ross-nordeen-leaves-musk-preps-spacex-ipo-2026-3" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="20" data-mrf-link="https://www.businessinsider.com/xai-cofounder-ross-nordeen-leaves-musk-preps-spacex-ipo-2026-3" cmp-ltrk="post body content" cmp-ltrk-idx="0" mrfobservableid="df633972-4d43-47f6-953c-c2d5167e290e">leaving xAI</a>. He didn't need to.</p>
                        <div class="audio-player-container">
                          
                  
                  
                    
                  
                  
                  
                  
                    <div class="audio-player is-idle" data-centered="false" style=""><audio src="https://ai-audio.insider-prd.engineering/post/elon-musk-xai-cofounder-exits-spacex-ipo-2026-4/narration.mp3" preload="auto"></audio><button class="audio-player-toggle-button" aria-label="Play audio"><div class="audio-player-toggle-icon"><svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="m3.5 2.5 6 3.5-6 3.5z" fill="currentColor"></path></svg></div><div class="audio-player-info label-md"><span class="audio-player-label">Listen to this story</span><span class="audio-player-dot"><svg xmlns="http://www.w3.org/2000/svg" width="3" height="3" viewBox="0 0 3 3" fill="none"><circle cx="1.5" cy="1.5" r="1.5" fill="currentColor"></circle></svg></span><span class="audio-player-duration">7 minutes</span></div></button></div>
                  
                        </div>
                      <div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_1-desktop-1" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-1/tech" data-region="in-content-1" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-1" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-1/tech&quot;,&quot;region&quot;:&quot;in-content-1&quot;,&quot;dvp_spos&quot;:&quot;in-content-1&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="1" data-ad-adjusted="" data-loaded-method="lazy" data-flow="doubleverify.success,rubicon.success,amazon.success,gam.requested" data-google-query-id="CLHpgo3z1JMDFRAhrAAdQyw6cg" data-ad-refresher-config="{&quot;isEmpty&quot;:false,&quot;curSize&quot;:[300,250],&quot;region&quot;:&quot;in-content-1&quot;}" data-viewable="false" data-timer="28"><div id="google_ads_iframe_/4442842/businessinsider.desktop/post/in-content-1/tech_0__container__" style="border: 0pt none;"><iframe id="google_ads_iframe_/4442842/businessinsider.desktop/post/in-content-1/tech_0" name="google_ads_iframe_/4442842/businessinsider.desktop/post/in-content-1/tech_0" title="3rd party ad content" width="300" height="250" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" aria-label="Advertisement" tabindex="0" allow="private-state-token-redemption;attribution-reporting" data-load-complete="true" style="border: 0px; vertical-align: bottom; width: 300px; height: 250px;" data-google-container-id="3"></iframe></div></div>
                        </div></div><p>The 36-year-old engineer was abruptly cut off from the company systems last week and disappeared from a sprawling group chat with CEO Elon Musk and hundreds of other engineers. Later, he posted a photo of a hiking trail with the caption: "Touching some grass."</p><p>Nordeen, one of the billionaire's closest deputies, was the final non-Musk cofounder to <a target="_self" class="" href="https://www.businessinsider.com/elon-musk-xai-leadership-style-big-year-grok-ipo-spacex-2026-2" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="20" data-mrf-link="https://www.businessinsider.com/elon-musk-xai-leadership-style-big-year-grok-ipo-spacex-2026-2" cmp-ltrk="post body content" cmp-ltrk-idx="1" mrfobservableid="b60f5119-f70e-45fd-a9c4-dc68318a0b04">depart the startup</a>, and the eighth to exit in under three months. It's an unusually rapid unraveling of a founding team at a critical point in the company's history.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_2-desktop-2" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-2/tech" data-region="in-content-2" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-2" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-2/tech&quot;,&quot;region&quot;:&quot;in-content-2&quot;,&quot;dvp_spos&quot;:&quot;in-content-2&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="1" data-ad-adjusted="" data-loaded-method="lazy" data-flow="doubleverify.success,amazon.success,rubicon.success,gam.requested" data-google-query-id="CJmCio3z1JMDFb4_rAAdZxwNCw" data-ad-refresher-config="{&quot;isEmpty&quot;:false,&quot;curSize&quot;:[1,1],&quot;region&quot;:&quot;in-content-2&quot;}" data-viewable="false" data-timer="26"><div id="google_ads_iframe_/4442842/businessinsider.desktop/post/in-content-2/tech_0__container__" style="border: 0pt none;"><iframe id="google_ads_iframe_/4442842/businessinsider.desktop/post/in-content-2/tech_0" name="google_ads_iframe_/4442842/businessinsider.desktop/post/in-content-2/tech_0" title="3rd party ad content" width="728" height="90" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" aria-label="Advertisement" tabindex="-1" allow="private-state-token-redemption;attribution-reporting" data-load-complete="true" data-google-container-id="4" style="border: 0px; vertical-align: bottom;"></iframe></div></div>
                        </div></div><p>As SpaceX, which <a target="_self" class="" href="https://www.businessinsider.com/xai-sends-staff-q-and-a-on-spacex-merger-2026-2" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="20" data-mrf-link="https://www.businessinsider.com/xai-sends-staff-q-and-a-on-spacex-merger-2026-2" cmp-ltrk="post body content" cmp-ltrk-idx="2" mrfobservableid="b9a4ea98-340d-4fd2-aebc-bac1e514cf55">merged with xAI</a> in February, races toward a blockbuster IPO, the shake-up has become something of a spectacle. It raises questions about the billionaire's motivations, the company's standing among competitors like OpenAI and Anthropic, and whether rebuilding is simply an iteration of Musk's playbook — or points to deeper issues inside the company.</p><p>"Anytime you see mass departures of the founding leadership team, that is a negative signal," Charles Elson, a corporate governance expert, told Business Insider.</p>
                    
                  
                    <div class="dynamic-module component-loaded" data-component-type="dynamic-module" data-load-strategy="lazy" data-root-margin="200% 0px">
                  
                          <div class="dynamic-module-components" data-component-name="newsletter-dynamic" data-component-segment="anonymous-newsletter" style="display: block;">
                            
                            <div class="newsletter-dynamic component-loaded" aria-expanded="true" aria-hidden="false" data-track-view="{&quot;element_name&quot;:&quot;inline_newsletter&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;}" data-component-type="newsletter-dynamic" data-load-strategy="exclude" data-element-name="inline_newsletter" data-source="techinlinesignup" data-skeleton-name="generic-tout" style=""><div class="component-container tech-memo"><div class="header"><span class="headline-bold title ">Tech Memo</span></div><p class="body-sm-subtle copy-text">Where Big Tech secrets go public — unfiltered in your inbox weekly.</p><form class="form "><input type="email" autocomplete="on" placeholder="Enter your email" required="" class="label-xl-subtle"><button type="submit" class="headline-semibold ">Sign up</button></form><p class="label-md-subtle error-message hide-error">Enter a valid email address</p><p class="headline-regular terms hide-terms">By clicking "Sign up", you agree to receive emails from Business Insider. In addition, you accept Insider’s <a target="_blank" rel="nofollow noopener noreferrer" href="https://www.businessinsider.com/terms" data-mrf-link="https://www.businessinsider.com/terms" cmp-ltrk="post body content" cmp-ltrk-idx="16" mrfobservableid="8380772a-34b1-4258-81c9-d414582279ce">Terms of Service</a> and <a target="_blank" rel="nofollow noopener noreferrer" href="https://www.businessinsider.com/privacy-policy" data-mrf-link="https://www.businessinsider.com/privacy-policy" cmp-ltrk="post body content" cmp-ltrk-idx="17" mrfobservableid="9bea5bb9-249f-4b2c-9fc8-d4be828b6498">Privacy Policy</a>.</p></div></div>        </div>
                  
                  
                    </div>
                  <div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_3-desktop-3" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-3/tech" data-region="in-content-3" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-3" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-3/tech&quot;,&quot;region&quot;:&quot;in-content-3&quot;,&quot;dvp_spos&quot;:&quot;in-content-3&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>"If things were bright and rosy for the future, why would you leave? Either you're leaving because you're cashing out, which suggests that you think the thing is overpriced or richly priced, or you're leaving because you don't have faith in the management of the organization going forward."</p><p>"Either way, it doesn't look good," he added.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-4" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-4" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>Franco Granda, a senior research analyst at Pitchbook, told Business Insider that companies are under increased scrutiny in the months leading up to an IPO. While the rocket ship business will be the core focus of SpaceX's stock market debut, the merger with xAI and exodus of cofounders created a "lot of distractions."</p><p>"When you integrate xAI, which is a bleeding, hemorrhaging business at this point, I think it creates a lot of risks," he said, pointing to reports of the startup burning through <a target="_blank" href="https://www.bloomberg.com/news/articles/2026-01-09/musk-s-xai-reports-higher-quarterly-loss-plans-to-power-optimus" data-track-click="{&quot;click_type&quot;:&quot;other&quot;,&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;outbound_click&quot;}" rel=" nofollow" data-analytics-post-depth="40" data-mrf-link="https://www.bloomberg.com/news/articles/2026-01-09/musk-s-xai-reports-higher-quarterly-loss-plans-to-power-optimus" cmp-ltrk="post body content" cmp-ltrk-idx="3" mrfobservableid="a68a56a6-8b64-4977-afa8-55f119ced35a">billions of dollars.</a></p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-5" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-5" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><h2 id="b143b714-a359-42f3-b73e-f12b06f8fa93" data-toc-id="b143b714-a359-42f3-b73e-f12b06f8fa93">'I thought he'd go down with the ship'</h2><p>Unlike some of the 10 cofounders who left before him, Nordeen's split was a surprise to some company insiders and close observers of Musk's empire.</p><p>He joined xAI in 2023 from Tesla, where he was a technical program manager on the <a target="_self" class="" href="https://www.businessinsider.com/ashok-elluswamy-tesla-autopilot-elon-musk-ai-2025-10" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="40" data-mrf-link="https://www.businessinsider.com/ashok-elluswamy-tesla-autopilot-elon-musk-ai-2025-10" cmp-ltrk="post body content" cmp-ltrk-idx="4" mrfobservableid="f14d7882-f6cf-43b7-8b23-44f72f348fb2">Autopilot team</a>. He's a longtime friend of Musk's cousin, James Musk, and was one of the "three musketeers" who assisted in Musk's 2022 <a target="_self" href="https://www.businessinsider.com/elon-musk-twitter" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="40" data-mrf-link="https://www.businessinsider.com/elon-musk-twitter" cmp-ltrk="post body content" cmp-ltrk-idx="5" mrfobservableid="db2084b3-bdcc-4984-871c-ada216818373">Twitter takeover</a>, according to Walter Isaacson's biography of the billionaire.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-6" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-6" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>One former colleague described Nordeen as "Musk's handler" and said, "I thought he'd go down with the ship."</p><p>Musk has said he's rebuilding that ship. In one social media post, he said xAI "was not built right first time around" and compared the turbulence to his retooling of Tesla nearly a decade ago.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-7" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-7" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>In 2008, Musk ousted cofounder and former <a target="_self" class="" href="https://www.businessinsider.com/tesla-cofounder-martin-eberhard-interview-history-elon-musk-ev-market-2023-2" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="40" data-mrf-link="https://www.businessinsider.com/tesla-cofounder-martin-eberhard-interview-history-elon-musk-ev-market-2023-2" cmp-ltrk="post body content" cmp-ltrk-idx="6" mrfobservableid="2f8519a4-4a59-4a4e-adb1-4d6f24263f16">CEO Martin Eberhard</a>, who was followed out the door by cofounder Marc Tarpenning. Tesla went through two more CEOs before Musk took over and built a fledgling startup with a few dozen employees into the most valuable car company in the world.</p><p>That turnaround magic could be difficult to replicate at xAI. Unlike Tesla, which had few EV competitors, the AI startup is operating in a highly saturated market. Though it's valued at around $250 billion, it lags behind OpenAI and Anthropic when it comes to visibility, consumer use, and scale.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-8" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-8" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>Behind closed doors, Musk has expressed frustration with the progress on Grok Imagine, the company's image and video generation tool, and Macrohard, insiders previously told Business Insider.</p><p>Since February, xAI has cut dozens of employees across the Grok Imagine and Macrohard teams and brought in Tesla and SpaceX engineers to help run the company. The <a target="_self" href="https://www.businessinsider.com/xai-macrohard-project-tesla-ai-agent-stalls-2026-3" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/xai-macrohard-project-tesla-ai-agent-stalls-2026-3" cmp-ltrk="post body content" cmp-ltrk-idx="7" mrfobservableid="9eb45d53-72a2-4ff1-8dd2-3e17d0711099">Macrohard project,</a> which saw several leads exit, stalled and has since become a joint project with Tesla, Business Insider previously reported.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-9" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-9" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>In January, cofounder Greg Yang stepped down, while <a target="_self" href="https://www.businessinsider.com/elon-musk-xai-loses-cofounder-tony-wu-2026-2" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/elon-musk-xai-loses-cofounder-tony-wu-2026-2" cmp-ltrk="post body content" cmp-ltrk-idx="8" mrfobservableid="85976238-5614-4713-acda-ff3ed4304cc5">cofounders Tony Wu</a> and Jimmy Ba — whose roles were narrowed — left the following month. Then came Toby Pohlen, who led xAI's computer use team; Zihang Dai, who worked on Grok Code; and <a target="_self" class="" href="https://www.businessinsider.com/xai-cofounders-guodong-zhang-zihang-dai-depart-elon-musk-company-2026-3" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/xai-cofounders-guodong-zhang-zihang-dai-depart-elon-musk-company-2026-3" cmp-ltrk="post body content" cmp-ltrk-idx="9" mrfobservableid="f1c9ad01-95f1-4df8-ad0b-a8e082a049e5">Guodong Zhang</a>, who led Grok Code and Grok Imagine. Manuel Kroiss, who also worked on the coding initiative, left in March.</p>
                  <div class="call-out" data-track-view="{&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;text_only&quot;,&quot;element_name&quot;:&quot;tout_collection&quot;}" data-track-click-shared="{&quot;product_field&quot;:&quot;text_only&quot;,&quot;element_name&quot;:&quot;tout_collection&quot;,&quot;event&quot;:&quot;tout_click&quot;}">
                    <div class="call-out-inner">
                        <h2 class="call-out-heading display-sm">The great cofounder exodus</h2>
                      
                      <div class="call-out-grid">
                          <div class="call-out-row">
                              <article class="call-out-item">
                                <div class="call-out-content">
                                    <div class="call-out-badge label-sm-strong">
                                      Exclusive
                                    </div>
                                  
                                  <h3 class="call-out-title heading-xs">
                                    <a href="/xai-cofounder-ross-nordeen-leaves-musk-preps-spacex-ipo-2026-3" class="call-out-link not-content-link" data-track-click="{&quot;index&quot;:1}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/xai-cofounder-ross-nordeen-leaves-musk-preps-spacex-ipo-2026-3" cmp-ltrk="post body content" cmp-ltrk-idx="0" mrfobservableid="a5251a4e-e72f-4b8c-8b2f-2f1034c9f6ce">
                                      And then there were none: Musk's last xAI cofounder is out
                                    </a>
                                  </h3>
                                </div>
                              </article>
                                <div class="call-out-separator"></div>
                              <article class="call-out-item">
                                <div class="call-out-content">
                                    <div class="call-out-badge label-sm-strong">
                                      Exclusive
                                    </div>
                                  
                                  <h3 class="call-out-title heading-xs">
                                    <a href="/manuel-kroiss-xai-cofounder-departure-elon-musk-2026-3" class="call-out-link not-content-link" data-track-click="{&quot;index&quot;:2}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/manuel-kroiss-xai-cofounder-departure-elon-musk-2026-3" cmp-ltrk="post body content" cmp-ltrk-idx="10" mrfobservableid="2b46755c-aa63-4831-acb8-8f29e65a24d6">
                                      A 10th cofounder is leaving xAI. Elon Musk has just one more left.
                                    </a>
                                  </h3>
                                </div>
                              </article>
                          </div>
                          <div class="call-out-row">
                              <article class="call-out-item">
                                <div class="call-out-content">
                                    <div class="call-out-badge label-sm-strong">
                                      Exclusive
                                    </div>
                                  
                                  <h3 class="call-out-title heading-xs">
                                    <a href="/xai-cofounders-guodong-zhang-zihang-dai-depart-elon-musk-company-2026-3" class="call-out-link not-content-link" data-track-click="{&quot;index&quot;:3}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/xai-cofounders-guodong-zhang-zihang-dai-depart-elon-musk-company-2026-3" cmp-ltrk="post body content" cmp-ltrk-idx="9" mrfobservableid="bd1bffab-844c-4249-950a-724bef846c2f">
                                      The xAI exodus: Two more cofounders leave — and Musk says he's rebuilding
                                    </a>
                                  </h3>
                                </div>
                              </article>
                                <div class="call-out-separator"></div>
                              <article class="call-out-item">
                                <div class="call-out-content">
                                  
                                  <h3 class="call-out-title heading-xs">
                                    <a href="/elon-musk-xai-loses-second-cofounder-jimmy-ba-2026-2" class="call-out-link not-content-link" data-track-click="{&quot;index&quot;:4}" rel="" data-analytics-post-depth="60" data-mrf-link="https://www.businessinsider.com/elon-musk-xai-loses-second-cofounder-jimmy-ba-2026-2" cmp-ltrk="post body content" cmp-ltrk-idx="11" mrfobservableid="e910998a-7208-47c5-8ca2-33f4f44f4e12">
                                      Elon Musk's xAI loses second cofounder in 48 hours
                                    </a>
                                  </h3>
                                </div>
                              </article>
                          </div>
                      </div>
                    </div>
                  </div><p>Even if the cofounders were fired, as Musk appeared to suggest in a <a target="_blank" class="" href="https://x.com/elonmusk/status/2032201568335044978" data-track-click="{&quot;click_type&quot;:&quot;other&quot;,&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;outbound_click&quot;}" rel=" nofollow" data-analytics-post-depth="60" data-mrf-link="https://x.com/elonmusk/status/2032201568335044978" cmp-ltrk="post body content" cmp-ltrk-idx="12" mrfobservableid="0d4ee7b9-474f-41cb-8098-b243f28b78fc">post on X</a>, Elson, the corporate strategy expert, said the potential for him to consolidate power doesn't offset the loss of talent.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-10" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-10" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>"The basis of the firm is not equipment or a patent. It's the intellectual capital of those who put it together," Elson said.</p><p>In the world of AI, talent is one of the most precious assets, prompting fierce poaching battles and astronomical salaries paid to top recruits at some of the biggest players in the industry.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-11" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-11" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>"Companies go to great lengths to recruit that talent and keep those people, " Paul Nary, a mergers and acquisitions expert at the University of Pennsylvania, told Business Insider.</p><p>"The AI talent at the top of xAI is probably the most valuable part of xAI," he said.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-12" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-12" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><h2 id="cc721394-5d50-4947-8f17-402ed6573375" data-toc-id="cc721394-5d50-4947-8f17-402ed6573375">The Musk playbook</h2><p>SpaceX confidentially filed for an IPO with the Securities and Exchange Commission on Wednesday, according to several news outlets, and could reportedly seek a valuation of $1.5 trillion or higher.</p><p>It's poised to be the biggest ever IPO and beat Musk's AI rivals to the stock market.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-13" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-13" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>It's not the first time Musk has taken a company public while under pressure. When he helped take Tesla public in 2010, the EV maker was cash-strapped, and Musk was focused on keeping the company afloat and getting its first mass-market vehicle on the road.</p><p>An engineer who worked at Tesla during that period said executive shuffling was common then. Musk stopped by people's desks on a weekly basis and asked engineers to explain their work, they said.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-14" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-14" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>"If he thought you were full of shit, you were out," they said.</p><p>They recalled flying out to celebrate the IPO, watching Musk pop a bottle of champagne, and flying back to Hawthorne, California, and working later that night.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-15" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-15" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>The IPO "was almost seen as a distraction," they said.</p><p>Executive turnover has remained a theme at Musk's companies, even among acolytes like <a target="_self" href="https://www.businessinsider.com/omead-afshar-executive-tesla-profile-2024-11" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="100" data-mrf-link="https://www.businessinsider.com/omead-afshar-executive-tesla-profile-2024-11" cmp-ltrk="post body content" cmp-ltrk-idx="13" mrfobservableid="0e722b90-d102-4974-a09e-6db961009066">Omead Afshar</a> and <a target="_self" class="" href="https://www.businessinsider.com/tesla-raj-jegannathan-departs-sales-it-vp-2026-2" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="100" data-mrf-link="https://www.businessinsider.com/tesla-raj-jegannathan-departs-sales-it-vp-2026-2" cmp-ltrk="post body content" cmp-ltrk-idx="14" mrfobservableid="99f05a7e-dfb8-4766-aa42-ab27d2835adf">Raj Jegannathan</a>. Now, at xAI, the exodus of cofounders has become a distraction from the SpaceX IPO.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-16" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-16" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>"A lot of people are probably looking at this and saying, 'He's known to do things like this and things still work,'" Pitchbook's Granda said. "But with AI as it stands, I don't know if you could afford to do things like that."</p><p>"Clearly they're trying to get their act together ahead of the IPO, but when you have everyone leave, and you have such limited talent, it's going to be a really tough task."</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-17" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-17" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p>Nary, the M&amp;A expert, said the cofounders' departures ahead of the IPO are far from conventional; typically, companies take steps to prevent top talent from leaving ahead of an IPO. Then again, he noted, Musk himself is an outlier who has been known to surprise skeptics.</p><p>"That's a defining feature — the same rules don't always apply to a Musk company," he said.</p><div class="in-post-sticky  only-desktop"><div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                          <div data-bi-ad="" id="gpt-post-tech-in_content_4_plus-desktop-18" class="ad ad-wrapper fluid in-post only-desktop" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/in-content-4-plus/tech" data-region="in-content-4-plus" data-responsive="[{&quot;browserLimit&quot;:[0,0],&quot;slotSize&quot;:[[300,600],[300,50],[300,250],[320,100],[320,50],[320,480],[6,1],&quot;fluid&quot;]},{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[728,90],[300,250],[800,480],[600,480],&quot;fluid&quot;]}]" data-tile-order="tile-18" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/in-content-4-plus/tech&quot;,&quot;region&quot;:&quot;in-content-4-plus&quot;,&quot;dvp_spos&quot;:&quot;in-content-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted=""></div>
                        </div></div><p><em>Do you work at xAI or have a tip? Contact this reporter via email at </em><a target="_blank" href="mailto:gkay@businessinsider.com" data-track-click="{&quot;click_type&quot;:&quot;other&quot;,&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;outbound_click&quot;}" rel=" nofollow" data-analytics-post-depth="100"><em>gkay@businessinsider.com</em></a><em> or Signal at 248-894-6012. Use a personal email address, a nonwork device, and nonwork WiFi; </em><a target="_self" href="https://www.businessinsider.com/insider-guide-to-securely-sharing-whistleblower-information-about-powerful-institutions-2021-10" data-track-click="{&quot;element_name&quot;:&quot;body_link&quot;,&quot;event&quot;:&quot;tout_click&quot;,&quot;index&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;}" rel="" data-analytics-post-depth="100" data-mrf-link="https://www.businessinsider.com/insider-guide-to-securely-sharing-whistleblower-information-about-powerful-institutions-2021-10" cmp-ltrk="post body content" cmp-ltrk-idx="15" mrfobservableid="d158d071-2931-4dbd-b723-5bb95ebe376c">here's our guide to sharing information securely</a><em>.</em></p>
                  
                  
                  </section>
                  
                  
                  
                  
                  
                  
        </div>
    
    
    
    
      </section>

    
    <!-- Included desktop "post-aside" -->  <section class="post-aside grid-area-post-aside" data-component-type="post-aside" data-load-strategy="exclude">
        
        
        
            <aside class="rail with-default-image has-video-ad component-loaded" id="l-rightrail" data-component-type="rail">
              <section data-rail="" data-track-page-area="RR" class="">
                    <div class="rail-container container-0">
                      
                      
                      <div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                              <div data-bi-ad="" id="gpt-post-tech-rail_1-desktop-1" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="1" data-type="ad" data-adunit="businessinsider.desktop/post/rail-1/tech" data-region="rail-1" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[300,600]]}]" data-tile-order="tile-0" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-1/tech&quot;,&quot;region&quot;:&quot;rail-1&quot;,&quot;dvp_spos&quot;:&quot;rail-1&quot;}" data-not-lazy="" data-enable-ad-refresher="true" data-refresh-count="1" data-ad-adjusted="" data-loaded-method="non-lazy" data-flow="doubleverify.success,amazon.success,rubicon.success,gam.requested" data-google-query-id="CJSqvozz1JMDFZYarAAdpisRdQ" data-ad-refresher-config="{&quot;isEmpty&quot;:false,&quot;curSize&quot;:[1,1],&quot;region&quot;:&quot;rail-1&quot;}" data-viewable="false" data-timer="27"><div id="google_ads_iframe_/4442842/businessinsider.desktop/post/rail-1/tech_0__container__" style="border: 0pt none;"><iframe id="google_ads_iframe_/4442842/businessinsider.desktop/post/rail-1/tech_0" name="google_ads_iframe_/4442842/businessinsider.desktop/post/rail-1/tech_0" title="3rd party ad content" width="300" height="250" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" aria-label="Advertisement" tabindex="-1" allow="private-state-token-redemption;attribution-reporting" data-load-complete="true" data-google-container-id="2" style="border: 0px; vertical-align: bottom;"></iframe></div></div>
                            </div>  </div>
                    <div class="rail-container video-ad-container">
                      
                      
                      <div class="post-recommended-video" data-component-type="post-recommended-video" data-load-strategy="exclude">
                        <h3 class="header display-xs">Recommended video</h3>
                        <div id="jw-strategy-player" class="ad psuedo-ad" data-bi-ad="">
                          <div id="player-container-XqOVG7Ek" data-component-type="video" class="jw-strategy-video component-loaded player-initialized" data-type="video" data-video-player="" data-media-id="eLjmMjbu" data-title="Why Tesla is at a tipping point" data-advertising="enabled" data-region="rail" data-render-thumbnail="true" data-id="eLjmMjbu" data-enabled="true" data-placement-id="XqOVG7Ek" data-events="disabled" data-preroll="4442842/businessinsider.desktop/post/pre-roll-rail/tech" data-midroll="" data-track-element="rail_video">
                            <div class="video-container"><script src="https://cdn.jwplayer.com/v2/sites/iAgve7lW/placements/XqOVG7Ek/embed.js"></script><div id="jwPlacementDiv_XqOVG7Ek" data-jw-placement-id="XqOVG7Ek"><div id="jwExperienceDiv_120rt0e1s49j"><cnx class="cnx-main-container cnx-in-desktop cnx-el cnx-right-rail cnx-mod-no-height" id="a9c3879cb16648d082393d4977a388e6"><cnx class="cnx-content-frame cnx-size-responsive"><cnx class="cnx-ratio" style="padding-bottom: 56.25%;"></cnx><cnx class="cnx-content-wrapper"><cnx class="cnx-video-container"></cnx></cnx></cnx></cnx></div></div></div>
                          </div>  </div>
                      </div>
                    </div>
                      <div class="rail-container">
                        
                        
                        <div class="ad-callout-wrapper ad-label headline-medium only-desktop">
                                <div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1" class="ad ad-wrapper fluid only-desktop is-collapsible height-250" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-2/tech" data-region="rail-2" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-0" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-2/tech&quot;,&quot;region&quot;:&quot;rail-2&quot;,&quot;dvp_spos&quot;:&quot;rail-2&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-loaded-method="lazy" data-flow="doubleverify.success,amazon.success,rubicon.success,gam.requested" data-google-query-id="CNqEwI3z1JMDFSQirAAdnasYpA" data-ad-refresher-config="{&quot;isEmpty&quot;:false,&quot;curSize&quot;:[300,250],&quot;region&quot;:&quot;rail-2&quot;}"><div id="google_ads_iframe_/4442842/businessinsider.desktop/post/rail-2/tech_0__container__" style="border: 0pt none;"><iframe id="google_ads_iframe_/4442842/businessinsider.desktop/post/rail-2/tech_0" name="google_ads_iframe_/4442842/businessinsider.desktop/post/rail-2/tech_0" title="3rd party ad content" width="300" height="250" scrolling="no" marginwidth="0" marginheight="0" frameborder="0" aria-label="Advertisement" tabindex="-1" allow="private-state-token-redemption;attribution-reporting" data-load-complete="true" data-google-container-id="5" style="border: 0px; vertical-align: bottom; width: 300px; height: 250px;" attention-creative-id="58d7aa3a-2972-4f17-95c5-3b60306ec464"></iframe></div></div>
                              </div>  </div><div class="rail-container container-2"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_0" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-3/tech" data-region="rail-3" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-1" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-3/tech&quot;,&quot;region&quot;:&quot;rail-3&quot;,&quot;dvp_spos&quot;:&quot;rail-3&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="3"></div></div></div><div class="rail-container container-3"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_1" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-2" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="4"></div></div></div><div class="rail-container container-4"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_2" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-3" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="5"></div></div></div><div class="rail-container container-5"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_3" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-4" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="6"></div></div></div><div class="rail-container container-6"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_4" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-5" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="7"></div></div></div><div class="rail-container container-7"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_5" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-6" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="8"></div></div></div><div class="rail-container container-8"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_6" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-7" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="9"></div></div></div><div class="rail-container container-9"><div class="ad-callout-wrapper ad-label headline-medium"><div data-bi-ad="" id="gpt-post-tech-rail_2-desktop-1_dynamic_7" class="ad ad-wrapper fluid  only-desktop is-collapsible" data-force="" data-type="ad" data-adunit="businessinsider.desktop/post/rail-4-plus/tech" data-region="rail-4-plus" data-responsive="[{&quot;browserLimit&quot;:[728,0],&quot;slotSize&quot;:[[300,250],[2,2]]}]" data-tile-order="tile-8" data-targeting="{&quot;adunit&quot;:&quot;businessinsider.desktop/post/rail-4-plus/tech&quot;,&quot;region&quot;:&quot;rail-4-plus&quot;,&quot;dvp_spos&quot;:&quot;rail-4-plus&quot;}" data-enable-destroy-slots="true" data-enable-ad-refresher="true" data-refresh-count="0" data-ad-adjusted="" data-buffer="155" data-occurrence="10"></div></div></div>
              </section>
            </aside>
            </section>

    
      
      <section class="post-bottom grid-area-post-bottom" data-component-type="post-bottom" data-load-strategy="exclude" data-track-marfeel="post-bottom" data-mrf-recirculation="post bottom">
        <section class="post-bottom-more">
    
    
          
          
          
          <div class="post-category-tags" data-component-type="post-category-tags" data-load-strategy="lazy" data-track-marfeel="post-category-tags" data-mrf-recirculation="post category tags">
            <ul class="post-category-tags-list headline-semibold is-truncated" data-track-click-shared="{&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;event&quot;:&quot;navigation&quot;,&quot;element_name&quot;:&quot;category_link&quot;}">
                
                <li class="post-category-tag">
                  <a data-track-click="" href="/category/elon-musk" title="Elon Musk" class="post-category-link" data-mrf-link="https://www.businessinsider.com/category/elon-musk" cmp-ltrk="post category tags" cmp-ltrk-idx="0" mrfobservableid="5e79ef87-2f3e-4cfe-80a7-bae71dce326f">Elon Musk</a>
                </li>      
                <li class="post-category-tag">
                  <a data-track-click="" href="/category/spacex" title="SpaceX" class="post-category-link" data-mrf-link="https://www.businessinsider.com/category/spacex" cmp-ltrk="post category tags" cmp-ltrk-idx="1" mrfobservableid="1cb40381-9dc1-4bce-ba46-9238465738a6">SpaceX</a>
                </li>      
                <li class="post-category-tag">
                  <a data-track-click="" href="/category/ipo" title="IPO" class="post-category-link" data-mrf-link="https://www.businessinsider.com/category/ipo" cmp-ltrk="post category tags" cmp-ltrk-idx="2" mrfobservableid="aabc1578-560f-47e3-a264-65ee39561bc9">IPO</a>
                </li>
                <li class="post-category-tag post-category-more">
                  <span class="post-category-link post-category-link-more" data-track-click="{&quot;click_text&quot;:&quot;More&quot;,&quot;click_path&quot;:&quot;bi_value_unassigned&quot;}" role="button" tabindex="0">More <svg class="svg-icon plus-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
            <path fill="currentColor" d="M14.006 2H9.994v7.994H2v4.012h7.994V22h4.012v-7.994H22V9.994h-7.994V2Z"></path>
          </svg></span>
                </li>
          
            </ul>
          </div>
    
    
            
              
              
              <section class="dad-related-posts-component at-post-bottom related-posts standard" data-component-type="dad-related-posts" data-delay-third-party-scripts="true" data-size="4" data-min-size="3" data-container-index="" data-included-verticals="tech" data-placement="post-bottom" data-track-marfeel="dad-related-posts-post-bottom" data-excluded-verticals="bi-video" data-root-margin="250px 0px" data-track-view="{&quot;element_name&quot;:&quot;end_of_article_recirc&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;}" data-mrf-recirculation="related posts bottom">
                  <div class="content-recommendations-title-container">
                    <h2 class="content-recommendations-title display-xs ignore-typography">
                      Read next
                    </h2>
                  </div>
            
            
                <div class="dad-related-posts-container" data-track-click-shared="{&quot;element_name&quot;:&quot;end_of_article_recirc&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;click_text&quot;:&quot;Read next&quot;,&quot;event&quot;:&quot;tout_click&quot;}">
                    <div class="related-posts-container">
                      
                      
                      
                      <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal as-placeholder with-ungrouped-text" data-post-id="post" data-mrf-layout="">
                       
                          
                            <span class="tout-image">        <div class="lazy-holder lazy-holder-4x3  ">
                                
                                
                                <img class="lazy-image js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/logos/placeholder.png" alt="" data-mrf-layout-img="">
                                
                                <noscript>
                                    <img class="no-script" src="/public/assets/logos/placeholder.png" />
                                </noscript>
                                
                                </div></span>
                        
                      
                      
                          <h3 class="tout-title font-weight-garnett-500">
                            <span class="tout-title-link" data-mrf-layout-anchor="" data-mrf-layout-title="">Business Insider tells the innovative stories you want to know</span>
                          </h3>
                      
                      
                      
                      </article>
                      
                      
                      
                      <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal as-placeholder with-ungrouped-text" data-post-id="post" data-mrf-layout="">
                       
                          
                            <span class="tout-image">        <div class="lazy-holder lazy-holder-4x3  ">
                                
                                
                                <img class="lazy-image js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/logos/placeholder.png" alt="" data-mrf-layout-img="">
                                
                                <noscript>
                                    <img class="no-script" src="/public/assets/logos/placeholder.png" />
                                </noscript>
                                
                                </div></span>
                        
                      
                      
                          <h3 class="tout-title font-weight-garnett-500">
                            <span class="tout-title-link" data-mrf-layout-anchor="" data-mrf-layout-title="">Business Insider tells the innovative stories you want to know</span>
                          </h3>
                      
                      
                      
                      </article>
                      
                      
                      
                      <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal as-placeholder with-ungrouped-text" data-post-id="post" data-mrf-layout="">
                       
                          
                            <span class="tout-image">        <div class="lazy-holder lazy-holder-4x3  ">
                                
                                
                                <img class="lazy-image js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/logos/placeholder.png" alt="" data-mrf-layout-img="">
                                
                                <noscript>
                                    <img class="no-script" src="/public/assets/logos/placeholder.png" />
                                </noscript>
                                
                                </div></span>
                        
                      
                      
                          <h3 class="tout-title font-weight-garnett-500">
                            <span class="tout-title-link" data-mrf-layout-anchor="" data-mrf-layout-title="">Business Insider tells the innovative stories you want to know</span>
                          </h3>
                      
                      
                      
                      </article>
                      
                      
                      
                      <article data-component-type="tout" data-load-strategy="exclude" class="tout as-horizontal as-placeholder with-ungrouped-text" data-post-id="post" data-mrf-layout="">
                       
                          
                            <span class="tout-image">        <div class="lazy-holder lazy-holder-4x3  ">
                                
                                
                                <img class="lazy-image js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/logos/placeholder.png" alt="" data-mrf-layout-img="">
                                
                                <noscript>
                                    <img class="no-script" src="/public/assets/logos/placeholder.png" />
                                </noscript>
                                
                                </div></span>
                        
                      
                      
                          <h3 class="tout-title font-weight-garnett-500">
                            <span class="tout-title-link" data-mrf-layout-anchor="" data-mrf-layout-title="">Business Insider tells the innovative stories you want to know</span>
                          </h3>
                      
                      
                      
                      </article>
                    </div>
                </div>
              </section>
        </section>
    
    
          <section class="post-bottom-taboola" data-track-page-area="Post Bottom">
          <!-- Included desktop "taboola" -->    <vendor-taboola class="component taboola js-only-desktop component-loaded" data-component-type="vendor-taboola" data-root-margin="0px 0px 100% 0px" data-consent="MARKETING" config="{&quot;providerName&quot;:&quot;taboola&quot;,&quot;providerPageType&quot;:{&quot;article&quot;:&quot;auto&quot;},&quot;providerUrl&quot;:&quot;//cdn.taboola.com/libtrc/businessinsider/loader.js&quot;,&quot;providerFlushValue&quot;:{&quot;flush&quot;:true},&quot;providerData&quot;:{&quot;mode&quot;:&quot;thumbs-1r&quot;,&quot;container&quot;:&quot;taboola-below-main-column&quot;,&quot;placement&quot;:&quot;below-main-column&quot;,&quot;onlyOn&quot;:&quot;desktop&quot;,&quot;target_type&quot;:&quot;mix&quot;}}" data-load-strategy="content-wall-decision-defer">
                <section class="taboola-container targeted-recommended only-desktop taboola-below-main-column trc_related_container tbl-feed-container render-late-effect tbl-feed-frame-NONE" id="taboola-below-main-column" data-e2e-name="taboola-below-main-column" data-track-event-label="rec-taboola-taboola-below-main-column" data-feed-container-num="1" data-feed-main-container-id="taboola-below-main-column" data-parent-placement-name="below-main-column" data-pub-lang="en" tbl-data-mutation-observer="true"><div id="taboola-below-main-column-sca1" tbl-feed-card="" data-card-index="1" class="trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_above-the-feed-premium-card-fp-delta above-the-feed-placement" data-placement-name="below-main-column | Injected 1" style="padding: 0px; margin: 0px; transform: translateX(0px);"></div><div class="tbl-feed-header tbl-logo-right-position"><div class="tbl-feed-header-logo"></div></div><div id="taboola-below-main-column-pl1" tbl-feed-card="" data-card-index="1" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_thumbs-feed-01-2" data-placement-name="below-main-column | Card 1" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_1036474236" class="trc_rbox thumbs-feed-01-2 trc-content-sponsored" style="overflow: hidden;"><div id="trc_header_1036474236" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_1036474236" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_1036474236"><div data-item-id="~~V1~~1342818917286698678~~qzucQMosZTQ_J8vTug89Y8amVhJ6srxkCZalRbVAxRQe79Ni-eBnd8iQ4KmvvX-QCoTT_IvWFG7RTbSa_z-XXmMavJ7AAPT1kgsUVaf3zF3pPm2-C7vAtwBG4o6ZuNPakh_AWjb28e4PT5EUm4u_bhoTeIrt5sx_ydDi9n2STzFAMnhVesYHQiOZp4ftik8_2EvOXtL2EY47MTgPJ-axBo6ROsMGkMFSoVsudHTeIrQ" data-item-title="10 Stocks in the Defense Spending Boom" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/GETTY_IMAGES/FKF/2161447160__IYNnH2iq.jpg" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-default textItem thumbnail_top videoCube_1_child syndicatedItem trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://seekingalpha.com/article/4877761-top-10-defense-stocks-as-mideast-conflict-escalates" attributionsrc="" slot="thumbnail" data-mrf-link="https://seekingalpha.com/article/4877761-top-10-defense-stocks-as-mideast-conflict-escalates" cmp-ltrk="post bottom" cmp-ltrk-idx="0" mrfobservableid="4db1d5f6-0548-473f-86fe-4db7d28c8a92"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="10 Stocks in the Defense Spending Boom" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="https://seekingalpha.com/article/4877761-top-10-defense-stocks-as-mideast-conflict-escalates" attributionsrc="" data-mrf-link="https://seekingalpha.com/article/4877761-top-10-defense-stocks-as-mideast-conflict-escalates" cmp-ltrk="post bottom" cmp-ltrk-idx="0" mrfobservableid="33c37637-a4b7-482f-b311-97b521321d07"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">10 Stocks in the Defense Spending Boom</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="Seeking Alpha in Taboola advertising section" class="branding-inner inline-branding">Seeking Alpha</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 1:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%201:" cmp-ltrk="post bottom" cmp-ltrk-idx="1" mrfobservableid="137f6068-f7df-4c51-b794-6cf35ff16f58"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 1:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%201:" cmp-ltrk="post bottom" cmp-ltrk-idx="1" mrfobservableid="91d42f1d-832c-45a4-85e4-4d532510d9f2"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Read More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div><div data-item-id="~~V1~~-5354678294134894878~~bHNXO7Vop_S54okO2PKvBnC88WqRNvaNGfvBSzO-jYLl2Pd8jhX1mcBq2z36y_es_q5PlPdAYTk5IAKRk_FmUb-qpFhaCdUEAMCZ39CDlZqPF8C2yPvlmbo_NIFLjI3J1cTA7c4YyVLp1OZJwq262qHfR3SjSzbLyBNlwd1NCpx8BNMVGPNcn9ZBvKI54gw4" data-item-title="10 High-Yield Dividend Stocks for March" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/be596e550dd5aa9c489ccedf2d2765ff.png" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-default textItem thumbnail_top videoCube_2_child syndicatedItem trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://seekingalpha.com/article/4876802-top-10-high-yield-dividend-stocks-for-march-2026" attributionsrc="" slot="thumbnail" data-mrf-link="https://seekingalpha.com/article/4876802-top-10-high-yield-dividend-stocks-for-march-2026" cmp-ltrk="post bottom" cmp-ltrk-idx="2" mrfobservableid="72df3636-9d18-4bf3-a757-ae0a688ab717"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="10 High-Yield Dividend Stocks for March" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="https://seekingalpha.com/article/4876802-top-10-high-yield-dividend-stocks-for-march-2026" attributionsrc="" data-mrf-link="https://seekingalpha.com/article/4876802-top-10-high-yield-dividend-stocks-for-march-2026" cmp-ltrk="post bottom" cmp-ltrk-idx="2" mrfobservableid="defc1189-396d-44ee-bcdd-73605af04366"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">10 High-Yield Dividend Stocks for March</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="Seeking Alpha in Taboola advertising section" class="branding-inner inline-branding">Seeking Alpha</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 1:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%201:" cmp-ltrk="post bottom" cmp-ltrk-idx="1" mrfobservableid="0eb55b3b-ca60-4ee6-b229-4a1029f4ceae"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 1:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%201:" cmp-ltrk="post bottom" cmp-ltrk-idx="1" mrfobservableid="477ed87c-8245-4bc1-8029-64f5679eb9c9"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Read More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl2" tbl-feed-card="" data-card-index="2" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_thumbs-feed-01" data-placement-name="below-main-column | Card 2" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_2551383606" class="trc_rbox thumbs-feed-01 trc-content-sponsored" style="overflow: hidden;"><div id="trc_header_2551383606" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_2551383606" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_2551383606"><div data-item-id="~~V1~~-959212193625380084~~7scR3uBzNg4oM8f848t1u_HGLOmyLmC5UC5fBlWVNxpw6cLzOYgYTH58zK8cIqqStHtCtQ9dESIYG_CBVnP4mSPO6UOL3l_dAo3hyefoS3jHS-H9N4H-q_rC1QD0vwguRdbgwlJdnqyroTPEQNNEnyMfv8YWG2bAXqa5oXQiYjlufPt9N6tgEzbVg0jG8BJxJQ5sT_0Qol2GtrAmnvpRTxJkmwXekRVQRG60CLuZ7_G6rXzQfT0owwZYoOtr28H3" data-item-title="A Chinese AI Breakthrough Is Raising New Questions" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/062c6c85515b967bcabbe7425286a9e3.png" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child syndicatedItem trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://go.finance-compare.com/4dcdc651-490b-4154-8c58-a0f805c34162" attributionsrc="" slot="thumbnail" data-mrf-link="https://go.finance-compare.com/4dcdc651-490b-4154-8c58-a0f805c34162" cmp-ltrk="post bottom" cmp-ltrk-idx="3" mrfobservableid="7d5bb0ff-6c10-4b78-bd40-f75a94af61c6"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="A Chinese AI Breakthrough Is Raising New Questions" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="https://go.finance-compare.com/4dcdc651-490b-4154-8c58-a0f805c34162" attributionsrc="" data-mrf-link="https://go.finance-compare.com/4dcdc651-490b-4154-8c58-a0f805c34162" cmp-ltrk="post bottom" cmp-ltrk-idx="3" mrfobservableid="b808744a-47da-4d82-943f-088ecdfa84ec"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 1;">A Chinese AI Breakthrough Is Raising New Questions</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="finance-compare.com in Taboola advertising section" class="branding-inner inline-branding">finance-compare.com</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 2:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%202:" cmp-ltrk="post bottom" cmp-ltrk-idx="4" mrfobservableid="ed7893aa-270d-4596-942d-01c62829ecf1"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 2:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%202:" cmp-ltrk="post bottom" cmp-ltrk-idx="4" mrfobservableid="236a6463-b2b1-4735-a475-3b4e4bf8601c"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Learn More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl3" tbl-feed-card="" data-card-index="3" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_thumbs-feed-01-2" data-placement-name="below-main-column | Card 3" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_4355548321" class="trc_rbox thumbs-feed-01-2 trc-content-sponsored" style="overflow: hidden;"><div id="trc_header_4355548321" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_4355548321" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_4355548321"><div data-item-id="~~V1~~-7716715652726136465~~_9Ywdz4c-4lsmLbce0AgL8FVbPJWtFyrJ9aLG1Opao5ZsizMzuSpeYXmXGCxAG7P3aoogmtI0n8idYo9N9hyDOLxD3GvAJFX3VOIPfQmIucw6uvtyS2u2BHsuIzSKfhtoe9fEEBpKzK5ls1ZSQq77rVUOZmf7UqEpIhuB3SflmVNLwxq7HaNYLWBFTefHkDuq01L1lyiugWeh_u3PWbwNa-1nefi1JFZpAK_m4CW8lAGl4VyGUMVvYyzUeSg5yxKHmV1Z-ze7r4e6uD3SlQXbA" data-item-title="North York Locals Try A New Way To Hear [See how]" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/0c70e7f3aa7b6a15f0ab340475c0254d.png" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-default textItem thumbnail_top videoCube_1_child syndicatedItem trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://forms.connecthearing.ca/mvp" attributionsrc="" slot="thumbnail" data-mrf-link="https://forms.connecthearing.ca/mvp" cmp-ltrk="post bottom" cmp-ltrk-idx="5" mrfobservableid="40bbd281-3143-4eb2-aab4-83d4cf1659c5"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="North York Locals Try A New Way To Hear [See how]" target="_blank" class="item-label-href" rel="nofollow noopener sponsored" href="https://forms.connecthearing.ca/mvp" attributionsrc="" data-mrf-link="https://forms.connecthearing.ca/mvp" cmp-ltrk="post bottom" cmp-ltrk-idx="5" mrfobservableid="b6a024a7-efb1-4829-8be7-38747e393d76"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">North York Locals Try A New Way To Hear [See how]</span><span class="video-label video-description" slot="description"></span><span class="branding composite-branding" slot="branding"><span role="link" aria-label="Connect Hearing in Taboola advertising section" class="branding-inner inline-branding">Connect Hearing</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 3:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%203:" cmp-ltrk="post bottom" cmp-ltrk-idx="6" mrfobservableid="05f5f677-cbf5-4c65-aa01-7b1a79c41454"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 3:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%203:" cmp-ltrk="post bottom" cmp-ltrk-idx="6" mrfobservableid="8e67d5d5-13fe-4a76-860e-d4df3236b954"><span>Sponsored</span></a></div></span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div><div data-item-id="~~V1~~2624736046565813347~~JPnbx7OuBRq1g3VHlxIFN8mEWHrrqTA5w8Wan9fbXiQe79Ni-eBnd8iQ4KmvvX-QPtVvJT2oZsUKTcbUlOwtfF7K02ol69sat4Xf5bVlx-rq7A_mptrFvWp9I9fajOvnpxbTEXwhjbiMBkHTXygJrRoTeIrt5sx_ydDi9n2STzHRTbD1iIEdU5mRj1QbWexgOLBleVVGtB2i5X_ldO2_4pWibM8DeUoalu17B0ccu4YRuzzdaXhbUCCxBbsqpGX7" data-item-title="Here's What Gutter Guards Should Cost You In North York&nbsp;" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/4fbd9fcd2045f36ee8a05676f88db835.jpeg" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-default textItem thumbnail_top videoCube_2_child syndicatedItem trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="http://www.mnbasd77.com/aff_c" attributionsrc="" slot="thumbnail" data-mrf-link="http://www.mnbasd77.com/aff_c" cmp-ltrk="post bottom" cmp-ltrk-idx="7" mrfobservableid="dba3552e-2060-4e51-b10f-01ce976731d7"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="Here's What Gutter Guards Should Cost You In North York&nbsp;" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="http://www.mnbasd77.com/aff_c" attributionsrc="" data-mrf-link="http://www.mnbasd77.com/aff_c" cmp-ltrk="post bottom" cmp-ltrk-idx="7" mrfobservableid="89942a00-8d8f-4e57-915f-71d6eaf211b6"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">Here's What Gutter Guards Should Cost You In North York&nbsp;</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="LeafFilter Partner in Taboola advertising section" class="branding-inner inline-branding">LeafFilter Partner</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 3:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%203:" cmp-ltrk="post bottom" cmp-ltrk-idx="6" mrfobservableid="2735ad74-b37b-4a07-a2ad-d5780413e936"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column | Card 3:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01-2:below-main-column%20|%20Card%203:" cmp-ltrk="post bottom" cmp-ltrk-idx="6" mrfobservableid="38e33f2b-91c2-4213-9094-889ae71e9e29"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Learn More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl4" tbl-feed-card="" data-card-index="4" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_thumbs-feed-01" data-placement-name="below-main-column | Card 4" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_9226271838" class="trc_rbox thumbs-feed-01 trc-content-sponsored" style="overflow: hidden;"><div id="trc_header_9226271838" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_9226271838" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_9226271838"><div data-item-id="~~V1~~8102690263876726132~~2ZMlJ5df8qUB_PTIfP3XxZZWGpI7OC0huoD8kZioDbQe79Ni-eBnd8iQ4KmvvX-QCoTT_IvWFG7RTbSa_z-XXlkO_eVpkVoNCCyp9Ou7uSBO8PLL7U1bLpjsxMDkKGS-ttWVPnO3mtFzMw9j4ICrE6rvSNhzvVrnrtt5OkLTgThAMnhVesYHQiOZp4ftik8_4g73Q_bBrW90sRp3JFC-KY6ROsMGkMFSoVsudHTeIrQ" data-item-title="Evergreen principles for liquidity sleeve management" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/c30fc6d022879308065acef615703012.jpg" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child syndicatedItem trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://www.franklintempleton.ca/en-ca/articles/2026/alternatives/evergreen-principles-for-liquidity-sleeve-management" attributionsrc="" slot="thumbnail" data-mrf-link="https://www.franklintempleton.ca/en-ca/articles/2026/alternatives/evergreen-principles-for-liquidity-sleeve-management" cmp-ltrk="post bottom" cmp-ltrk-idx="8" mrfobservableid="8d1496be-2291-4215-8ffb-fb875456148c"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="Evergreen principles for liquidity sleeve management" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="https://www.franklintempleton.ca/en-ca/articles/2026/alternatives/evergreen-principles-for-liquidity-sleeve-management" attributionsrc="" data-mrf-link="https://www.franklintempleton.ca/en-ca/articles/2026/alternatives/evergreen-principles-for-liquidity-sleeve-management" cmp-ltrk="post bottom" cmp-ltrk-idx="8" mrfobservableid="7882536a-c193-48e0-963a-bb0899e159b4"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 1;">Evergreen principles for liquidity sleeve management</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="Franklin Templeton in Taboola advertising section" class="branding-inner inline-branding">Franklin Templeton</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 4:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%204:" cmp-ltrk="post bottom" cmp-ltrk-idx="9" mrfobservableid="551f9151-b9c5-4dfe-bc43-3c3f3ab7af36"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 4:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%204:" cmp-ltrk="post bottom" cmp-ltrk-idx="9" mrfobservableid="d286aca4-2fe3-45d4-9692-0e0d3e89dbfa"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Read More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl5" tbl-feed-card="" data-card-index="5" class="trc_related_container tbl-trecs-container trc_spotlight_widget" style="padding: 0px; margin: 0px;"></div><div id="taboola-below-main-column-pl6" tbl-feed-card="" data-card-index="6" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_organic-thumbs-feed-01-2" data-placement-name="below-main-column | Card 6" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_440953813" class="trc_rbox organic-thumbs-feed-01-2 trc-content-organic" style="overflow: hidden;"><div id="trc_header_440953813" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_440953813" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_440953813"><div data-item-id="~~V1~~697618414756992718~~zCx8I4uR8WQra7rqjf8sAA" data-item-title="I took the same grocery list to Walmart and Costco. When it comes to prices and value, I found a clear winner." data-item-thumb="https://i.insider.com/69cd3313c02a678bd7e46e8e?width=1200&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined photoItem thumbnail_top videoCube_1_child trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/walmart-vs-costco-grocery-shopping-price-comparison-better-review-2026-4" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/walmart-vs-costco-grocery-shopping-price-comparison-better-review-2026-4" cmp-ltrk="post bottom" cmp-ltrk-idx="10" mrfobservableid="480e7d40-5f54-48d1-acfc-7b033d60db17"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="I took the same grocery list to Walmart and Costco. When it comes to prices and value, I found a clear winner." target="_parent" class="item-label-href" href="https://www.businessinsider.com/walmart-vs-costco-grocery-shopping-price-comparison-better-review-2026-4" data-mrf-link="https://www.businessinsider.com/walmart-vs-costco-grocery-shopping-price-comparison-better-review-2026-4" cmp-ltrk="post bottom" cmp-ltrk-idx="10" mrfobservableid="e54b2f64-e41b-4de9-bb4c-61947497add5"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 4;">I took the same grocery list to Walmart and Costco. When it comes to prices and value, I found a clear winner.</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 4;">I brought the same grocery list to Walmart and Costco to see which has better prices and value, thus becoming the best place to buy cheap groceries.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div><div data-item-id="~~V1~~-105954337405272102~~UIWI5xk5GBrW6nsT-RI88w" data-item-title="The HR exec from the viral Coldplay 'Kiss Cam' video says she can't get a job" data-item-thumb="https://i.insider.com/69b9513e4d65ec51752a1e8a?width=1200&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_2_child trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/coldplay-kiss-cam-video-kristin-cabot-cant-get-job-2026-3" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/coldplay-kiss-cam-video-kristin-cabot-cant-get-job-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="11" mrfobservableid="dab835a0-8282-4df6-9da6-fca0d0665795"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="The HR exec from the viral Coldplay 'Kiss Cam' video says she can't get a job" target="_parent" class="item-label-href" href="https://www.businessinsider.com/coldplay-kiss-cam-video-kristin-cabot-cant-get-job-2026-3" data-mrf-link="https://www.businessinsider.com/coldplay-kiss-cam-video-kristin-cabot-cant-get-job-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="11" mrfobservableid="483fdbf9-5cdb-430a-b8a1-15b9ea166649"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 3;">The HR exec from the viral Coldplay 'Kiss Cam' video says she can't get a job</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 3;">Kristin Cabot, former HR executive at Astronomer, said she is struggling to find work after the 'kiss cam' fiasco.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl7" tbl-feed-card="" data-card-index="7" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_thumbs-feed-01" data-placement-name="below-main-column | Card 7" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_9374876533" class="trc_rbox thumbs-feed-01 trc-content-sponsored" style="overflow: hidden;"><div id="trc_header_9374876533" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_9374876533" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_9374876533"><div data-item-id="~~V1~~-2685743826560746473~~H3jKr-k-QVsTk0ty0Woz7ZZWGpI7OC0huoD8kZioDbQe79Ni-eBnd8iQ4KmvvX-QCoTT_IvWFG7RTbSa_z-XXk7mo3o_DWuCv2DPT4s-bO1O8PLL7U1bLpjsxMDkKGS-ttWVPnO3mtFzMw9j4ICrE6rvSNhzvVrnrtt5OkLTgThAMnhVesYHQiOZp4ftik8_4g73Q_bBrW90sRp3JFC-KY6ROsMGkMFSoVsudHTeIrQ" data-item-title="Evaluating Canadian equity implications from Iran conflict" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/IMAGE_UPSCALER/EIU/d693db61-05f0-45b6-ad95-c9a8a01d7018__YyUZfFCP.jpg" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child syndicatedItem trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://www.franklintempleton.ca/en-ca/articles-ca/clearbridge-investments/evaluating-canadian-equity-implications-from-iran-conflict" attributionsrc="" slot="thumbnail" data-mrf-link="https://www.franklintempleton.ca/en-ca/articles-ca/clearbridge-investments/evaluating-canadian-equity-implications-from-iran-conflict" cmp-ltrk="post bottom" cmp-ltrk-idx="12" mrfobservableid="63202b86-8af6-4b11-994e-6f99f812c6b5"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="Evaluating Canadian equity implications from Iran conflict" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="https://www.franklintempleton.ca/en-ca/articles-ca/clearbridge-investments/evaluating-canadian-equity-implications-from-iran-conflict" attributionsrc="" data-mrf-link="https://www.franklintempleton.ca/en-ca/articles-ca/clearbridge-investments/evaluating-canadian-equity-implications-from-iran-conflict" cmp-ltrk="post bottom" cmp-ltrk-idx="12" mrfobservableid="ed2f8369-78cb-453e-b2b9-f6912851db77"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">Evaluating Canadian equity implications from Iran conflict</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="Franklin Templeton in Taboola advertising section" class="branding-inner inline-branding">Franklin Templeton</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 7:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%207:" cmp-ltrk="post bottom" cmp-ltrk-idx="13" mrfobservableid="f21fd7eb-b8cb-48c2-9730-d97e88e18de0"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 7:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%207:" cmp-ltrk="post bottom" cmp-ltrk-idx="13" mrfobservableid="03571108-f87c-4934-9d34-2d140ee1e2e6"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Read More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl8" tbl-feed-card="" data-card-index="8" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_organic-thumbs-feed-01-2" data-placement-name="below-main-column | Card 8" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_6886749754" class="trc_rbox organic-thumbs-feed-01-2 trc-content-organic" style="overflow: hidden;"><div id="trc_header_6886749754" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_6886749754" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_6886749754"><div data-item-id="~~V1~~6795778791213494423~~zCx8I4uR8WQra7rqjf8sAA" data-item-title="The 10-second trick to spot a liar, according to a psychopathy researcher" data-item-thumb="https://i.insider.com/69b0685accda166eed3d1b5a?width=1200&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/10-second-trick-spot-liars-poisonous-people-narcissism-psychopathy-2026-3" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/10-second-trick-spot-liars-poisonous-people-narcissism-psychopathy-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="14" mrfobservableid="16d35676-0bec-48fc-936c-120f33e4c5a2"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="The 10-second trick to spot a liar, according to a psychopathy researcher" target="_parent" class="item-label-href" href="https://www.businessinsider.com/10-second-trick-spot-liars-poisonous-people-narcissism-psychopathy-2026-3" data-mrf-link="https://www.businessinsider.com/10-second-trick-spot-liars-poisonous-people-narcissism-psychopathy-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="14" mrfobservableid="b0d2c710-2bd0-4ace-bb4b-e3e42a69702f"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 3;">The 10-second trick to spot a liar, according to a psychopathy researcher</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 3;">Leanne ten Brinke, a psychologist specializing in dark personalities, shared an easy way to spot lying.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div><div data-item-id="~~V1~~-6213912600768681267~~UIWI5xk5GBrW6nsT-RI88w" data-item-title="Guilty, all counts: Alexander brothers shake their heads 'no' as the verdict is read" data-item-thumb="https://i.insider.com/69ab146afd4fbd083f29ac97?width=1200&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_2_child trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/alexander-brothers-guilty-sex-trafficking-trial-verdict-prison-2026-3" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/alexander-brothers-guilty-sex-trafficking-trial-verdict-prison-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="15" mrfobservableid="ae4b38f8-9a3a-465f-aaed-92a21352c70e"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="Guilty, all counts: Alexander brothers shake their heads 'no' as the verdict is read" target="_parent" class="item-label-href" href="https://www.businessinsider.com/alexander-brothers-guilty-sex-trafficking-trial-verdict-prison-2026-3" data-mrf-link="https://www.businessinsider.com/alexander-brothers-guilty-sex-trafficking-trial-verdict-prison-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="15" mrfobservableid="0bbe1d3e-1a55-4aad-a506-5a6a160b0212"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 3;">Guilty, all counts: Alexander brothers shake their heads 'no' as the verdict is read</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 4;">A federal jury has reached a verdict in the Manhattan trial of three wealthy siblings charged in a decade-long pattern of drugging and raping women.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl9" tbl-feed-card="" data-card-index="9" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_thumbs-feed-01" data-placement-name="below-main-column | Card 9" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_509864604" class="trc_rbox thumbs-feed-01 trc-content-sponsored" style="overflow: hidden;"><div id="trc_header_509864604" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_509864604" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_509864604"><div data-item-id="~~V1~~6258353523447813903~~3FDLMLltpjPmfc3sI0gggcmEWHrrqTA5w8Wan9fbXiQe79Ni-eBnd8iQ4KmvvX-QCoTT_IvWFG7RTbSa_z-XXkNaWEQRVpGuK6Fnl43l06Dq7A_mptrFvWp9I9fajOvnpxbTEXwhjbiMBkHTXygJrRoTeIrt5sx_ydDi9n2STzHRTbD1iIEdU5mRj1QbWexgOLBleVVGtB2i5X_ldO2_4pWibM8DeUoalu17B0ccu4YRuzzdaXhbUCCxBbsqpGX7" data-item-title="Here's What Gutter Guards Should Cost You In North York" data-item-thumb="https://cdn.taboola.com/libtrc/static/thumbnails/b43307884108009771839e186345296b.png" data-item-syndicated="true" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child syndicatedItem trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_blank" class="item-thumbnail-href" rel="nofollow noopener sponsored" href="https://www.mnbasd77.com/aff_c" attributionsrc="" slot="thumbnail" data-mrf-link="https://www.mnbasd77.com/aff_c" cmp-ltrk="post bottom" cmp-ltrk-idx="16" mrfobservableid="66ed7a59-5b62-4e57-a97f-d27c45bd1486"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://www')" class="thumbnail-emblem none"></span></span><div class="videoCube_aspect"></div></div></a><a title="Here's What Gutter Guards Should Cost You In North York" target="_blank" class="item-label-href video-cta-style" rel="nofollow noopener sponsored" href="https://www.mnbasd77.com/aff_c" attributionsrc="" data-mrf-link="https://www.mnbasd77.com/aff_c" cmp-ltrk="post bottom" cmp-ltrk-idx="16" mrfobservableid="1b7bf38e-1dd5-4168-b2ce-27d71963c49e"><span class="video-label-box trc-main-label video-label-box-cta video-label-box-cta-non-ie"><span class="video-label video-title video-label-flex-cta-item trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">Here's What Gutter Guards Should Cost You In North York</span><span class="video-label video-description video-label-flex-cta-item" slot="description"></span><span class="branding composite-branding video-branding-flex-cta-item" slot="branding"><span role="link" aria-label="LeafFilter Partner in Taboola advertising section" class="branding-inner inline-branding">LeafFilter Partner</span><span class="branding-separator"> | </span><div class="logoDiv link-disclosure attribution-disclosure-link-sponsored align-disclosure-left"><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 9:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_desktop_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%209:" cmp-ltrk="post bottom" cmp-ltrk-idx="17" mrfobservableid="1cae392d-9c14-4bf1-8b87-6b66e5c17b50"><span>Sponsored</span></a><a href="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column | Card 9:" rel="nofollow sponsored noopener" target="_blank" aria-label="Sponsored: learn about this recommendation (opens dialog)" class="trc_mobile_disclosure_link trc_attribution_position_after_branding" data-mrf-link="https://popup.taboola.com/en/?template=colorbox&amp;utm_source=businessinsider&amp;utm_medium=referral&amp;utm_content=thumbs-feed-01:below-main-column%20|%20Card%209:" cmp-ltrk="post bottom" cmp-ltrk-idx="17" mrfobservableid="ca0d78d8-47b5-40cd-8b40-6bbf399b5602"><span>Sponsored</span></a></div></span><div class="video-cta-href"><button type="button" class="video-cta-button video-cta-style" style="font-family: Garnett; color: rgb(10, 10, 10); border-color: rgb(10, 10, 10);">Learn More</button></div></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl10" tbl-feed-card="" data-card-index="10" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_organic-thumbs-feed-01-2" data-placement-name="below-main-column | Card 10" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_372942787" class="trc_rbox organic-thumbs-feed-01-2 trc-content-organic" style="overflow: hidden;"><div id="trc_header_372942787" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_372942787" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_372942787"><div data-item-id="~~V1~~489255480737371612~~zCx8I4uR8WQra7rqjf8sAA" data-item-title="The missing voice in the debate over Jeffrey Epstein's death is found in the Epstein files" data-item-thumb="https://i.insider.com/69acf200d3e2f1aef36a322b?width=1200&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/jeffrey-epstein-death-autopsy-doctor-explains-delayed-suicide-ruling-2026-3" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/jeffrey-epstein-death-autopsy-doctor-explains-delayed-suicide-ruling-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="18" mrfobservableid="8419aced-8b95-49c7-a542-3df3857dc1ff"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="The missing voice in the debate over Jeffrey Epstein's death is found in the Epstein files" target="_parent" class="item-label-href" href="https://www.businessinsider.com/jeffrey-epstein-death-autopsy-doctor-explains-delayed-suicide-ruling-2026-3" data-mrf-link="https://www.businessinsider.com/jeffrey-epstein-death-autopsy-doctor-explains-delayed-suicide-ruling-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="18" mrfobservableid="98e36551-aab5-45f3-a3d6-eba3c0d75827"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 3;">The missing voice in the debate over Jeffrey Epstein's death is found in the Epstein files</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 4;">The Epstein files include a never-before-seen interview with the doctor who conducted the autopsy on Jeffrey Epstein.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div><div data-item-id="~~V1~~-6697180479758992095~~UIWI5xk5GBrW6nsT-RI88w" data-item-title="I've been on over 25 cruises. There are 3 things I never bother packing." data-item-thumb="https://i.insider.com/69c158b25b58f1f0f9336340?width=1200&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_2_child trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/things-never-bring-cruises-frequent-traveler-packing-2026-3" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/things-never-bring-cruises-frequent-traveler-packing-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="19" mrfobservableid="17d94e6b-2712-42a6-971b-bdead8f9b071"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="I've been on over 25 cruises. There are 3 things I never bother packing." target="_parent" class="item-label-href" href="https://www.businessinsider.com/things-never-bring-cruises-frequent-traveler-packing-2026-3" data-mrf-link="https://www.businessinsider.com/things-never-bring-cruises-frequent-traveler-packing-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="19" mrfobservableid="9695b3c8-9117-4c1b-8219-7e2959265b97"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">I've been on over 25 cruises. There are 3 things I never bother packing.</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 4;">After going on many cruises, there are several things I never pack so I don't waste space or break onboard rules, from formal wear to flat irons.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div id="taboola-below-main-column-pl11" tbl-feed-card="" data-card-index="11" class="tbl-feed-card trc_related_container tbl-trecs-container trc_spotlight_widget trc_elastic trc_elastic_organic-thumbs-feed-01-a" data-placement-name="below-main-column | Card 11" style="padding: 0px;"><div class="trc_rbox_container"><div><div id="trc_wrapper_2615797561" class="trc_rbox organic-thumbs-feed-01-a trc-content-organic" style="overflow: hidden;"><div id="trc_header_2615797561" class="trc_rbox_header trc_rbox_border_elm"><div class="trc_header_ext"></div><span role="heading" aria-level="3" class="trc_rbox_header_span"></span></div><div id="outer_2615797561" class="trc_rbox_outer"><div id="rbox-t2v" class="trc_rbox_div trc_rbox_border_elm"><div id="internal_trc_2615797561"><div data-item-id="~~V1~~7660805329500203335~~zCx8I4uR8WQra7rqjf8sAA" data-item-title="Sarah Michelle Gellar says one detail at home has helped her marriage last 23 years" data-item-thumb="https://i.insider.com/69bb5b1a75bee4e0ee55ddd8?width=1024&amp;format=jpeg" data-item-syndicated="false" class="videoCube trc_spotlight_item origin-undefined textItem thumbnail_top videoCube_1_child trc-first-recommendation trc-spotlight-first-recommendation trc_excludable"><a target="_parent" class="item-thumbnail-href" href="https://www.businessinsider.com/sarah-michelle-gellar-tip-avoid-marital-conflict-relationship-freddie-prinze-2026-3" slot="thumbnail" data-mrf-link="https://www.businessinsider.com/sarah-michelle-gellar-tip-avoid-marital-conflict-relationship-freddie-prinze-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="20" mrfobservableid="1ee8e052-395e-4472-b7d0-6dad8c32ae6e"><div class="thumbBlock_holder"><span role="img" aria-label="Image for Taboola Advertising Unit" class="thumbBlock"><span class="thumbnail-overlay"></span><span style="background-image: url('https://cdn.taboola.com/static/37/37910250-e8b8-49dd-a9f3-2a449facca30.svg')" class="thumbnail-emblem bottom-left"></span></span><div class="videoCube_aspect"></div></div></a><a title="Sarah Michelle Gellar says one detail at home has helped her marriage last 23 years" target="_parent" class="item-label-href" href="https://www.businessinsider.com/sarah-michelle-gellar-tip-avoid-marital-conflict-relationship-freddie-prinze-2026-3" data-mrf-link="https://www.businessinsider.com/sarah-michelle-gellar-tip-avoid-marital-conflict-relationship-freddie-prinze-2026-3" cmp-ltrk="post bottom" cmp-ltrk-idx="20" mrfobservableid="5e9cb848-0e8c-4c28-a165-78742318e601"><span class="video-label-box trc-main-label"><span class="video-label video-title trc_ellipsis" role="link" slot="title" style="-webkit-line-clamp: 2;">Sarah Michelle Gellar says one detail at home has helped her marriage last 23 years</span><span class="video-label video-description trc_ellipsis" slot="description" style="-webkit-line-clamp: 2;">Sarah Michelle Gellar says this setup "stops a lot of petty fighting" in her marriage to Freddie Prinze Jr.</span><span class="branding" slot="branding" aria-label="Business Insider in Taboola advertising section" role="link">Business Insider</span></span></a><div title="Remove this item" class="trc_user_exclude_btn"></div><div class="trc_exclude_overlay trc_fade"></div><div class="trc_exclude_undo_btn">Undo</div></div></div></div></div><div class="trc_clearer"></div></div></div></div></div><div class="tbl-batch-anchor"></div><div class="tbl-loading-spinner tbl-hidden"></div><div id="_cm-css-reset" class="_cm-ad-feed-manager vpaid-player-container multi-vpaids" style="width: 700px; height: 0px; position: absolute; top: 2342px; left: 0px; z-index: 1;"><div id="_cm-iframes-wrapper" class="iframes-wrapper" style="display: none;"></div><div class="_cm-ad-feed-manager vpaid-player-container multi-vpaids vpaid-handler" id="0__cm-css-reset" style="width: 700px; height: 0px; position: absolute; top: 0px; left: 0px; border: 0px; z-index: 0;"></div></div><div id="1775329859453" class="_cm-ad-feed-manager" style="width: 700px; height: 0px; position: absolute; top: 2342px; left: 0px; z-index: 1;"></div></section>
              </vendor-taboola>
          
          <!-- Excluded mobile "taboola" --></section>
    
      </section>
  </section>

  <div class="pw-modal-entry"></div>
  <div class="pw-modal-backdrop"></div>

      <div data-component-type="paywall" data-load-strategy="exclude" data-content-selector="[data-content-container]" class="component-loaded">
      </div>

  <back-to-home class="component back-to-home" data-component-type="back-to-home" data-load-strategy="defer" data-only-on="mobile">
    
    
    <div class="col-12">
      <section class="back-to-home-container">
        <div class="back-to-home">
          <a class="back-to-home-link headline-semibold" href="/" data-track-click="{&quot;click_text&quot;:&quot;Home&quot;,&quot;click_path&quot;:&quot;/&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;element_name&quot;:&quot;back_to_hp&quot;,&quot;event&quot;:&quot;navigation&quot;}">
            <svg class="svg-icon chevron-left-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
              <path fill="currentColor" fill-rule="evenodd" d="m18.5 19.44-7.72-7.486 7.626-7.394L15.766 2 5.5 11.954 15.86 22l2.64-2.56Z"></path>
            </svg>          <span class="back-to-home-text headline-semibold">HOME</span>
          </a>
  
            <a class="back-to-home-subscribe-link headline-semibold" href="https://www.businessinsider.com/subscription" title="Subscribe" data-track-click="{&quot;click_text&quot;:&quot;subscribe&quot;,&quot;click_path&quot;:&quot;/subscribe&quot;,&quot;product_field&quot;:&quot;subscribe_scroll&quot;,&quot;element_name&quot;:&quot;masthead&quot;,&quot;event&quot;:&quot;navigation&quot;}">
              <svg class="svg-icon brand-arrow-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                <path fill="currentColor" d="M3 3v5.252h8.631L3 16.883V21h4.117l8.63-8.631V21H21V3H3Z"></path>
              </svg>    Subscribe
            </a>
        </div>
      </section>
    </div>
  
    <style data-bind-style="back-to-home">
      .component.back-to-home.style-loading {
        display: none;
      }
    </style>
  </back-to-home>
</section>

  

  <div data-notify-wrapper="" class="notify-wrapper">
    <span data-notify-close="" class="notify-close icon-close"></span>
    <span class="icon-check"></span>
    <span data-notify-message="" class="notify-message"></span>
  </div>
  
  <div class="inline-backup-paywall mobile" data-component-type="inline-backup-paywall" style="display:none">
    <span class="headline-semibold subscription-msg">This story is available exclusively to Business Insider
      subscribers. <a href="/subscription" class="subscription-link">Become an Insider</a>
      and start reading now.</span>
    <span class="headline-regular login-prompt">Have an account? <button class="login-prompt-btn">Log in</button>.</span>
  </div>



    
    <footer id="site-footer" class="footer headline-regular" data-track-view="{&quot;subscription_experience&quot;:&quot;bi_value_unassigned&quot;,&quot;product_field&quot;:&quot;bi_value_unassigned&quot;,&quot;element_name&quot;:&quot;footer&quot;}">
    
        <section class="top-section">
          <section class="sub-section-left"><a href="https://www.businessinsider.com" class="business-insider-logo footer-logo" title="Visit Business Insider" aria-label="Click to visit Business Insider" alt="Click to visit Business Insider">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 32 / 93)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/logos/stacked-black.svg" alt="Business Insider">
      
      <noscript>
          <img class="no-script" src="/public/assets/logos/stacked-black.svg" />
      </noscript>
      
      </div></a></section>
          <section class="sub-section-right">
            <section class="sub-section-social">
    <div class="social-media-follow" data-e2e-name="social-links" data-track-click-shared="{&quot;click_type&quot;:&quot;owned_socials&quot;,&quot;element_name&quot;:&quot;footer&quot;,&quot;event&quot;:&quot;outbound_click&quot;}">
        <a class="social-link as-facebook" href="https://www.facebook.com/businessinsider" label="facebook" title="Follow us on Facebook" aria-label="Click to visit us on Facebook" data-track-click="{&quot;click_text&quot;:&quot;facebook&quot;}" data-e2e-name="facebook" target="_blank" rel="noopener nofollow">
          <svg class="svg-icon social-facebook-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Facebook">
            <path fill="currentColor" d="M22 12.037C22 6.494 17.523 2 12 2S2 6.494 2 12.037c0 4.707 3.229 8.656 7.584 9.741v-6.674H7.522v-3.067h2.062v-1.322c0-3.416 1.54-5 4.882-5 .634 0 1.727.125 2.174.25v2.78a12.807 12.807 0 0 0-1.155-.037c-1.64 0-2.273.623-2.273 2.244v1.085h3.266l-.561 3.067h-2.705V22C18.163 21.4 22 17.168 22 12.037Z"></path>
          </svg>    </a>
        <a class="social-link as-x" href="https://x.com/businessinsider" label="x" title="Follow us on X" aria-label="Click to visit us on X" data-track-click="{&quot;click_text&quot;:&quot;x&quot;}" data-e2e-name="x" target="_blank" rel="noopener nofollow">
          <svg class="svg-icon social-x-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="X">
            <path fill="currentColor" d="M17.751 3h3.067l-6.7 7.625L22 21h-6.172l-4.833-6.293L5.464 21h-3.07l7.167-8.155L2 3h6.328l4.37 5.752L17.75 3Zm-1.076 16.172h1.7L7.404 4.732H5.58l11.094 14.44Z"></path>
          </svg>    </a>
        <a class="social-link as-linkedin" href="https://www.linkedin.com/company/businessinsider/" label="linkedin" title="Follow us on LinkedIn" aria-label="Click to visit us on LinkedIn" data-track-click="{&quot;click_text&quot;:&quot;linkedin&quot;}" data-e2e-name="linkedin" target="_blank" rel="noopener nofollow">
          <svg class="svg-icon social-linkedin-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="LinkedIn">
            <path fill="currentColor" fill-rule="evenodd" d="M4 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H4Zm4.339 4.606a1.627 1.627 0 1 1-3.254 0 1.627 1.627 0 0 1 3.254 0Zm-.221 2.867H5.13v9.335h2.988V9.473Zm4.517 0H9.662v9.335h2.943V13.91c0-2.729 3.461-2.982 3.461 0v4.9h2.849v-5.914c0-4.6-5.07-4.43-6.31-2.17l.03-1.252Z"></path></svg>
              </a>
        <a class="social-link as-youtube" href="https://www.youtube.com/user/businessinsider" label="youtube" title="Follow us on YouTube" aria-label="Click to visit us on YouTube" data-track-click="{&quot;click_text&quot;:&quot;youtube&quot;}" data-e2e-name="youtube" target="_blank" rel="noopener nofollow">
          <svg class="svg-icon social-youtube-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="YouTube">
            <path fill="currentColor" d="M11.732 5.5c.508.003 1.777.014 3.126.064l.478.019c1.358.06 2.715.16 3.388.333.898.232 1.604.91 1.842 1.77.38 1.364.427 4.026.433 4.67l.001.134v.153c-.007.644-.054 3.307-.434 4.671-.242.862-.947 1.54-1.842 1.77-.673.172-2.03.273-3.388.332l-.478.02c-1.349.05-2.618.06-3.126.063l-.223.001h-.242c-1.074-.006-5.564-.05-6.992-.417-.898-.232-1.603-.91-1.842-1.769-.38-1.364-.427-4.027-.433-4.671v-.286c.006-.645.053-3.307.433-4.672.242-.862.947-1.54 1.842-1.769 1.428-.366 5.918-.41 6.992-.416h.465ZM9.6 9.937v5.125l5.2-2.562-5.2-2.563Z"></path></svg>
              </a>
        <a class="social-link as-instagram" href="https://www.instagram.com/businessinsider/" label="instagram" title="Follow us on Instagram" aria-label="Click to visit us on Instagram" data-track-click="{&quot;click_text&quot;:&quot;instagram&quot;}" data-e2e-name="instagram" target="_blank" rel="noopener nofollow">
          <svg class="svg-icon social-instagram-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Instagram">
            <path fill="currentColor" d="M7.858 2.07c-1.064.05-1.79.22-2.425.47-.658.256-1.215.6-1.77 1.156a4.899 4.899 0 0 0-1.15 1.772c-.246.637-.413 1.364-.46 2.429-.047 1.064-.057 1.407-.052 4.122.005 2.716.017 3.056.069 4.123.05 1.064.22 1.79.47 2.426.256.657.6 1.214 1.156 1.769a4.894 4.894 0 0 0 1.774 1.15c.636.245 1.363.413 2.428.46 1.064.046 1.407.057 4.122.052 2.715-.005 3.056-.017 4.123-.068 1.067-.05 1.79-.221 2.425-.47a4.901 4.901 0 0 0 1.769-1.156 4.9 4.9 0 0 0 1.15-1.774c.246-.636.413-1.363.46-2.427.046-1.067.057-1.408.052-4.123-.005-2.715-.018-3.056-.068-4.122-.05-1.067-.22-1.79-.47-2.427a4.91 4.91 0 0 0-1.156-1.769 4.88 4.88 0 0 0-1.773-1.15c-.637-.245-1.364-.413-2.428-.46-1.065-.045-1.407-.057-4.123-.052-2.716.005-3.056.017-4.123.069Zm.117 18.078c-.975-.043-1.504-.205-1.857-.34-.467-.18-.8-.398-1.152-.746a3.08 3.08 0 0 1-.75-1.149c-.137-.352-.302-.881-.347-1.856-.05-1.054-.06-1.37-.066-4.04-.006-2.67.004-2.986.05-4.04.042-.974.205-1.504.34-1.857.18-.468.397-.8.746-1.151a3.087 3.087 0 0 1 1.15-.75c.351-.138.88-.302 1.855-.348 1.054-.05 1.37-.06 4.04-.066 2.67-.006 2.986.004 4.041.05.974.043 1.505.204 1.857.34.467.18.8.397 1.151.746.352.35.568.682.75 1.15.138.35.302.88.348 1.855.05 1.054.062 1.37.066 4.04.005 2.669-.004 2.986-.05 4.04-.043.975-.205 1.504-.34 1.857a3.1 3.1 0 0 1-.747 1.152c-.349.35-.681.567-1.148.75-.352.137-.882.301-1.855.347-1.055.05-1.371.06-4.041.066-2.67.006-2.986-.005-4.04-.05m8.152-13.493a1.2 1.2 0 1 0 2.4-.003 1.2 1.2 0 0 0-2.4.003ZM6.865 12.01a5.134 5.134 0 1 0 10.27-.02 5.134 5.134 0 0 0-10.27.02Zm1.802-.004a3.334 3.334 0 1 1 6.667-.013 3.334 3.334 0 0 1-6.667.013Z"></path>
          </svg>    </a>
        <a class="social-link as-snapchat" href="https://www.snapchat.com/p/6f1c2e77-0539-4e08-a90c-7bdd4b3f1da9/3298916208531456" label="snapchat" title="Follow us on Snapchat" aria-label="Click to visit us on Snapchat" data-track-click="{&quot;click_text&quot;:&quot;snapchat&quot;}" data-e2e-name="snapchat" target="_blank" rel="noopener nofollow">
          <svg class="svg-icon social-snapchat-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24" aria-labelledby="Snapchat">
            <path fill="currentColor" d="M21.928 16.396c-.139-.364-.403-.56-.705-.721a1.757 1.757 0 0 0-.153-.078c-.09-.045-.182-.088-.273-.134-.94-.48-1.674-1.087-2.183-1.805a4.065 4.065 0 0 1-.374-.64c-.044-.12-.042-.189-.01-.25a.413.413 0 0 1 .12-.122c.161-.103.328-.207.44-.278.202-.125.361-.225.464-.295.386-.26.656-.537.824-.846a1.64 1.64 0 0 0 .087-1.399c-.256-.648-.891-1.051-1.66-1.051a2.368 2.368 0 0 0-.61.078c.007-.444-.003-.912-.044-1.373-.145-1.62-.733-2.47-1.346-3.147a5.337 5.337 0 0 0-1.37-1.062C14.206 2.76 13.15 2.5 12 2.5c-1.15 0-2.2.26-3.132.773-.515.28-.978.639-1.371 1.064-.614.678-1.202 1.528-1.347 3.147-.04.46-.051.932-.044 1.373a2.367 2.367 0 0 0-.609-.078c-.77 0-1.406.402-1.66 1.051a1.632 1.632 0 0 0 .084 1.4c.169.31.439.586.824.846.103.07.262.169.464.296l.423.267c.055.034.101.079.136.132.033.064.034.134-.014.262a4.02 4.02 0 0 1-.369.627c-.498.703-1.21 1.298-2.12 1.775-.481.246-.982.41-1.194.965-.16.419-.055.895.35 1.296.15.15.322.276.511.373.395.21.815.371 1.25.483.09.022.176.059.253.108.148.125.127.313.324.588.098.142.224.265.37.363.412.275.876.292 1.368.31.444.017.947.035 1.522.218.238.076.486.223.772.395.689.408 1.631.966 3.208.966 1.577 0 2.526-.561 3.22-.971.284-.169.53-.314.761-.388.575-.183 1.078-.201 1.522-.218.492-.018.956-.035 1.369-.31.172-.116.316-.268.42-.444.142-.232.139-.394.272-.508a.796.796 0 0 1 .237-.104 5.677 5.677 0 0 0 1.267-.487c.202-.104.383-.241.537-.405l.005-.006c.38-.392.475-.855.32-1.263Zm-1.401.727c-.855.455-1.423.406-1.865.68-.376.234-.154.737-.426.918-.336.223-1.326-.016-2.607.392-1.055.337-1.729 1.305-3.628 1.305-1.898 0-2.556-.966-3.63-1.308-1.277-.407-2.27-.168-2.605-.391-.273-.182-.051-.684-.426-.918-.443-.274-1.011-.225-1.866-.678-.544-.29-.235-.47-.054-.554 3.097-1.446 3.591-3.68 3.613-3.845.027-.2.056-.358-.173-.562-.22-.197-1.203-.783-1.475-.967-.45-.303-.649-.606-.503-.979.102-.258.352-.355.613-.355.083 0 .166.01.246.027.495.103.975.342 1.253.407a.457.457 0 0 0 .102.013c.148 0 .2-.072.19-.235-.032-.522-.108-1.54-.023-2.49.117-1.309.554-1.957 1.073-2.53.25-.275 1.421-1.47 3.662-1.47 2.24 0 3.415 1.19 3.665 1.464.52.573.957 1.222 1.073 2.53.085.95.011 1.968-.023 2.49-.012.172.042.235.19.235a.457.457 0 0 0 .102-.013c.278-.065.758-.304 1.253-.407a1.18 1.18 0 0 1 .246-.027c.263 0 .51.099.613.355.146.373-.051.676-.502.98-.273.183-1.254.768-1.475.966-.23.204-.2.362-.173.562.022.168.515 2.401 3.613 3.845.182.088.491.268-.053.56Z"></path>
          </svg>    </a>
    </div>
    </section>
            <section class="sub-section-app-store"><div class="app-store-icons">
      <a href="https://itunes.apple.com/app/apple-store/id554260576?mt=8" class="app-store-icon" target="_blank" rel="noopener nofollow" alt="Download the app on the App Store">
          <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 40 / 135)">
        
        
        <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/badges/app-store-badge.svg" alt="Download on the App Store">
        
        <noscript>
            <img class="no-script" src="/public/assets/badges/app-store-badge.svg" />
        </noscript>
        
        </div>  </a>
      <a href="https://play.google.com/store/apps/details?id=com.freerange360.mpp.businessinsider" class="app-store-icon" target="_blank" rel="noopener nofollow" alt="Download the app on Google Play">
          <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 40 / 135)">
        
        
        <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/badges/google-play-badge.svg" alt="Get it on Google Play">
        
        <noscript>
            <img class="no-script" src="/public/assets/badges/google-play-badge.svg" />
        </noscript>
        
        </div>  </a>
    </div></section>
          </section>
        </section>
    
      <section class="links-section">
        <section class="sub-section-privacy"><div class="links-list-heading headline-semibold">Legal &amp; Privacy</div>
    <ul class="links-list">
      <li><a class="links-list-link" href="/terms">Terms of Service</a></li>
      <li><a class="links-list-link" href="/terms-of-sale">Terms of Sale</a></li>
      <li><a class="links-list-link" href="/privacy-policy">Privacy Policy</a></li>
      <li><a class="links-list-link" href="/accessibility">Accessibility</a></li>
      <li><a class="links-list-link" href="/code-of-ethics">Code of Ethics Policy</a></li>
      <li><a class="links-list-link" href="https://www.parsintl.com/publication/business-insider/">Reprints &amp; Permissions</a></li>
      <li><a class="links-list-link" href="/disclaimer">Disclaimer</a></li>
      <li><a class="links-list-link" href="/advertising-policies">Advertising Policies</a></li>
      <li><a class="links-list-link" href="/conflict-of-interest-policy">Conflict of Interest Policy</a></li>
      <li><a class="links-list-link" href="/commerce-policy">Commerce Policy</a></li>
      <li><a class="links-list-link" href="/coupons-privacy-policy">Coupons Privacy Policy</a></li>
      <li><a class="links-list-link" href="/coupons-terms">Coupons Terms</a></li>
    </ul></section>
        <section class="sub-section-company"><div class="links-list-heading headline-semibold">Company</div>
    <ul class="links-list">
      <li><a class="links-list-link" href="https://www.businessinsider.com/about-us">About Us</a></li>
      <li><a class="links-list-link" href="/work-at-business-insider">Careers</a></li>
      <li><a class="links-list-link" href="https://advertising.businessinsider.com/">Advertise With Us</a></li>
      <li><a class="links-list-link" href="/contact">Contact Us</a></li>
      <li><a class="links-list-link" href="/secure-news-tips">News Tips</a></li>
      <li><a class="links-list-link" href="/category/business-insider-press-room">Company News</a></li>
      <li><a class="links-list-link" href="/awards">Awards</a></li>
      <li><a class="links-list-link" href="/masthead">Masthead</a></li>
    </ul></section>
        <section class="sub-section-group">
          <section class="sub-section-other"><div class="links-list-heading headline-semibold">Other</div>
    <ul class="links-list">
      <li><a class="links-list-link" href="/sitemap/html/index.html">Sitemap</a></li>
      <li><a class="links-list-link" href="https://www.finanzen.net/">Stock quotes by finanzen.net</a></li>
      <li><a class="links-list-link" href="/category/corrections">Corrections</a></li>
      <li><a class="links-list-link" href="/community-guidelines">Community Guidelines</a></li>
      <li><a class="links-list-link" href="/how-the-business-insider-newsroom-uses-ai">AI Use</a></li>
    </ul></section>
          <section class="sub-section-editions"><div class="links-list-heading headline-semibold">International Editions</div>
    <ul class="links-list">
      <li><a class="links-list-link" href="https://www.businessinsider.de/?IR=C">AT</a></li>
      <li><a class="links-list-link" href="https://www.businessinsider.de/?IR=C">DE</a></li>
      <li><a class="links-list-link" href="https://businessinsider.es/">ES</a></li>
      <li><a class="links-list-link" href="https://www.businessinsider.jp/">JP</a></li>
      <li><a class="links-list-link" href="https://www.businessinsider.com.pl/?IR=C">PL</a></li>
      <li><a class="links-list-link" href="https://www.businessinsider.tw">TW</a></li>
    </ul></section>
        </section>
      </section>
    
      <section class="copyright-section"><a class="copy-link" href="/terms">Copyright © 2026</a> 
    Insider Inc. All rights reserved.
    Registration on or use of this site constitutes acceptance of our 
    <a class="copy-link" href="/terms" data-e2e-name="footer-terms-of-service">Terms of Service</a>
    <span>and</span>
    <a class="copy-link privacy" href="/privacy-policy" data-e2e-name="footer-privacy-policy">Privacy Policy</a>.</section>
    
        <section class="bottom-section">
          <section class="sub-section sub-section-top"><div class="brand-logo insider-com">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 16 / 103)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/INSIDER/US/logos/insider-com-trademark-opt.svg" alt="Insider.com TM Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/INSIDER/US/logos/insider-com-trademark-opt.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo insider-logo">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 17 / 100)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/INSIDER/US/logos/Insider-logo-dark-opt.svg" alt="Insider">
      
      <noscript>
          <img class="no-script" src="/public/assets/INSIDER/US/logos/Insider-logo-dark-opt.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo brand-logo insider-inc">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 16 / 77)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/INSIDER/US/logos/insider-inc.svg" alt="Insider-Inc Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/INSIDER/US/logos/insider-inc.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo insider-tech">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 44 / 103)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/BI/US/logos/Tech-Insider-opt.svg" alt="Tech Insider Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/BI/US/logos/Tech-Insider-opt.svg" />
      </noscript>
      
      </div></div></section>
          <section class="sub-section sub-section-bottom"><div class="brand-logo bi-de">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 32 / 151)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/BI/DE/logos/BI-DE-Black-on-Light-final-footer-logo-opt.svg" alt="Business Insider DE Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/BI/DE/logos/BI-DE-Black-on-Light-final-footer-logo-opt.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo markets-insider">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 36 / 70)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/MI/logos/markets-insider-stacked.svg" alt="Insider Media Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/MI/logos/markets-insider-stacked.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo insider-media">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 36 / 70)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/INSIDER/US/logos/insider-media.svg" alt="Insider Media Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/INSIDER/US/logos/insider-media.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo news-insider">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 36 / 62)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/INSIDER/US/logos/news-insider.svg" alt="News Insider Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/INSIDER/US/logos/news-insider.svg" />
      </noscript>
      
      </div></div>
    
    <div class="brand-logo silicon-alley-insider">
        <div class="lazy-holder lazy-holder  has-transparency" style="padding-top: calc(100% * 36 / 150)">
      
      
      <img class="lazy-image has-transparency js-queued" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1 1'%3E%3C/svg%3E" data-src="/public/assets/INSIDER/US/logos/silicon-alley-insider.svg" alt="Silicon Alley Logo">
      
      <noscript>
          <img class="no-script" src="/public/assets/INSIDER/US/logos/silicon-alley-insider.svg" />
      </noscript>
      
      </div></div></section>
        </section>
    
    </footer>

  

  <script>window.allScripts = window.allScripts || []; window.allScripts.push({ type: "first-party", script: "%3Cscript%20async%20type%3D%22text%2Fjavascript%22%20src%3D%22%2Fscripts%2Futilities.a75bae3d26cbd43ca782.js%22%3E%3C%2Fscript%3E" });</script>
  <script>window.allScripts = window.allScripts || []; window.allScripts.push({ type: "first-party", script: "%3Cscript%20async%20type%3D%22text%2Fjavascript%22%20src%3D%22%2Fscripts%2Fvendors.887b1f2e9e5957401491.js%22%3E%3C%2Fscript%3E" });</script>
  <script>window.allScripts = window.allScripts || []; window.allScripts.push({ type: "first-party", script: "%3Cscript%20async%20type%3D%22text%2Fjavascript%22%20src%3D%22%2Fscripts%2Fmain.cbea60eb6dd2554a607f.js%22%3E%3C%2Fscript%3E" });</script>


  <noscript>
    <img src="https://sb.scorecardresearch.com/p?c1=2&c2=9900186&cv=3.6.0&;cj=1&comscorekw="/>
  </noscript>

  <script id="consent-manager-script">(()=>{var e={19249(e,n,t){"use strict";const o=async()=>{const e=localStorage.getItem("profile");if(!e)return;let n;try{n=JSON.parse(e)}catch{return}const t=n["https://insider/memberId"],o=n["https://insider/token"];if(!t||!o)return;const i=window.Fenrir.cm?.isOptedOutOfAds,{privacyApi:r}=window.Fenrir,{countryCode:s}=window.Fenrir.geoData,a={ads:i,privacyApi:r,countryCode:s},d=localStorage.getItem("idun-consent-preferences");let c={};if(d)try{c=JSON.parse(d)}catch{}if(c.ads!==i)try{(await fetch(`${window.Fenrir.config.apigateway.domain}/v1.0/users/${t}/consent-preferences`,{method:"POST",headers:{"Content-Type":"application/json",Authorization:`Bearer ${o}`},body:JSON.stringify(a)})).ok&&localStorage.setItem("idun-consent-preferences",JSON.stringify(a))}catch(e){}};const i=function(){window.Fenrir.geoData?o():document.addEventListener("onGeoDataCaptured",()=>{o()})};t(61187);const r="Sourcepoint Load - start",s="Sourcepoint Load - end sourcepoint",a="Sourcepoint Load - has consent",d="Sourcepoint Load - load queue consent";let c=!1,w=!1,u=!1;function p(){return w||c}function m(){let e=!0,n=null;const t=localStorage.getItem("_sp_user_consent_6165");try{n=t?JSON.parse(t):null}catch(e){}if("GPP"===window.Fenrir.privacyApi){const{granularStatus:t}=n?.usnat?.consentStatus||{};e=!1===t?.sellStatus}else if("TCF"===window.Fenrir.privacyApi){const{granularStatus:t}=n?.gdpr?.consentStatus||{};e="ALL"!==t?.purposeConsent?.toUpperCase()}return e}function f(e){const{step:n,timeFromStart:t}=e;delete e.step,delete e.timeFromStart;const o={now:window.Fenrir.getTime(),step:n,timeFromStart:t,cmStarted:window.Fenrir.cm.cmStarted,usPrivacyApplies:window.Fenrir.cm.usPrivacyApplies,euPrivacyApplies:window.Fenrir.cm.euPrivacyApplies,windowLoaded:window.Fenrir.cm.windowLoaded,isOptedOutOfAds:window.Fenrir.cm.isOptedOutOfAds,queueConsent:window.Fenrir.cm.queueConsent,...e};return o.timeFromStart||delete o.timeFromStart,o}function l(e){window.Fenrir.cm.isOptedOutOfAds=e,window.Fenrir.cm.cmStarted=!0,window.Fenrir.cm.loadQueueConsent();const n=new CustomEvent("onConsentReady",{detail:{isOptedOutOfAds:window.Fenrir.cm.isOptedOutOfAds,type:"update"}});document.dispatchEvent(n),i()}window.performance.mark(r),window.__tcfapi&&window.__tcfapi("addEventListener",2,function(e,n){if(n&&e){if("cmpuishown"===e.eventStatus){if(window.Fenrir.console.info(f({step:"consentManager sp.getTCData cmpuishown"})),window.Fenrir.cm.isOptedOutOfAds=m(),!w){window.performance.mark(s);const e=window.performance.measure("load - sourcepoint",r,s);window.Fenrir.console.info(f({step:"consentManager europePrivacy.bannerShown",timeFromStart:e.duration}))}w=!0,window.Fenrir.cm.cmStarted=p(),window.Fenrir.cm.loadQueueConsent()}else if("useractioncomplete"===e.eventStatus||"tcloaded"===e.eventStatus){window.Fenrir.console.info(f({step:`consentManager sp.getTCData ${e.eventStatus}`})),window.Fenrir.cm.isOptedOutOfAds=m(),c||(window.performance.mark(a),window.performance.measure("consentManager europePrivacy.consentGiven",r,a)),c=!0,window.Fenrir.cm.cmStarted=p(),window.Fenrir.cm.loadQueueConsent();const n=new CustomEvent("onConsentReady",{detail:{isOptedOutOfAds:window.Fenrir.cm.isOptedOutOfAds,type:"update"}});document.dispatchEvent(n),i()}}else window.Fenrir.console.info(f({step:"consentManager sp.getTCData error",tcData:e}))}),window.__gpp&&window.__gpp("addEventListener",function(e){if("sectionChange"===e.eventName){let n=!1;Object.keys(e.pingData.parsedSections).forEach(t=>{1===e.pingData?.parsedSections[t]?.SaleOptOut&&(n=!0)}),window.Fenrir.console.info(f({step:"consentManager gpp.sectionChange",data:e})),l(n)}else"signalStatus"===e.eventName&&"disabled"===e.pingData?.cmpDisplayStatus&&(window.Fenrir.console.info(f({step:"consentManager gpp.signalStatus",data:e})),l(!1))});const F="GPP"===window.Fenrir?.privacyApi,g="TCF"===window.Fenrir?.privacyApi;window.Fenrir.cm=Object.assign({},window.Fenrir.cm,{cmStarted:!1,windowLoaded:!1,usPrivacyApplies:F,euPrivacyApplies:g,onConsent:function(e){if("function"!=typeof e)throw new Error("method `onConsent` requires `callback` function");return document.addEventListener("onConsentReady",n=>{window.Fenrir.console.info(f({step:"consentManager onConsentReady",event:n})),e(n.detail)}),e({isOptedOutOfAds:window.Fenrir.cm.isOptedOutOfAds})},requestConsent:function(e){window.Fenrir.console.info(f({step:"consentManager requestConsent",requestor:e}));const n=new CustomEvent("onConsentReady",{detail:{isOptedOutOfAds:window.Fenrir.cm.isOptedOutOfAds,type:"request",scope:e}});document.dispatchEvent(n)},loadQueueConsent:function(){if(window.Fenrir.console.info(f({step:"consentManager loadQueueConsent"})),!window.Fenrir.cm.windowLoaded||!window.Fenrir.cm.cmStarted)return;let e;u||(window.performance.mark(d),e=window.performance.measure("queue load - sourcepoint",r,d)),u=!0,window.Fenrir.config.delayThirdPartyScripts=!1,window.Fenrir.console.info(f({step:"consentManager loadQueueConsent load scripts",timeFromStart:e?.duration}));let n=window.Fenrir.cm.queueConsent.length;for(;n;){const e=window.Fenrir.cm.queueConsent.shift();n=window.Fenrir.cm.queueConsent.length,"function"==typeof e&&e(),window.Fenrir.console.info(f({step:"consentManager loadQueueConsent script",queueLength:n}))}},getAdConsent:function(){function e(){let e=!0;if(window.Fenrir.cm.usPrivacyApplies||window.Fenrir.cm.euPrivacyApplies){const{isOptedOutOfAds:n}=window.Fenrir.cm;e=!n}return e}return new Promise(n=>{if("boolean"!=typeof window.Fenrir?.cm?.isOptedOutOfAds){const t=setTimeout(()=>n(!0),3e3);document.addEventListener("onConsentSaved",()=>{t&&clearTimeout(t),n(e())})}else n(e())})},queueConsent:[]}),window.Fenrir.console.info(f({now:window.Fenrir.getTime(),step:"consentManager starting...",tcfapi:window.__tcfapi}))},61187(){window._sp_queue&&window._sp_queue.push(()=>{window._sp_.addEventListener("onMessageChoiceSelect",(e,n,t)=>{const o=window.dataLayer||[],i={event:"privacy_center_engagement",element_name:"privacy_banner",action:"save"};if("gdpr"===e){switch(t){case 11:i.is_opted_out_of_ads=!1;break;case 12:i.action="click_to_preference_center",i.is_opted_out_of_ads="bi_value_unassigned";break;case 13:i.is_opted_out_of_ads=!0}o.push(i),window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"privacy modal engagement dataLayer push",dataEvent:i})}})})}},n={};function t(o){var i=n[o];if(void 0!==i)return i.exports;var r=n[o]={exports:{}};return e[o](r,r.exports,t),r.exports}t.m=e,t.c=n,t.o=(e,n)=>Object.prototype.hasOwnProperty.call(e,n),(()=>{t.S={};var e={},n={};t.I=(o,i)=>{i||(i=[]);var r=n[o];if(r||(r=n[o]={}),!(i.indexOf(r)>=0)){if(i.push(r),e[o])return e[o];t.o(t.S,o)||(t.S[o]={});t.S[o];var s=[];return s.length?e[o]=Promise.all(s).then(()=>e[o]=1):e[o]=1}}})();t(19249)})();</script><script id="script-loader-script">(()=>{"use strict";var e={98210(){const e={},t={sm:"0",smMax:"599px",md:"600px",mdMax:"959px",lg:"960px",lgMax:"1259px",xl:"1260px"};window.Fenrir?.viewVersion&&(t.mdMax="1007px",t.lg="1008px",t.lgMax="1307px",t.xl="1308px");const n={small:`(max-width:${t.smMax})`,medium:`(min-width:${t.md}) and (max-width:${t.mdMax})`,large:`(min-width:${t.lg}) and (max-width:${t.lgMax})`,xlarge:`(min-width:${t.xl})`},r={mobile:`(max-width:${t.smMax})`,tablet:`(min-width:${t.md}) and (max-width:${t.mdMax})`,desktop:`(min-width:${t.lg})`,desktopxl:`(min-width:${t.xl})`},i=e=>({get:()=>window.matchMedia(e).matches}),o=e=>({get:()=>Object.values(e).reduce((t,n,r)=>(window.matchMedia(n).matches&&(t=`${Object.keys(e)[r]}`),t),"")});Object.defineProperties({},{isSmall:i(n.small),isMedium:i(n.medium),isLarge:i(n.large),isXLarge:i(n.xlarge),current:o(n)}),Object.defineProperties({},{isMobile:i(r.mobile),isTablet:i(r.tablet),isDesktop:i(r.desktop),current:o(r)}),Object.defineProperties(e,{isMobile:i(`(max-width:${t.mdMax})`),isDesktop:i(r.desktop),deviceType:{get:()=>window.matchMedia(`(max-width:${t.mdMax})`).matches?"mobile":"desktop"},width:{get:()=>document.documentElement.clientWidth},height:{get:()=>document.documentElement.clientHeight}});(()=>{function e(e){const t=new RegExp(`(?:^|;)(?:[ s]*)(?:${e}=)([^;]+)`).exec(document.cookie);return t&&t[1]?t[1]:null}})();const d=(e="",t="variant")=>{const n=document.querySelector(`meta[name="ii-ab-test:${e}"]`);if(!n)return!1;const r=n.getAttribute("value");return[t].flat().includes(r)};function a(e){let t;return window.performance?.mark?t=window.performance.mark(e):window.LUX?.mark&&(t=window.LUX.mark(e)),t||(t=window.performance.getEntriesByName(e,"mark").shift(),t||(t={startTime:window.performance.now()})),t}function s(e){return`script-loader: ${e}`}function c(e,t){const n=s(e),r=function(e){return`script-loader-${e}`}(e),i=a(`${n} - End`),o=function(e,t,n){let r;try{window.performance?.measure?r=window.performance.measure(e,t,n):window.LUX?.measure&&(r=window.LUX.measure(e,t,n))}catch(e){}return r||(r=window.performance.getEntriesByName(e,"measure").shift(),r||(r={startTime:window.performance.now()})),r}(r,`${n} - Start`,`${n} - End`),d=window.performance.getEntriesByName(`${n} - Start`,"mark")[0];let c,l,w;return(t||d)&&(c=t?.startTime||d?.startTime,l=i.startTime,w=o.duration||l-c),{start:c,end:l,duration:w}}function l(e){const t=new CustomEvent("onTrackedScriptLoaded",{detail:e});document.dispatchEvent(t)}const w="testing"===window.Fenrir?.config?.context,p=window.Fenrir?.config?.shouldDeferScripts,m=3e3,u=document.querySelector("head");function f(e,t){const n=document.createElement("script");let r,i,o,d;return Array.prototype.slice.call(e.attributes).forEach(e=>{const t=e.nodeName;let d=e.nodeValue;["id","src","async","defer"].includes(t)?(["async","defer"].includes(t)&&!d&&(d=1),n[t]=d):"data-track-load"===t?r=d:"data-request-consent"===t&&window.Fenrir?.config?.delayThirdPartyScripts?i=d||!0:"onload"===t?o=d:n.setAttribute(t,d)}),r&&(d=a(`${s(r)} - Start`),n.onerror=function(){const e={name:r,error:!0};window.Fenrir.trackedScripts.push(e),l(e)}),n.onreadystatechange=function(e,t){if(t||!n.readyState||/loaded|complete/.test(n.readyState)){if(r){const{start:e,end:t,duration:n}=c(r,d),i={name:r,error:!1,start:e,end:t,duration:n};window.Fenrir.trackedScripts.push(i),l(i)}if(i&&window.Fenrir.cm&&window.Fenrir.cm.requestConsent(i),n.onreadystatechange=null,n.onload=null,o){window.Fenrir.console.info({step:"scriptLoader.loadMethod: downloadScript.OnLoad",onloadCallback:o});const e=document.createElement("script");e.setAttribute("data-on-load-callback",""),e.textContent=o,u.appendChild(e)}}},n.onload=n.onreadystatechange,window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.loadMethod: downloadScript",src:e.src,trackLoad:e.dataset.trackLoad,scriptIndex:t,script:e}),n}function g(e,t){e=decodeURIComponent(e);const n=document.createElement("div");n.innerHTML=e;const r=window.Fenrir?.privacyApi;window.Fenrir.cm.cmStarted||"NONE"!==r||(window.Fenrir.cm.cmStarted=!0);Array.prototype.slice.call(n.querySelectorAll("script")).forEach((e,n)=>{let r=e;const{trackLoad:i=""}=r.dataset||{};try{const o=r&&r.dataset&&r.dataset.consent,d=()=>{r.textContent&&r.textContent.trim()?(r=document.createElement("script"),r.textContent=e.textContent,window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.loadMethod: injectInlineScript",trackLoad:i,scriptIndex:t,script:r})):r.src&&(r=f(r,t));const o=e.id||`inline-script-${t}-${n}`;r.setAttribute("data-script-id",o),window.setTimeout(()=>u.appendChild(r),0)};if(o&&window.Fenrir.cm&&(!window.Fenrir.cm.windowLoaded||!window.Fenrir.cm.cmStarted||window.Fenrir.cm.euPrivacyApplies&&"boolean"!=typeof window.Fenrir.cm.isOptedOutOfAds))return void window.Fenrir.cm.queueConsent.push(()=>{d()});d()}catch(e){console.error(e)}})}function y(t){t=t||"load";const n=window.allScripts.filter((n,r)=>{if(Object.prototype.hasOwnProperty.call(n,"index")||(n.index=r),n.filtered)return!1;const i=n.type||"load",o=/data-only-on=['"]?(?<onlyOn>[A-Za-z\d\s-_]*)['"]?/gi.exec(decodeURIComponent(n.script)),d=o?.groups?.onlyOn;if(d&&d!==e.deviceType)return n.filtered=!0,!1;if(window.Fenrir.cm&&!window.Fenrir.cm.euPrivacyApplies){if("first-party"===t){if(i.indexOf("first-party")>=0)return n.filtered=!0,!0}else if(i.indexOf("first-party")<0)return n.filtered=!0,!0;return!1}const a=t===n.type;return a&&(n.filtered=!0),a});window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.loadScriptLoaderScripts: filtered",loadScriptType:t,scripts:n,allScripts:window.allScripts}),n.forEach((e,t)=>{e.loaded||(e.loaded=!0,w?g(e.script,t):setTimeout(()=>{g(e.script,e.index||t)},0))})}window.allScripts=window.allScripts||[],window.Fenrir.trackedScripts=[];let F=!1;const h=[];function x(e){if(window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.manageScriptTypeLoadOrder",scriptTypeToLoad:e}),"load"===e){if(F)return;return F=!0,y(e),void h.forEach(y)}F?y(e):h.push(e)}function v(){window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.triggered: load"}),x("load"),window.Fenrir.cm&&(window.Fenrir.cm.loadQueueConsent(),window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.milestone: loadQueueConsent"}))}if(p){let e=!1;const t=()=>{if(window.Fenrir.cm&&(window.Fenrir.cm.windowLoaded=!0,window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.eventHandler: window.load"})),e)return;let t;if(e=!0,d("tti","v1")&&(t="requestIdleCallback"),d("tti","v2")&&(t="setTimeout"),d("tti","v3")&&(t="onLargestContentfulPaint"),d("tti","v4")&&(t="afterFirstPartyComplete"),navigator.connection){const{rtt:e,downlink:n}=navigator.connection;(e>200||n<5)&&(t=t||"onLargestContentfulPaint"),window.Fenrir.console.info({now:window.Fenrir.getTime(),rtt:e,downlink:n})}if(window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.triggered: first-party ",ttiTestType:t}),y("first-party"),t){if("requestIdleCallback"===t)r={timeout:m},"function"==typeof(n=v)&&("function"==typeof requestIdleCallback?requestIdleCallback(n,r):setTimeout(n,0));else if("setTimeout"===t)setTimeout(v,m);else if("onLargestContentfulPaint"===t)!function(e){"function"==typeof e&&("function"==typeof PerformanceObserver&&"function"==typeof LargestContentfulPaint?new PerformanceObserver(t=>{const n=t.getEntries(),r=n[n.length-1];window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.eventHandler: onLargestContentfulPaint",entry:r}),e({entry:r})}).observe({type:"largest-contentful-paint",buffered:!0}):setTimeout(e,m,{entry:void 0,fallback:!0}))}(v);else if("afterFirstPartyComplete"===t){let e=!1;document.addEventListener("loadDelayedOnLoadScripts",()=>{e||(e=!0,window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.eventHandler: loadDelayedOnLoadScripts"}),v())})}}else v();var n,r};window.addEventListener("load",t),"serviceWorker"in navigator&&("local"!==window.Fenrir.config.fenrirEnv?window.addEventListener("load",()=>{window.Fenrir.console.info("Registering service worker"),navigator.serviceWorker.register("/service-worker.js")}):navigator.serviceWorker.getRegistrations().then(e=>{e.length&&e.forEach(e=>{window.Fenrir.console.info("Unregistering service worker"),e.unregister()})}).catch(e=>{window.Fenrir.console.info("Error unregistering service worker",e)}))}let L=!1;document.addEventListener("loadDelayedFirstPartyScripts",()=>{L||(L=!0,window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.eventHandler: loadDelayedFirstPartyScripts"}),window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.triggered: gdpr-first-party"}),x("gdpr-first-party"))});let T=!1;document.addEventListener("loadDelayedThirdPartyScripts",()=>{T||(T=!0,window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.eventHandler: loadDelayedThirdPartyScripts"}),window.Fenrir.console.info({now:window.Fenrir.getTime(),step:"scriptLoader.triggered: gdpr"}),x("gdpr"),window.Fenrir.onloadDelayedThirdPartyScripts())})}},t={};function n(r){var i=t[r];if(void 0!==i)return i.exports;var o=t[r]={exports:{}};return e[r](o,o.exports,n),o.exports}n.m=e,n.c=t,n.o=(e,t)=>Object.prototype.hasOwnProperty.call(e,t),(()=>{n.S={};var e={},t={};n.I=(r,i)=>{i||(i=[]);var o=t[r];if(o||(o=t[r]={}),!(i.indexOf(o)>=0)){if(i.push(o),e[r])return e[r];n.o(n.S,r)||(n.S[r]={});n.S[r];var d=[];return d.length?e[r]=Promise.all(d).then(()=>e[r]=1):e[r]=1}}})();n(98210)})();</script>
  



  

  <iframe src="https://markets.businessinsider.com/cross-domain" data-src="https://markets.businessinsider.com/cross-domain" data-load-strategy="disable-lazy" id="0-iframe" style="display:none" class="cross-domain"></iframe> 
  <iframe src="https://my.businessinsider.com/cross-domain" data-src="https://my.businessinsider.com/cross-domain" data-load-strategy="disable-lazy" id="1-iframe" style="display:none" class="cross-domain"></iframe> 

    
    
    <div class="jumper" data-component-type="jumper" data-load-strategy="exclude">
      <p>Jump to</p>
      <ol>
          <li><a href="#post-headline">Main content</a></li>
    
        <li><a href="#search" data-jumper-target=".subnav-item-link.search" data-jumper-action="click">Search</a></li>
        <li><a href="#account" data-jumper-action="account">Account</a></li>
    
        <li class="hide-jumper-link"><a href="/">Jump to top of page</a></li>
      </ol>
    </div>


  <div id="checkout-entry" class="bifrost-entry full-screen hidden"></div>
  <div id="auth-entry" class="bifrost-entry full-screen hidden"></div>
  <div id="dialog-entry" class="bifrost-entry full-screen hidden"></div>
  <div id="onboarding-entry" class="bifrost-entry full-screen hidden"></div>
  <div id="content-wall-drawer-entry" class="bifrost-entry bottom hidden"></div>
  <div id="appBanner-entry" class="bifrost-entry bottom hidden"></div>
  <div id="paywall-drawer-entry" class="bifrost-entry bottom hidden"></div>

  <noscript>
    <iframe
      src="https://www.googletagmanager.com/ns.html?id=GTM-MP6F46L"
      title="GTM" height="0" width="0" style="display:none;visibility:hidden"
    ></iframe>
  
  </noscript>


  
  <div class="overlay" data-component-type="overlay" data-load-strategy="interaction"></div>
    


<iframe marginwidth="0" marginheight="0" scrolling="no" frameborder="0" id="1da13537976d938" width="0" height="0" src="about:blank" name="__pb_locator__" style="display: none; height: 0px; width: 0px; border: 0px;"></iframe><iframe name="googlefcPresent" style="display: none; width: 0px; height: 0px; border: none; z-index: -1000; left: -1000px; top: -1000px;"></iframe><iframe name="__launchpadLocator" style="display: none;"></iframe><div class="follow-topic-subscribe-modal component-loaded" data-component-type="follow-topic-subscribe-modal" data-topic="{&quot;type&quot;:&quot;author&quot;,&quot;slug&quot;:&quot;grace-kay&quot;,&quot;label&quot;:&quot;Grace Kay&quot;,&quot;shortenedLabel&quot;:&quot;Grace&quot;,&quot;image&quot;:null,&quot;link&quot;:&quot;https://www.businessinsider.com/author/grace-kay&quot;}" data-location="byline" role="dialog" aria-modal="true">
                                          <button class="close-button" aria-label="Close modal">
                                            <svg class="svg-icon close-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                                              <path fill="currentColor" d="M21 5.394 18.606 3 12 9.606 5.394 3 3 5.394 9.606 12 3 18.606 5.394 21 12 14.394 18.606 21 21 18.606 14.394 12 21 5.394Z"></path>
                                            </svg>    </button>
                                      
                                      
                                          <div class="modal-title-wrapper">
                                            <h2 class="modal-title heading-md">
                                              <svg class="svg-icon check-icon " role="img" xmlns="http://www.w3.org/2000/svg" width="1em" height="1em" viewBox="0 0 24 24">
                                                <path fill="currentColor" d="M21.985 6.289 19.19 3.277 8.383 14.222 4.117 9.895l-2.813 3.013 7.082 7.044L21.985 6.289Z"></path>
                                              </svg>        <span class="modal-title-text">Follow Grace Kay</span>
                                            </h2>
                                          </div>
                                      
                                          <p class="modal-subtitle body-xs-subtle">
                                              Every time Grace publishes a story, you’ll get an alert straight to your inbox!
                                          </p>
                                      
                                          <section class="form-section">
                                            <div class="form-input-wrapper">
                                              <p class="follow-topic-email-label label-md-strong">Enter your email</p>
                                              <input type="email" class="follow-topic-email-input label-lg-subtle" name="email" required="" autocomplete="off">
                                              <p class="error-message label-sm-subtle d-none"></p>
                                            </div>
                                      
                                            <button class="submit-button label-lg-strong">Sign up</button>
                                      
                                            <p class="disclaimer label-sm-subtle">
                                              By clicking “Sign up”, you agree to receive emails from Business Insider. In addition, you accept Insider’s
                                              <a href="/terms" target="_blank" rel="noopener noreferrer" data-mrf-link="https://www.businessinsider.com/terms" cmp-ltrk="post byline" cmp-ltrk-idx="1" mrfobservableid="e784b8a7-a471-4215-a266-5a4817727b9c">Terms of Service</a> and
                                              <a href="/privacy-policy" target="_blank" rel="noopener noreferrer" data-mrf-link="https://www.businessinsider.com/privacy-policy" cmp-ltrk="post byline" cmp-ltrk-idx="2" mrfobservableid="a914cc46-7a9b-4f4d-af54-dde37dd6490b">Privacy Policy</a>.
                                            </p>
                                          </section>
                                        </div><iframe name="googlefcInactive" src="about:blank" style="display: none; width: 0px; height: 0px; border: none; z-index: -1000; left: -1000px; top: -1000px;"></iframe><iframe name="googlefcLoaded" src="about:blank" style="display: none; width: 0px; height: 0px; border: none; z-index: -1000; left: -1000px; top: -1000px;"></iframe>
<script type="text/javascript" id="" charset="">!function(d,e,f,a,b,c){d.twq||(a=d.twq=function(){a.exe?a.exe.apply(a,arguments):a.queue.push(arguments)},a.version="1.1",a.queue=[],b=e.createElement(f),b.async=!0,b.src="//static.ads-twitter.com/uwt.js",c=e.getElementsByTagName(f)[0],c.parentNode.insertBefore(b,c))}(window,document,"script");twq("init","o389k");twq("track","PageView");</script>
<script id="" text="" charset="" type="text/javascript" src="https://cdn.brandmetrics.com/tag/2307d3ae2e9240c98867fcda61fc7d4f/insi
der.js"></script><script type="text/javascript" id="" charset="">(function(a,c,e,k,b){a[b]=a[b]||[];a[b].push({projectId:"10000",properties:{pixelId:"10170109",userEmail:"\x3cemail_address\x3e"}});var d=c.createElement(e);d.src=k;d.async=!0;d.onload=d.onreadystatechange=function(){var f=this.readyState,l=a[b];if(!f||f=="complete"||f=="loaded")try{var g=YAHOO.ywa.I13N.fireBeacon;a[b]=[];a[b].push=function(h){g([h])};g(l)}catch(h){}};c=c.getElementsByTagName(e)[0];e=c.parentNode;e.insertBefore(d,c)})(window,document,"script","https://s.yimg.com/wi/ytc.js","dotq");</script><script type="text/javascript" id="" charset="">var loadJWLib=function(){function f(a,e){var c=10,d=function(){setTimeout(function(){c--;a()?e():c>0&&d()},1E3)};d()}function b(a,e,c){var d=a.getPlaylistItem().title?a.getPlaylistItem().title:"not set";dataLayer.push({event:e,jwp_player_id:a.id,jwp_video_name:d,jwp_interaction:c,jwp_video_url:a.getPlaylistItem().file,jwp_duration:a.getDuration(),jwp_width:a.getWidth(),jwp_height:a.getHeight(),jwp_position:a.getPosition(),jwp_volume:a.getVolume(),jwp_player_type:a.renderingMode})}window.timeCount=
0;window.playCount=0;try{jwplayer().on("ready",function(a){b(this,"playback-playerisready","playersetup");window.readyCheck=!0})}catch(a){window.readyCheck=!1}f(function(){return window.jwplayer!==void 0},function(){try{if(window.readyCheck===!1)jwplayer().on("ready",function(a){b(this,"playback-playerisready","playersetup")});jwplayer().on("setupError",function(a){b(this,"setup-error",a.message)});jwplayer().on("play",function(a){jwplayer().getPosition()>0&&b(this,"playback-resume","resume")});jwplayer().on("play",
function(a){jwplayer().getPosition()==0&&window.playCount===0&&(b(this,"playback-play","play"),window.playCount+=1)});jwplayer().on("seek",function(a){b(this,"playback-seek","seek")});jwplayer().on("time",function(a){Math.round(this.getPosition()/this.getDuration()*100)===20&&window.timeCount===0&&(window.timeCount+=1,b(this,"playback-time","20%"));Math.round(this.getPosition()/this.getDuration()*100)===40&&window.timeCount===1&&(window.timeCount+=1,b(this,"playback-time","40%"));Math.round(this.getPosition()/
this.getDuration()*100)===60&&window.timeCount===2&&(window.timeCount+=1,b(this,"playback-time","60%"));Math.round(this.getPosition()/this.getDuration()*100)===80&&window.timeCount===3&&(window.timeCount+=1,b(this,"playback-time","80%"));Math.round(this.getPosition()/this.getDuration()*100)===100&&window.timeCount===4&&(b(this,"playback-time","98%"),window.timeCount=0,window.playCount=0)});jwplayer().on("pause",function(a){b(this,"playback-pause","Pause")});jwplayer().on("firstFrame",function(a){b(this,
"playback-firstFrame","First Frame")});jwplayer().on("adRequest",function(a){b(this,"playback-adrequest","Ad Request")});jwplayer().on("adError",function(a){b(this,"playback-aderror",a.message)});jwplayer().on("adImpression",function(a){b(this,"playback-adimpression","Ad Impression")});jwplayer().on("adPlay",function(a){b(this,"playback-adplay","Ad Play")});jwplayer().on("adClick",function(a){b(this,"playback-adclicked","Ad Skipped")});jwplayer().on("adSkipped",function(a){b(this,"playback-adskip",
"Ad Skipped")});jwplayer().on("adBlock",function(a){b(this,"playback-adblock","Ad Blocked")});jwplayer().on("complete",function(a){b(this,"playback-complete","Complete");window.playCount=0});jwplayer().on("error",function(a){b(this,"playback-error",a.message)})}catch(a){}})},jwInterval=setInterval(function(){window.jwplayer!=void 0&&(loadJWLib(),clearInterval(jwInterval))},200);setTimeout(function(){clearInterval(jwInterval)},15E3);</script><script type="text/javascript" async="true" src="https://cdn.brandmetrics.com/scripts/bundle/65568.js?sid=e212afbd-8285-4839-a80d-4aa911385e1e&amp;toploc=www.businessinsider.com"></script><script type="text/javascript" id="" charset="">(function(){dataLayer.push({element_name:void 0})})();</script><script type="text/javascript" id="" charset="">(function(){dataLayer.push({element_name:void 0})})();</script><iframe style="width: 0px; height: 0px; display: none; position: fixed; left: -999px; top: -999px;"></iframe><iframe name="cnftComm" style="width: 0px; height: 0px; display: none; position: fixed; left: -999px; top: -999px;"></iframe><div id="confiant_tag_holder" style="display:none"></div><img src="https://t.co/i/adsct?bci=3&amp;dv=America%2FToronto%26en-US%2Cen%26Google%20Inc.%26MacIntel%26127%261512%26982%2610%2630%261512%26869%260%26na&amp;eci=2&amp;event_id=06f086c5-14f3-4d3c-9b6e-d78bab89d82a&amp;events=%5B%5B%22pageview%22%2C%7B%7D%5D%5D&amp;integration=advertiser&amp;p_id=Twitter&amp;p_user_id=0&amp;pl_id=988847c1-1eac-414e-8ccc-b7106913f90e&amp;pt=XAI's%20Cofounder%20Chaos%2C%20Rebuilding%20Is%20Vintage%20Elon%20Musk%20-%20Business%20Insider&amp;tw_document_href=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;tw_iframe_status=0&amp;tw_order_quantity=0&amp;tw_pid_src=2&amp;tw_sale_amount=0&amp;twpid=tw.1775329853002.236626802142051189&amp;txn_id=o389k&amp;type=javascript&amp;version=2.3.50" height="1" width="1" fetchpriority="high" style="display: none;"><img src="https://analytics.twitter.com/i/adsct?bci=3&amp;dv=America%2FToronto%26en-US%2Cen%26Google%20Inc.%26MacIntel%26127%261512%26982%2610%2630%261512%26869%260%26na&amp;eci=2&amp;event_id=06f086c5-14f3-4d3c-9b6e-d78bab89d82a&amp;events=%5B%5B%22pageview%22%2C%7B%7D%5D%5D&amp;integration=advertiser&amp;p_id=Twitter&amp;p_user_id=0&amp;pl_id=988847c1-1eac-414e-8ccc-b7106913f90e&amp;pt=XAI's%20Cofounder%20Chaos%2C%20Rebuilding%20Is%20Vintage%20Elon%20Musk%20-%20Business%20Insider&amp;tw_document_href=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;tw_iframe_status=0&amp;tw_order_quantity=0&amp;tw_pid_src=2&amp;tw_sale_amount=0&amp;twpid=tw.1775329853002.236626802142051189&amp;txn_id=o389k&amp;type=javascript&amp;version=2.3.50" height="1" width="1" fetchpriority="high" style="display: none;"><iframe id="__bm_locator" name="__bm_locator" width="0" height="0" scrolling="no" src="about:blank" aria-hidden="true" tabindex="-1" style="display: none; width: 0px; height: 0px;"></iframe><img class="ywa-10000" src="https://sp.analytics.yahoo.com/sp.pl?a=10000&amp;d=Sat%2C%2004%20Apr%202026%2019%3A10%3A57%20GMT&amp;n=4d&amp;b=XAI's%20Cofounder%20Chaos%2C%20Rebuilding%20Is%20Vintage%20Elon%20Musk%20-%20Business%20Insider&amp;.yp=10170109&amp;f=https%3A%2F%2Fwww.businessinsider.com%2Felon-musk-xai-cofounder-exits-spacex-ipo-2026-4&amp;e=https%3A%2F%2Fwww.businessinsider.com%2Ftransportation&amp;enc=UTF-8&amp;yv=1.16.6&amp;tagmgr=gtm" alt="dot image pixel" style="display: none;"><iframe id="li_sync_frame" title="data" src="https://i.liadm.com/sync-container?duid=c9c4baefd3f9--01kncyffarxmgpv62khen2jqb9&amp;appId=b-01h4&amp;euns=0&amp;s=Ci0KBQgKEKcdCgYI3QEQpx0KBQgMELEdCgYI9QEQpx0KBgiiARCnHQoFCAsQpx0SNw322cKtEjAKBgjKARCnHQoGCMUBEKcdCgYIxgEQph0KBgjHARClHQoGCMgBEKcdCgYI_gEQpx0SLw3kkThaEigKBgjKARCnHQoGCMUBEKcdCgYIxgEQph0KBgjHARClHQoGCMgBEKcdEicN58XrYRIgCgYIygEQpx0KBgjIARCnHQoGCMYBEKYdCgYIxQEQpx0&amp;version=v3.14.0&amp;cd=.businessinsider.com&amp;pv=02c04537-5971-4b89-95dd-7c3e8bfafa41" style="opacity: 0; width: 0px; height: 0px; border: 0px; position: absolute; top: 0px; left: 0px; z-index: -1000;"></iframe><script type="text/javascript" id="" charset="">(function(){dataLayer.push({element_name:void 0})})();</script><iframe src="https://www.google.com/recaptcha/api2/aframe" width="0" height="0" style="display: none;"></iframe><script type="text/javascript" id="" charset="">(function(){dataLayer.push({element_name:void 0})})();</script><div class="image-modal-modal" role="dialog" aria-modal="true" aria-label="Fullscreen image viewer"><button class="image-modal-close" aria-label="Close fullscreen image viewer">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
      </svg>
    </button><div class="image-modal-image-container" style="touch-action: none;"></div></div><script type="text/javascript" id="" charset="">(function(){dataLayer.push({element_name:void 0})})();</script><div id="tbl-aug-95763"><div id="tbl-aug-9235"><div id="tbl-aug-385"><div class="trc_popover trc_popover_fade trc_bottom"><div class="trc_popover_arrow"></div><div class="popupContentWrapper"><div class="trc_popover_title_wrapper"><div class="trc_popover_title"></div></div><div class="trc_popover_content_wrapper"><div class="trc_popover_content"></div></div></div></div></div></div></div><iframe id="trc-pixel-iframe-5848" name="trc-pixel-iframe-5848" width="0px" height="0px" class="trc-hidden" style="display: none;"></iframe><iframe src="//imprchmp.taboola.com/st?cijs=convusmp&amp;ttype=0&amp;cisd=convusmp&amp;cipid=66361655&amp;crid=-1&amp;dast=V9MgMCABYDAOG1pYbX7xZWBADhtaWG1-8WVgUAAAAABgYA9AcAJDmczXyz5Wgt8Y1cbtHEs3ArV8PlWjhzTDyj1Wg2822GAECSw9nMN1uO1hLfyOUWTTwLt3I1XK6FM8fEM1qNZjPfZgoAGMZymQxqgcRl9vveaofT7tb4za633Q0AT2g6HT7XvV73-90lrs_T7vJ8nnbP0-Sy3DV-t19l9tvdatfn6xY-nG6N3-Z33U0uy1tlfJo-b83h4XEZ30rD3y0ZTGZr0RwAAAAAAB4A_v___yEAAAAAACIAAAAAACQAAAAAACgAAioA_i0ABC4AAAAAADAA_v___zUAAEw2AASeTg4ABfdbTkeD8m_5-gMAAAAAAAQAAAAAgAQAQAB7rAQA4KJ89ATg_________z8GYIA-80YG4P____8GYKEHAODBBwDgQQgAAADgYgjgw-3-fJoYCY4IAEDgl7IIwBHAJIBOAKgALKoA_v__-60AAK4AAAACOrPOpSOzAHQHJd7CAAAAAALEAFbNq7ZY_FGzxgAW6GHx-80Ou8bvdhnA_________78ZwP8ZwD8agNCLB24agLCnfrgawC8gAMAawC8gAAAbgLoB_P-_AQTAAYQcgAuaTofPda_X_X53ievztLs8n6fd8zS5LHeN3-0XXR52z-FvOT1MT7_ddgAAAAAAdwD_____eACr5lVbLP6oWXoAIDmb2IyL0WaxmSxGts1uZPPMbMaNY7BxGFamiWN7AIz2U-GFPCAzfQAa4jL7fW-1w2l3a_xm19tuEB80DMvJIJgfwIQtRqvJZLMczpaLyWA4Go5G-wMYiNFsgAATNBwOFrvBYrdYDCeLyWiwHCwQQCAGEwSgaNFgshqNJovJcDWarGbLxW63QQCKVq1mo81guJpNZrvdajgYLkcjBJiwxWg1mWyWw9lyMRkMR8PRaIgAMTEbrQyT4cSt2i1Wa9HKN1pLXDPLWmPa7QYTz2Jms-3WotfH9BjMZibPZLlFAMEApb1InhbpRDgz7XYT02g2XHhmy91itJsYZjabcTCaLFbLlXEilmhOFulEdtk3ZxObcTHaLDaTxci22Y1snpnNuHEMNg7DyjRx7Buz0cowGU7cqt1itRatfKO1xDWzrDWm3W4w8SxmNttuLXp9TI_BbGbyTJb7xm632kyWw9Vw39jtVpvJcrga7jtMpmfqczaqPmez6PjUrM9V9clg8R3UB9vPpPsthA3zuCg5Oc8htcEYcaYPkrPB47AuvKbHdnJ6Oa_V8Wp4UTgOHoPB6DAZjAZFLBFcpBOJ6_O0uzyfp93zNLksF7FEabpIJ3qV2W93q12fr1v4cLo1fpvfdTe5LG-V8Wn6vDWHh8dlfCsNf7dkMJmtRROxRHC6SCeil_F0Ub8SAAAAAAAAAADAEsAmAAAAAAAngEEMZ6PZbp0AB7GazRaL1XIBAAAGHHQBfsoZklc6WKN2AXB8fw_na28LjwEexPV52l2ez9PueZpclisDADzYRTADbAb4DEAQa7Va1gAAAAAD2AAAAAAB3AC6AXgDCDyd4wD____-9AAAAAD0-wBAUguFHrhR7P8AAAIUYq1Wq9uNtVqtgAACWmxmEwgACDC_KwgAAAAAAAAgczQIAAAAAAAAqKNFCBDYdhMCKAQYDNHyd7u8EJAhAAAAAAAAoArIISAH4i9r6kGT9iEAACCgM-tc2mAi4KA9U4Ni8BlFwP___39FQEEyKIzlLAJyIP6ypng3Ei4CAAACOrPOo6ExAhhiOZwrZ3PNbq4YDg!&amp;cmcv=&amp;pix=undefined&amp;cb=1775329858687&amp;uv=3608&amp;tms=1775329858687&amp;abt=rbcatc_vA!strpl2_vA!strpl2_vB!strpl2_vC!tmaxc_vA!ufm_vE&amp;ru=https://www.businessinsider.com/transportation&amp;ft=0&amp;su=6&amp;unm=FEED_MANAGER&amp;aure=false&amp;agl=1&amp;cirid=986f7694-b7de-4b3a-9589-8f1b34546f73&amp;excid=e22lLINE_ITEM_ID_WILL_BE_HERE_ON_SERVINGc&amp;tst=1&amp;docw=0&amp;cs=true&amp;cias=1" style="display: none;"></iframe><iframe src="https://ch-match.taboola.com/sync?dast=V9MgMCABYDAOG1pYbX7xZWBADhtaWG1-8WVgUAAAAABgYA9AcAJDmczXyz5Wgt8Y1cbtHEs3ArV8PlWjhzTDyj1Wg2822GAECSw9nMN1uO1hLfyOUWTTwLt3I1XK6FM8fEM1qNZjPfZgoAGMZymQxqgcRl9vveaofT7tb4za633Q0AT2g6HT7XvV73-90lrs_T7vJ8nnbP0-Sy3DV-t19l9tvdatfn6xY-nG6N3-Z33U0uy1tlfJo-b83h4XEZ30rD3y0ZTGZr0RwAAAAAAB4A_v___yEAAAAAACIAAAAAACQAAAAAACgAAioA_i0ABC4AAAAAADAA_v___zUAAEw2AASeTg4ABfdbTkeD8m_5-gMAAAAAAAQAAAAAgAQAQAB7rAQA4KJ89ATg_________z8GYIA-80YG4P____8GYKEHAODBBwDgQQgAAADgYgjgw-3-fJoYCY4IAEDgl7IIwBHAJIBOAKgALKoA_v__-60AAK4AAAACOrPOpSOzAHQHJd7CAAAAAALEAFbNq7ZY_FGzxgAW6GHx-80Ou8bvdhnA_________78ZwP8ZwD8agNCLB24agLCnfrgawC8gAMAawC8gAAAbgLoB_P-_AQTAAYQcgAuaTofPda_X_X53ievztLs8n6fd8zS5LHeN3-0XXR52z-FvOT1MT7_ddgAAAAAAdwD_____eACr5lVbLP6oWXoAIDmb2IyL0WaxmSxGts1uZPPMbMaNY7BxGFamiWN7AIz2U-GFPCAzfQAa4jL7fW-1w2l3a_xm19tuEB80DMvJIJgfwIQtRqvJZLMczpaLyWA4Go5G-wMYiNFsgAATNBwOFrvBYrdYDCeLyWiwHCwQQCAGEwSgaNFgshqNJovJcDWarGbLxW63QQCKVq1mo81guJpNZrvdajgYLkcjBJiwxWg1mWyWw9lyMRkMR8PRaIgAMTEbrQyT4cSt2i1Wa9HKN1pLXDPLWmPa7QYTz2Jms-3WotfH9BjMZibPZLlFAMEApb1InhbpRDgz7XYT02g2XHhmy91itJsYZjabcTCaLFbLlXEilmhOFulEdtk3ZxObcTHaLDaTxci22Y1snpnNuHEMNg7DyjRx7Buz0cowGU7cqt1itRatfKO1xDWzrDWm3W4w8SxmNttuLXp9TI_BbGbyTJb7xm632kyWw9Vw39jtVpvJcrga7jtMpmfqczaqPmez6PjUrM9V9clg8R3UB9vPpPsthA3zuCg5Oc8htcEYcaYPkrPB47AuvKbHdnJ6Oa_V8Wp4UTgOHoPB6DAZjAZFLBFcpBOJ6_O0uzyfp93zNLksF7FEabpIJ3qV2W93q12fr1v4cLo1fpvfdTe5LG-V8Wn6vDWHh8dlfCsNf7dkMJmtRROxRHC6SCeil_F0Ub8SAAAAAAAAAADAEsAmAAAAAAAngEEMZ6PZbp0AB7GazRaL1XIBAAAGHHQBfsoZklc6WKN2AXB8fw_na28LjwEexPV52l2ez9PueZpclisDADzYRTADbAb4DEAQa7Va1gAAAAAD2AAAAAAB3AC6AXgDCDyd4wD____-9AAAAAD0-wBAUguFHrhR7P8AAAIUYq1Wq9uNtVqtgAACWmxmEwgACDC_KwgAAAAAAAAgczQIAAAAAAAAqKNFCBDYdhMCKAQYDNHyd7u8EJAhAAAAAAAAoArIISAH4i9r6kGT9iEAACCgM-tc2mAi4KA9U4Ni8BlFwP___39FQEEyKIzlLAJyIP6ypng3Ei4CAAACOrPOo6ExAhhiOZwrZ3PNbq4YDg!&amp;excid=22&amp;docw=0&amp;cijs=1&amp;nlb=false" style="display: none;"></iframe><iframe name="google_ads_top_frame" id="google_ads_top_frame" style="display: none; position: fixed; left: -999px; top: -999px; width: 0px; height: 0px;"></iframe><div class="_cm-communication-input" data-unit-info=""></div><div id="w1775329861564" style="color-scheme: initial; forced-color-adjust: initial; math-depth: initial; position: initial; position-anchor: initial; text-size-adjust: initial; appearance: initial; color: initial; font: initial; font-palette: initial; font-synthesis: initial; position-area: initial; text-orientation: initial; text-rendering: initial; text-spacing-trim: initial; -webkit-font-smoothing: initial; -webkit-locale: initial; -webkit-text-orientation: initial; -webkit-writing-mode: initial; writing-mode: initial; zoom: initial; accent-color: initial; place-content: initial; place-items: initial; place-self: initial; alignment-baseline: initial; anchor-name: initial; anchor-scope: initial; animation-composition: initial; animation: initial; animation-trigger: initial; app-region: initial; aspect-ratio: initial; backdrop-filter: initial; backface-visibility: initial; background: initial; background-blend-mode: initial; baseline-shift: initial; baseline-source: initial; block-size: initial; border-block: initial; border: initial; border-radius: initial; border-collapse: initial; border-end-end-radius: initial; border-end-start-radius: initial; border-inline: initial; border-start-end-radius: initial; border-start-start-radius: initial; inset: initial; box-decoration-break: initial; box-shadow: initial; box-sizing: initial; break-after: initial; break-before: initial; break-inside: initial; buffered-rendering: initial; caption-side: initial; caret-animation: initial; caret-color: initial; caret-shape: initial; clear: initial; clip: initial; clip-path: initial; clip-rule: initial; color-interpolation: initial; color-interpolation-filters: initial; color-rendering: initial; columns: initial; column-fill: initial; gap: initial; column-rule: initial; column-span: initial; contain: initial; contain-intrinsic-block-size: initial; contain-intrinsic-size: initial; contain-intrinsic-inline-size: initial; container: initial; content: initial; content-visibility: initial; corner-shape: initial; corner-block-end-shape: initial; corner-block-start-shape: initial; counter-increment: initial; counter-reset: initial; counter-set: initial; cursor: initial; cx: initial; cy: initial; d: initial; display: block; dominant-baseline: initial; dynamic-range-limit: initial; empty-cells: initial; field-sizing: initial; fill: initial; fill-opacity: initial; fill-rule: initial; filter: initial; flex: initial; flex-flow: initial; float: initial; flood-color: initial; flood-opacity: initial; grid: initial; grid-area: initial; height: 0px; hyphenate-character: initial; hyphenate-limit-chars: initial; hyphens: initial; image-orientation: initial; image-rendering: initial; initial-letter: initial; inline-size: initial; inset-block: initial; inset-inline: initial; interactivity: initial; interest-delay: initial; interpolate-size: initial; isolation: initial; letter-spacing: initial; lighting-color: initial; line-break: initial; list-style: initial; margin-block: initial; margin: initial; margin-inline: initial; marker: initial; mask: initial; mask-type: initial; math-shift: initial; math-style: initial; max-block-size: initial; max-height: initial; max-inline-size: initial; max-width: initial; min-block-size: initial; min-height: initial; min-inline-size: initial; min-width: initial; mix-blend-mode: initial; object-fit: initial; object-position: initial; object-view-box: initial; offset: initial; opacity: initial; order: initial; orphans: initial; outline: initial; outline-offset: initial; overflow-anchor: initial; overflow-block: initial; overflow-clip-margin: initial; overflow-inline: initial; overflow-wrap: initial; overflow: initial; overlay: initial; overscroll-behavior-block: initial; overscroll-behavior-inline: initial; overscroll-behavior: initial; padding-block: initial; padding: initial; padding-inline: initial; page: initial; page-orientation: initial; paint-order: initial; perspective: initial; perspective-origin: initial; pointer-events: initial; position-try: initial; position-visibility: initial; print-color-adjust: initial; quotes: initial; r: initial; reading-flow: initial; reading-order: initial; resize: initial; rotate: initial; ruby-align: initial; ruby-position: initial; rx: initial; ry: initial; scale: initial; scroll-behavior: initial; scroll-initial-target: initial; scroll-margin-block: initial; scroll-margin: initial; scroll-margin-inline: initial; scroll-marker-group: initial; scroll-padding-block: initial; scroll-padding: initial; scroll-padding-inline: initial; scroll-snap-align: initial; scroll-snap-stop: initial; scroll-snap-type: initial; scroll-target-group: initial; scroll-timeline: initial; scrollbar-color: initial; scrollbar-gutter: initial; scrollbar-width: initial; shape-image-threshold: initial; shape-margin: initial; shape-outside: initial; shape-rendering: initial; size: initial; speak: initial; stop-color: initial; stop-opacity: initial; stroke: initial; stroke-dasharray: initial; stroke-dashoffset: initial; stroke-linecap: initial; stroke-linejoin: initial; stroke-miterlimit: initial; stroke-opacity: initial; stroke-width: initial; tab-size: initial; table-layout: initial; text-align: initial; text-align-last: initial; text-anchor: initial; text-autospace: initial; text-box: initial; text-combine-upright: initial; text-decoration: initial; text-decoration-skip-ink: initial; text-emphasis: initial; text-emphasis-position: initial; text-indent: initial; text-justify: initial; text-overflow: initial; text-shadow: initial; text-transform: initial; text-underline-offset: initial; text-underline-position: initial; text-wrap: initial; timeline-scope: initial; timeline-trigger: initial; touch-action: initial; transform: initial; transform-box: initial; transform-origin: initial; transform-style: initial; transition: initial; translate: initial; trigger-scope: initial; user-select: initial; vector-effect: initial; vertical-align: initial; view-timeline: initial; view-transition-class: initial; view-transition-group: initial; view-transition-name: initial; visibility: hidden; border-spacing: initial; -webkit-box-align: initial; -webkit-box-decoration-break: initial; -webkit-box-direction: initial; -webkit-box-flex: initial; -webkit-box-ordinal-group: initial; -webkit-box-orient: initial; -webkit-box-pack: initial; -webkit-box-reflect: initial; -webkit-line-break: initial; -webkit-line-clamp: initial; -webkit-mask-box-image: initial; -webkit-rtl-ordering: initial; -webkit-ruby-position: initial; -webkit-tap-highlight-color: initial; -webkit-text-combine: initial; -webkit-text-decorations-in-effect: initial; -webkit-text-fill-color: initial; -webkit-text-security: initial; -webkit-text-stroke: initial; -webkit-user-drag: initial; white-space-collapse: initial; widows: initial; width: 0px; will-change: initial; word-break: initial; word-spacing: initial; x: initial; y: initial; z-index: initial;"><style>#w1775329861564 *{margin:0;padding:0;position:static;outline:0;background:transparent none;border:none;overflow:visible;visibility:visible;filter:alpha(opacity=100);opacity:1;box-sizing:content-box;-moz-box-sizing:content-box;text-decoration:none;font:normal 12px/1 arial;text-shadow:none;box-shadow:none;color:#000;text-align:left;vertical-align:top;float:none;max-width:none;max-height:none}#w1775329861564 [id$="_ATTRIBUTION"] [tabindex]:active,#w1775329861564 [id$="_ATTRIBUTION"] [tabindex]:focus,#w1775329861564 [id$="_CLOSE"] [tabindex]:active,#w1775329861564 [id$="_CLOSE"] [tabindex]:focus,#w1775329861564 [id$="_ADCHOICES"] [tabindex]:active,#w1775329861564 [id$="_ADCHOICES"] [tabindex]:focus,#w1775329861564 .GGModal_StandAlone [tabindex]:active,#w1775329861564 .GGModal_StandAlone [tabindex]:focus{box-shadow:0px 0px 10px 0px #666 !important;}#w1775329861564 > iframe{display:none!important}#w1775329861564 > ._ar_sc{transition:opacity 0.2s ease}#w1775329861564._hii > ._ar_sc{opacity:0 !important}</style><div id="GG_PXS" aria-hidden="true" style="display:none"><iframe frameborder="0" scrolling="no" name="ggifri1775329861566" src="about:blank" height="100%" width="100%"></iframe></div><script async="" type="text/javascript">(function(win,doc,G,env,undef){try{/* SUP-2995 */
win.ggevents.push({'inscreen.load': function (data) {
    document.querySelector('.mobile-sticky-container').style.display = 'none';
}});
googletag.pubads().addEventListener('slotRequested', function(event) {
    if(event.slot.getSlotElementId().includes('sticky')) {
        if(GUMGUM && GUMGUM.isad) {
            GUMGUM.removeISAd();
            document.querySelector('.mobile-sticky-container').style.display = '';
        }
    }
});}catch(err){GUMGUM.log("Custom JS", err)}}(window,window.document,window.GUMGUM,"desktop"))</script><iframe style="color-scheme: initial; forced-color-adjust: initial; math-depth: initial; position: initial; position-anchor: initial; text-size-adjust: initial; appearance: initial; color: initial; font: initial; font-palette: initial; font-synthesis: initial; position-area: initial; text-orientation: initial; text-rendering: initial; text-spacing-trim: initial; -webkit-font-smoothing: initial; -webkit-locale: initial; -webkit-text-orientation: initial; -webkit-writing-mode: initial; writing-mode: initial; zoom: initial; accent-color: initial; place-content: initial; place-items: initial; place-self: initial; alignment-baseline: initial; anchor-name: initial; anchor-scope: initial; animation-composition: initial; animation: initial; animation-trigger: initial; app-region: initial; aspect-ratio: initial; backdrop-filter: initial; backface-visibility: initial; background: initial; background-blend-mode: initial; baseline-shift: initial; baseline-source: initial; block-size: initial; border-block: initial; border: initial; border-radius: initial; border-collapse: initial; border-end-end-radius: initial; border-end-start-radius: initial; border-inline: initial; border-start-end-radius: initial; border-start-start-radius: initial; inset: initial; box-decoration-break: initial; box-shadow: initial; box-sizing: initial; break-after: initial; break-before: initial; break-inside: initial; buffered-rendering: initial; caption-side: initial; caret-animation: initial; caret-color: initial; caret-shape: initial; clear: initial; clip: initial; clip-path: initial; clip-rule: initial; color-interpolation: initial; color-interpolation-filters: initial; color-rendering: initial; columns: initial; column-fill: initial; gap: initial; column-rule: initial; column-span: initial; contain: initial; contain-intrinsic-block-size: initial; contain-intrinsic-size: initial; contain-intrinsic-inline-size: initial; container: initial; content: initial; content-visibility: initial; corner-shape: initial; corner-block-end-shape: initial; corner-block-start-shape: initial; counter-increment: initial; counter-reset: initial; counter-set: initial; cursor: initial; cx: initial; cy: initial; d: initial; display: block; dominant-baseline: initial; dynamic-range-limit: initial; empty-cells: initial; field-sizing: initial; fill: initial; fill-opacity: initial; fill-rule: initial; filter: initial; flex: initial; flex-flow: initial; float: initial; flood-color: initial; flood-opacity: initial; grid: initial; grid-area: initial; height: 0px; hyphenate-character: initial; hyphenate-limit-chars: initial; hyphens: initial; image-orientation: initial; image-rendering: initial; initial-letter: initial; inline-size: initial; inset-block: initial; inset-inline: initial; interactivity: initial; interest-delay: initial; interpolate-size: initial; isolation: initial; letter-spacing: initial; lighting-color: initial; line-break: initial; list-style: initial; margin-block: initial; margin: initial; margin-inline: initial; marker: initial; mask: initial; mask-type: initial; math-shift: initial; math-style: initial; max-block-size: initial; max-height: initial; max-inline-size: initial; max-width: initial; min-block-size: initial; min-height: initial; min-inline-size: initial; min-width: initial; mix-blend-mode: initial; object-fit: initial; object-position: initial; object-view-box: initial; offset: initial; opacity: initial; order: initial; orphans: initial; outline: initial; outline-offset: initial; overflow-anchor: initial; overflow-block: initial; overflow-clip-margin: initial; overflow-inline: initial; overflow-wrap: initial; overflow: initial; overlay: initial; overscroll-behavior-block: initial; overscroll-behavior-inline: initial; overscroll-behavior: initial; padding-block: initial; padding: initial; padding-inline: initial; page: initial; page-orientation: initial; paint-order: initial; perspective: initial; perspective-origin: initial; pointer-events: initial; position-try: initial; position-visibility: initial; print-color-adjust: initial; quotes: initial; r: initial; reading-flow: initial; reading-order: initial; resize: initial; rotate: initial; ruby-align: initial; ruby-position: initial; rx: initial; ry: initial; scale: initial; scroll-behavior: initial; scroll-initial-target: initial; scroll-margin-block: initial; scroll-margin: initial; scroll-margin-inline: initial; scroll-marker-group: initial; scroll-padding-block: initial; scroll-padding: initial; scroll-padding-inline: initial; scroll-snap-align: initial; scroll-snap-stop: initial; scroll-snap-type: initial; scroll-target-group: initial; scroll-timeline: initial; scrollbar-color: initial; scrollbar-gutter: initial; scrollbar-width: initial; shape-image-threshold: initial; shape-margin: initial; shape-outside: initial; shape-rendering: initial; size: initial; speak: initial; stop-color: initial; stop-opacity: initial; stroke: initial; stroke-dasharray: initial; stroke-dashoffset: initial; stroke-linecap: initial; stroke-linejoin: initial; stroke-miterlimit: initial; stroke-opacity: initial; stroke-width: initial; tab-size: initial; table-layout: initial; text-align: initial; text-align-last: initial; text-anchor: initial; text-autospace: initial; text-box: initial; text-combine-upright: initial; text-decoration: initial; text-decoration-skip-ink: initial; text-emphasis: initial; text-emphasis-position: initial; text-indent: initial; text-justify: initial; text-overflow: initial; text-shadow: initial; text-transform: initial; text-underline-offset: initial; text-underline-position: initial; text-wrap: initial; timeline-scope: initial; timeline-trigger: initial; touch-action: initial; transform: initial; transform-box: initial; transform-origin: initial; transform-style: initial; transition: initial; translate: initial; trigger-scope: initial; user-select: initial; vector-effect: initial; vertical-align: initial; view-timeline: initial; view-transition-class: initial; view-transition-group: initial; view-transition-name: initial; visibility: hidden; border-spacing: initial; -webkit-box-align: initial; -webkit-box-decoration-break: initial; -webkit-box-direction: initial; -webkit-box-flex: initial; -webkit-box-ordinal-group: initial; -webkit-box-orient: initial; -webkit-box-pack: initial; -webkit-box-reflect: initial; -webkit-line-break: initial; -webkit-line-clamp: initial; -webkit-mask-box-image: initial; -webkit-rtl-ordering: initial; -webkit-ruby-position: initial; -webkit-tap-highlight-color: initial; -webkit-text-combine: initial; -webkit-text-decorations-in-effect: initial; -webkit-text-fill-color: initial; -webkit-text-security: initial; -webkit-text-stroke: initial; -webkit-user-drag: initial; white-space-collapse: initial; widows: initial; width: 0px; will-change: initial; word-break: initial; word-spacing: initial; x: initial; y: initial; z-index: initial;"></iframe></div><script type="text/javascript" id="" charset="">(function(){dataLayer.push({action:void 0})})();</script><style>.adBanner{display:block!important;position:absolute!important;top:-1000px!important;left:-10000px!important;background-color:transparent;width:1px!important;height:1px!important}</style><style>.adBanner{display:block!important;position:absolute!important;top:-1000px!important;left:-10000px!important;background-color:transparent;width:1px!important;height:1px!important}</style></body>
"""

print(clean_text(test))