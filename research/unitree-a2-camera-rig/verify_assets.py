"""Verify downloaded reference bytes and local dossier links; no network required."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
MANIFESTS = [
    "a2-cad/download-manifest.json",
    "a2-mounting/assets-manifest.json",
    "a2-mounting/manual-manifest.json",
    "printer-cameras/download-manifest.json",
    "v1-cover-update/cover-research/cad-download-manifest.json",
    "v1-cover-update/cover-research/reference-images-manifest.json",
    "v1-cover-update/cover-research/step-inspection.json",
    "v1-cover-update/cover-research/bare-a2-download-manifest.json",
    "v1-cover-update/quick-release/download-manifest.json",
]


def main():
    checked = 0
    issues = []
    unavailable_urls = []
    for relative in MANIFESTS:
        manifest = ROOT / relative
        data = json.loads(manifest.read_text())
        records = data.get("assets", [data]) if isinstance(data, dict) else data
        if isinstance(data, dict) and isinstance(data.get("step"), dict):
            records = records + [data["step"]]
        for record in records:
            if record.get("error") and not record.get("path", record.get("file")):
                unavailable_urls.append({"url": record["source_url"], "error": record["error"]})
                continue
            p = Path(record.get("path", record.get("file", record.get("friendly_file", record.get("name", "")))))
            if not p.is_absolute():
                p = manifest.parent / p
            if not p.is_file():
                issues.append(f"Missing: {p}")
                continue
            content = p.read_bytes()
            if hashlib.sha256(content).hexdigest() != record["sha256"]:
                issues.append(f"SHA-256 mismatch: {p}")
            size = record.get("bytes", record.get("size_bytes"))
            if size is not None and len(content) != size:
                issues.append(f"Size mismatch: {p}")
            if record.get("upstream_blob_sha"):
                git_blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
                if git_blob != record["upstream_blob_sha"]:
                    issues.append(f"Git blob mismatch: {p}")
            checked += 1
    local_link_count = 0
    for relative in ["README.md", "v1-cover-update/README.md"]:
        doc = ROOT / relative
        links = re.findall(r"\]\(([^)]+)\)", doc.read_text())
        local_links = [x for x in links if not x.startswith(("https:", "http:", "#"))]
        local_link_count += len(local_links)
        for link in local_links:
            if not (doc.parent / link.split("#")[0]).exists():
                issues.append(f"Broken dossier link in {relative}: {link}")
    for relative in ["design-inputs.json", "printer-cameras/design-inputs.json"]:
        json.loads((ROOT / relative).read_text())
    result = {"source_records_checked": checked, "local_dossier_links_checked": local_link_count, "unavailable_download_urls_logged": unavailable_urls, "issues": issues}
    print(json.dumps(result, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
