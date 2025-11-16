"""
Screenshot module for rendering HTML and taking screenshots using Selenium.
"""

import tempfile
import time
import re
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

def clean_forwarded_message(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove any element containing forwarded text
    for tag in soup.find_all(text=re.compile("--- Forwarded message ---", re.IGNORECASE)):
        parent = tag.parent
        parent.decompose()  # Completely delete the block

    return str(soup)

def html_to_screenshot(html_content, out_path="email.png"):
    """
    Render HTML content and take a screenshot using headless Chrome.
    
    Args:
        html_content: HTML string to render
        out_path: Output path for the screenshot
    
    Returns:
        Path to the saved screenshot
    """
    # Remove <div dir="ltr" class="gmail_attr"> if it contains the forwarded message heading
    pattern = r'(<div[^>]*class="gmail_attr"[^>]*>.*?--- Forwarded message. ---*?</div>)'
    html_content = re.sub(pattern, '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = clean_forwarded_message(html_content)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1200,1600')

    # Correct WebDriver initialization
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # write temp file
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        fname = f.name

    driver.get('file://' + fname)
    time.sleep(0.5)
    driver.save_screenshot(out_path)
    driver.quit()

    return out_path

# html_to_screenshot("template.html")