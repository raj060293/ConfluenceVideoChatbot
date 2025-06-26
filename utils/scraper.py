import os
import re
import hashlib
import tempfile
import subprocess
import requests
from urllib.parse import urlparse, quote
import shlex
import subprocess
import os


def get_page_id_from_url(url):
    match = re.search(r'/pages/(\d+)', url)
    if match:
        return match.group(1)
    segments = url.split("/")
    for i, seg in enumerate(segments):
        if seg == "pages" and i + 1 < len(segments):
            potential_id = segments[i + 1]
            if potential_id.isdigit():
                return potential_id
    return None


def is_valid_mp4(file_path):
    result = subprocess.run(["file", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"📦 File type check: {result.stdout.strip()}")
    return "MP4" in result.stdout or "ISO Media" in result.stdout



def download_video_with_curl(url, email, api_token, output_path):
    """
    Uses curl via subprocess with properly quoted URL and authentication.
    """
    auth = f"{email}:{api_token}"

    # Escape URL for shell
    escaped_url = shlex.quote(url)
    escaped_output = shlex.quote(output_path)

    # Build full shell command exactly like you'd type in terminal
    cmd = f'curl -L -u "{auth}" {escaped_url} -o {escaped_output}'
    print(f"🚀 Running curl command: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,  # <--- let shell handle quotes/escapes
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode == 0 and os.path.exists(output_path) and is_valid_mp4(output_path):
            print("✅ curl succeeded")
            return output_path
        else:
            print("❌ curl failed")
            print("stderr:", result.stderr)
            if os.path.exists(output_path):
                with open(output_path, "r", encoding="utf-8", errors="ignore") as f:
                    print("📄 File contents (start):", f.read(500))
            return None

    except Exception as e:
        print(f"❌ Exception running curl: {e}")
        return None



def extract_video_url(confluence_url, email, api_token, cache_key=None):
    page_id = get_page_id_from_url(confluence_url)
    if not page_id:
        print("❌ Could not extract page ID.")
        return None

    base_url = urlparse(confluence_url).scheme + "://" + urlparse(confluence_url).netloc
    auth = (email, api_token)
    headers = {"Accept": "application/json"}

    # Setup cache
    cache_dir = os.path.join(tempfile.gettempdir(), "confluence_video_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_key = cache_key or confluence_url + email
    cache_file = os.path.join(cache_dir, hashlib.sha256(cache_key.encode()).hexdigest() + ".mp4")

    if os.path.exists(cache_file):
        print(f"🧠 Using cached video: {cache_file}")
        return cache_file

    # Step 1: Fetch attachments
    attachment_url = f"{base_url}/wiki/rest/api/content/{page_id}/child/attachment"
    print(f"🔍 Fetching attachments from: {attachment_url}")
    response = requests.get(attachment_url, headers=headers, auth=auth)

    if response.status_code == 200:
        attachments = response.json().get("results", [])
        for result in attachments:
            media_type = result.get("metadata", {}).get("mediaType", "")
            if media_type.startswith("video"):
                title = result.get("title", "video.mp4")
                safe_title = quote(title)
                download_path = result["_links"]["download"].rsplit('/', 1)[0] + '/' + safe_title
                download_url = base_url + "/wiki" + download_path

                print(f"🔗 Found video: {title}")
                print(f"➡️ Trying curl download from: {download_url}")
                return download_video_with_curl(download_url, email, api_token, cache_file)

        print("❌ No video attachments found.")
    else:
        print(f"❌ Failed to retrieve attachments. Status: {response.status_code}")
        print(response.text)

    return None
