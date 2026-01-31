#!/usr/bin/env python3
"""Test mobile UI with sample data."""
from __future__ import annotations

import sys
import time
from playwright.sync_api import sync_playwright


def test_mobile_ui_with_data(base_url: str = "http://localhost:5000", room: str = "testroom"):
    """Test mobile UI with sample data and capture screenshots."""
    with sync_playwright() as p:
        print("Launching Chromium in mobile emulation mode...")
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            viewport={"width": 375, "height": 667},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
        )

        page = context.new_page()
        url = f"{base_url}/r/{room}"
        print(f"Navigating to {url}...")
        page.goto(url)
        page.wait_for_selector(".list-grid", timeout=5000)

        # Add some test items
        print("Adding test data...")
        test_movies = [
            {"title_id": "tt0111161", "title": "The Shawshank Redemption", "year": "1994", "type_label": "movie"},
            {"title_id": "tt0068646", "title": "The Godfather", "year": "1972", "type_label": "movie"},
            {"title_id": "tt0468569", "title": "The Dark Knight", "year": "2008", "type_label": "movie"},
            {"title_id": "tt0167260", "title": "The Lord of the Rings: The Return of the King", "year": "2003", "type_label": "movie"},
        ]

        for movie in test_movies:
            page.evaluate(f"""
                fetch('/api/list', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        room: '{room}',
                        title_id: '{movie["title_id"]}',
                        title: '{movie["title"]}',
                        year: '{movie["year"]}',
                        type_label: '{movie["type_label"]}'
                    }})
                }});
            """)
            time.sleep(0.2)

        # Reload to show the items
        print("Reloading page with data...")
        page.reload()
        page.wait_for_selector(".card", timeout=5000)
        time.sleep(1)  # Wait for any animations

        # Check mobile mode
        body_class = page.locator("body").get_attribute("class")
        is_mobile = "is-mobile" in (body_class or "")
        print(f"Mobile mode: {'✓' if is_mobile else '✗'}")

        # Count cards
        cards = page.locator(".card")
        card_count = cards.count()
        print(f"Found {card_count} card(s)")

        if card_count > 0:
            first_card = cards.first

            # Check drag handle visibility
            mobile_handle = first_card.locator(".card-drag-handle-mobile")
            desktop_handle = first_card.locator(".card-drag-handle-desktop")

            mobile_visible = mobile_handle.is_visible() if mobile_handle.count() > 0 else False
            desktop_visible = desktop_handle.is_visible() if desktop_handle.count() > 0 else False

            print(f"Mobile drag handle: {'✓ visible' if mobile_visible else '✗ hidden'}")
            print(f"Desktop drag handle: {'✓ visible' if desktop_visible else '✗ hidden'}")

            # Check card dimensions
            card_height = first_card.evaluate("el => el.offsetHeight")
            card_width = first_card.evaluate("el => el.offsetWidth")
            print(f"Card dimensions: {card_width}px × {card_height}px")

            if card_height > 150:
                print(f"⚠ Warning: Card height seems tall ({card_height}px)")
            else:
                print(f"✓ Card height looks good ({card_height}px)")

            # Check if card-meta-row contains drag handle
            meta_row = first_card.locator(".card-meta-row")
            if meta_row.count() > 0:
                meta_handle = meta_row.locator(".card-drag-handle-mobile")
                handle_in_meta = meta_handle.count() > 0
                print(f"Drag handle in meta-row: {'✓ yes' if handle_in_meta else '✗ no'}")

            # Check card-row-actions visibility
            row_actions = first_card.locator(".card-row-actions")
            if row_actions.count() > 0:
                actions_visible = row_actions.is_visible()
                print(f"Card-row-actions: {'✗ visible (should be hidden!)' if actions_visible else '✓ hidden'}")

        # Take screenshot of list
        screenshot_dir = "/tmp/claude-1000/-home-massimo-repos-shovo/bfccc0b9-a9be-40b6-a07d-22cef65ca8f3/scratchpad"
        screenshot_path = f"{screenshot_dir}/mobile_cards_layout.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 Screenshot saved to: {screenshot_path}")

        # Test swipe on first card
        if card_count > 0:
            print("\n--- Testing Swipe Gesture ---")
            card = cards.first
            card_box = card.bounding_box()

            if card_box:
                # Take screenshot before swipe
                before_swipe = f"{screenshot_dir}/before_swipe.png"
                page.screenshot(path=before_swipe)
                print(f"📸 Before swipe: {before_swipe}")

                # Simulate swipe left
                start_x = card_box["x"] + card_box["width"] - 50
                start_y = card_box["y"] + card_box["height"] / 2
                end_x = card_box["x"] + 50
                end_y = start_y

                print(f"Swiping from ({start_x:.0f}, {start_y:.0f}) to ({end_x:.0f}, {end_y:.0f})")

                # Use mouse events to simulate touch swipe
                page.mouse.move(start_x, start_y)
                page.mouse.down()
                time.sleep(0.1)
                page.mouse.move(end_x, end_y)
                time.sleep(0.1)
                page.mouse.up()

                # Wait for animation
                time.sleep(0.5)

                # Check swipe state
                card_class = card.get_attribute("class")
                is_swiping = "swiping" in (card_class or "")
                print(f"Swiping state: {'✓ active' if is_swiping else '✗ not active'}")
                print(f"Card classes: {card_class}")

                # Check if swipe actions are visible
                left_action = card.locator(".card-swipe-left")
                right_action = card.locator(".card-swipe-right")

                left_visible = left_action.is_visible() if left_action.count() > 0 else False
                right_visible = right_action.is_visible() if right_action.count() > 0 else False

                print(f"Left swipe action: {'✓ visible' if left_visible else '✗ hidden'}")
                print(f"Right swipe action: {'✓ visible' if right_visible else '✗ hidden'}")

                # Take screenshot during swipe
                during_swipe = f"{screenshot_dir}/during_swipe.png"
                page.screenshot(path=during_swipe)
                print(f"📸 During swipe: {during_swipe}")

        browser.close()
        print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    room = sys.argv[2] if len(sys.argv) > 2 else "testmobile"

    try:
        test_mobile_ui_with_data(base_url, room)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
