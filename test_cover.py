"""
Simple backend-only test script to generate a cover and poll status.

Usage (PowerShell):
  # Set your JWT token and story id
  $env:AUTH_TOKEN = "<YOUR_BEARER_TOKEN>"
  $env:STORY_ID = "123"
  # Optional: change base url
  $env:BASE_URL = "http://127.0.0.1:8000"

  # Run
  python test_cover.py --story-id $env:STORY_ID --timeout 180 --interval 8

You can also pass --token and --base-url flags directly instead of env vars.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Optional

import requests


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.environ.get(name)
    return value if value is not None and value != "" else default


def build_headers(token: Optional[str]) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def main() -> int:
    parser = argparse.ArgumentParser(description="Test cover generation via backend endpoints")
    parser.add_argument("--base-url", default=get_env("BASE_URL", "http://127.0.0.1:8000"), help="API base URL")
    parser.add_argument("--story-id", type=int, default=int(get_env("STORY_ID", "0")), help="Story ID to generate cover for")
    parser.add_argument("--token", default=get_env("AUTH_TOKEN"), help="Bearer token for auth (or set AUTH_TOKEN env)")
    parser.add_argument("--timeout", type=int, default=180, help="Max seconds to wait for completion")
    parser.add_argument("--interval", type=int, default=8, help="Polling interval seconds")
    parser.add_argument("--download", action="store_true", help="Download the final image to ./cover_<story>.jpg/png if available")

    args = parser.parse_args()

    if not args.story_id:
        print("ERROR: --story-id or STORY_ID env is required", file=sys.stderr)
        return 2
    if not args.token:
        print("ERROR: --token or AUTH_TOKEN env is required", file=sys.stderr)
        return 2

    headers = build_headers(args.token)
    base = args.base_url.rstrip("/")

    # 1) Kick off generation
    gen_url = f"{base}/story/{args.story_id}/generate_cover"
    print(f"POST {gen_url}")
    try:
        resp = requests.post(gen_url, headers=headers, timeout=30)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1

    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except Exception:
        print(resp.text)

    if resp.status_code >= 400:
        return 1

    # 2) Poll status
    status_url = f"{base}/story/{args.story_id}/cover_status"
    print(f"\nPolling {status_url} every {args.interval}s for up to {args.timeout}s...")
    deadline = time.time() + args.timeout
    last_status = None
    final_payload = None

    while time.time() < deadline:
        try:
            s_resp = requests.get(status_url, headers=headers, timeout=15)
            payload = s_resp.json()
        except Exception as e:
            print(f"Status check failed: {e}")
            time.sleep(args.interval)
            continue

        status = payload.get("status") or payload.get("cover_generation_status")
        if status != last_status:
            print(f"Status: {status}")
            last_status = status

        if status in {"completed", "failed"}:
            final_payload = payload
            break

        time.sleep(args.interval)

    if final_payload is None:
        print("Timeout waiting for completion")
        return 124  # ETIME

    print("\nFinal payload:")
    print(final_payload)

    if final_payload.get("status") != "completed":
        return 1

    if args.download:
        image_url = final_payload.get("cover_image_url")
        if image_url:
            try:
                img = requests.get(image_url, timeout=60).content
                # Guess extension
                ext = "png" if image_url.lower().endswith(".png") else "jpg"
                out_path = f"cover_{args.story_id}.{ext}"
                with open(out_path, "wb") as f:
                    f.write(img)
                print(f"Saved image to {out_path}")
            except Exception as e:
                print(f"Failed to download image: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


