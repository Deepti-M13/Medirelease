import asyncio
from playwright.async_api import async_playwright
import sys

async def capture_screenshot():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating to Tata 1mg...")
        try:
            await page.goto("https://www.1mg.com/search/all?name=Crocin", timeout=60000)
            await asyncio.sleep(5) # Wait for load
            await page.screenshot(path="1mg_search.png")
            print("Screenshot saved to 1mg_search.png")
            
            # Print some HTML to see class names
            content = await page.content()
            with open("1mg_page.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("HTML saved to 1mg_page.html")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_screenshot())
