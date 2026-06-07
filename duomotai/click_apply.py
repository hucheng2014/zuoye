from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        print("Connecting to browser...")
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9239")
        except Exception as e:
            print(f"Failed to connect: {e}")
            return
            
        print("Connected.")
        
        # Get the first context and page
        contexts = browser.contexts
        if not contexts:
            print("No contexts found")
            return
            
        context = contexts[0]
        pages = context.pages
        
        if not pages:
            print("No pages found")
            return
            
        page = pages[0]
        
        # In case the user is on a different tab, find the one with the right content
        target_page = page
        for p_iter in pages:
            title = p_iter.title()
            print(f"Tab: {title}")
            # we can look for specific text
            if "申请" in p_iter.content() or "资质审核" in p_iter.content() or "任务说明" in p_iter.content():
                target_page = p_iter
                break
                
        page = target_page
        print(f"Target page title: {page.title()}")
        
        # Wait a bit for page to be fully loaded
        page.wait_for_load_state("networkidle", timeout=5000)
        
        content = page.content()
        # Save HTML for inspection if needed
        with open("page.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Looking for task description and Apply button...")
        
        # Find "立即申请" button and click it
        # We can use multiple selectors
        apply_buttons = page.locator("text=立即申请")
        count = apply_buttons.count()
        print(f"Found {count} '立即申请' buttons")
        
        if count > 0:
            # Click the first one
            try:
                apply_buttons.nth(0).click()
                print("Clicked '立即申请'.")
                page.wait_for_timeout(3000) # wait for next page/modal to load
                page.screenshot(path="after_click.png")
                print("Saved screenshot to after_click.png")
            except Exception as e:
                print(f"Error clicking: {e}")
        else:
            print("Could not find '立即申请' button. Let's try looking at links or buttons:")
            for e in page.locator("button, a").all():
                text = e.text_content()
                if text and "申请" in text:
                    print(f"Possible alternative: {text}")
        
        browser.close()

if __name__ == "__main__":
    run()