import os
import json
import logging
import urllib.request
import urllib.error
import urllib.parse

logger = logging.getLogger(__name__)

def upload_to_github_release(file_path: str, repo: str, token: str, tag: str = "latest") -> bool:
    """Uploads an asset to a GitHub Release under the specified tag."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ytm-ios-alarm"
    }

    # 1. Fetch or create release
    release_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    release_data = None
    try:
        req = urllib.request.Request(release_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            release_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            create_url = f"https://api.github.com/repos/{repo}/releases"
            payload = json.dumps({
                "tag_name": tag,
                "name": "Latest Daily Alarm",
                "body": "Automated alarm snippet generated from playlist.",
                "draft": False,
                "prerelease": False
            }).encode()
            req = urllib.request.Request(create_url, data=payload, headers={**headers, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req) as resp:
                    release_data = json.loads(resp.read().decode())
            except Exception as create_err:
                logger.error(f"Failed to create release: {create_err}")
                return False
        else:
            logger.error(f"GitHub API error: {e}")
            return False

    if not release_data or "id" not in release_data:
        return False

    # 2. Delete existing asset with matching filename
    file_name = os.path.basename(file_path)
    for asset in release_data.get("assets", []):
        if asset.get("name") == file_name:
            delete_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset['id']}"
            del_req = urllib.request.Request(delete_url, headers=headers, method="DELETE")
            try:
                with urllib.request.urlopen(del_req):
                    pass
            except Exception as del_err:
                logger.debug(f"Could not delete old asset: {del_err}")

    # 3. Upload asset
    upload_url = release_data.get("upload_url", "").split("{")[0]
    upload_url = f"{upload_url}?name={urllib.parse.quote(file_name)}"

    with open(file_path, "rb") as f:
        data = f.read()

    upload_headers = {
        **headers,
        "Content-Type": "audio/mp4",
        "Content-Length": str(len(data))
    }

    req = urllib.request.Request(upload_url, data=data, headers=upload_headers, method="POST")
    try:
        with urllib.request.urlopen(req):
            logger.info(f"Uploaded {file_name} -> https://github.com/{repo}/releases/latest/download/{file_name}")
            return True
    except Exception as upload_err:
        logger.error(f"Failed to upload asset: {upload_err}")
        return False
