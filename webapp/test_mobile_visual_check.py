#!/usr/bin/env python3
"""Capture mobile UI screenshots to verify layout issues."""
from __future__ import annotations

import sys
from playwright.sync_api import sync_playwright


def capture_mobile_screenshots(base_url: str = "http://localhost:5000", room: str = "mona"):
    """Capture mobile UI screenshots for visual verification.

    Args:
        base_url: Base URL of the app
        room: Room name to test
    """
    screenshot_dir = "/tmp/claude-1000/-home-massimo-repos-shovo/bfccc0b9-a9be-40b6-a07d-22cef65ca8f3/scratchpad"

    with sync_playwright() as p:
        print("Launching browser in mobile mode...")
        browser = p.chromium.launch(headless=True)

        # iPhone-like mobile viewport
        context = browser.new_context(
            viewport={"width": 375, "height": 667},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
        )

        page = context.new_page()

        # Navigate to the app
        url = f"{base_url}/r/{room}"
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")

        # Wait for content to load
        page.wait_for_selector(".list-grid", timeout=10000)
        print("Page loaded!")

        # Take full page screenshot
        full_screenshot = f"{screenshot_dir}/mobile_full_page.png"
        page.screenshot(path=full_screenshot, full_page=True)
        print(f"📸 Full page screenshot: {full_screenshot}")

        # Take viewport screenshot (what user sees without scrolling)
        viewport_screenshot = f"{screenshot_dir}/mobile_viewport.png"
        page.screenshot(path=viewport_screenshot)
        print(f"📸 Viewport screenshot: {viewport_screenshot}")

        # Check for cards and measure their dimensions
        cards = page.locator(".card")
        card_count = cards.count()
        print(f"\nFound {card_count} cards")

        if card_count > 0:
            first_card = cards.first

            # Get card dimensions
            card_box = first_card.bounding_box()
            if card_box:
                viewport_width = 375
                gap_right = viewport_width - (card_box["x"] + card_box["width"])
                print(f"Card width: {card_box['width']}px")
                print(f"Card height: {card_box['height']}px")
                print(f"Gap on right: {gap_right}px")

                if gap_right > 20:
                    print(f"⚠️  WARNING: Large gap on right ({gap_right}px)")

            # Check mini-poster dimensions
            poster = first_card.locator(".card-mini-poster")
            if poster.count() > 0:
                poster_box = poster.bounding_box()
                if poster_box and card_box:
                    poster_height = poster_box["height"]
                    card_height = card_box["height"]
                    ratio = poster_height / card_height if card_height > 0 else 0
                    print(f"\nMini-poster height: {poster_height}px")
                    print(f"Poster/Card height ratio: {ratio:.2%}")

                    if ratio < 0.7:
                        print(f"⚠️  WARNING: Mini-poster too small (only {ratio:.2%} of card height)")

        # Check search box dimensions
        search_box = page.locator("#search-input")
        if search_box.count() > 0:
            search_box_dims = search_box.bounding_box()
            if search_box_dims:
                print(f"\nSearch box width: {search_box_dims['width']}px")
                print(f"Search box position: x={search_box_dims['x']}px")

                if search_box_dims['width'] < 200:
                    print(f"⚠️  WARNING: Search box too narrow ({search_box_dims['width']}px)")

        browser.close()
        print("\n✅ Screenshots captured successfully!")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    room = sys.argv[2] if len(sys.argv) > 2 else "mona"

    try:
        capture_mobile_screenshots(base_url, room)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
