import json
import os
import sys

def setup():
    print("=" * 60)
    print("YouTube Music Auth Setup for 'The Alarm Demon'")
    print("=" * 60)
    print("\nTo access your private Top Songs and Listening History:")
    print("1. Open Chrome/Edge/Firefox and log in to https://music.youtube.com")
    print("2. Press F12 to open Developer Tools -> go to the 'Network' tab.")
    print("3. Filter by 'browse' or click on 'Library'.")
    print("4. Right click on any request to music.youtube.com -> Copy -> Copy request headers.")
    print("5. Paste the entire header text into a file named 'browser_headers.txt' in this directory.\n")
    
    headers_file = "browser_headers.txt"
    if not os.path.exists(headers_file):
        with open(headers_file, "w", encoding="utf-8") as f:
            f.write("PASTE_YOUR_REQUEST_HEADERS_HERE\n")
        print(f"Created template '{headers_file}'. Fill it in and re-run this script.")
        return

    try:
        from ytmusicapi import setup as yt_setup
        yt_setup(filepath="oauth.json", headers_raw=open(headers_file, "r", encoding="utf-8").read())
        print("\n[SUCCESS] 'oauth.json' successfully generated!")
        print("You can now run 'python main.py' to fetch and build your alarm snippets.")
    except Exception as e:
        print(f"\n[ERROR] Failed to parse headers: {e}")
        print("Make sure you copied raw request headers including Cookie and Authorization.")

if __name__ == "__main__":
    setup()
