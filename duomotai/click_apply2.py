from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9239")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return
            
        context = browser.contexts[0]
        pages = context.pages
        
        target_page = pages[0]
        for p_iter in pages:
            if "申请" in p_iter.content():
                target_page = p_iter
                break
                
        page = target_page
        print(f"Current Title: {page.title()}")
        
        # Look for buttons specifically
        buttons = page.locator("button:has-text('立即申请')")
        count = buttons.count()
        print(f"Found {count} buttons with text '立即申请'")
        
        if count > 0:
            for i in range(count):
                btn = buttons.nth(i)
                # Check if visible
                if btn.is_visible():
                    print(f"Clicking button {i}...")
                    btn.click()
                    page.wait_for_timeout(3000)
                    
                    # See if new page opened or URL changed
                    print(f"After click title: {page.title()}, url: {page.url}")
                    page.screenshot(path=f"after_click_btn_{i}.png")
                    
                    # Print all open pages in case a new tab opened
                    for i, p_iter in enumerate(context.pages):
                        print(f"Page {i}: {p_iter.title()} - {p_iter.url}")
                        p_iter.screenshot(path=f"page_{i}.png")
                    break

        browser.close()

if __name__ == "__main__":
    run()