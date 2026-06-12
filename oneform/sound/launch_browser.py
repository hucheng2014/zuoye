import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        # Launch a new controlled browser window
        browser = await p.chromium.launch(
            headless=False,  # Show the browser window
            args=["--start-maximized"],
        )

        # Create a new context and page
        context = await browser.new_context()
        page = await context.new_page()

        print("Controlled browser window opened!")
        print("You can navigate to any website, and I can interact with it.")
        print("Press Ctrl+C to close the browser.")

        # Keep the browser open
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await browser.close()
            print("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())
