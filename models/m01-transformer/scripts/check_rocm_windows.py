import urllib.request
import re

url = "https://repo.radeon.com/rocm/windows/"
html = urllib.request.urlopen(url).read().decode('utf-8')
releases = re.findall(r'href=["\'](rocm-rel-[^"\']+)["\']', html)
print("Available ROCm Windows Releases:")
for r in releases:
    print(" -", r)

latest_rel = releases[-1] if releases else "rocm-rel-7.2.1/"
print(f"\nInspecting latest release: {latest_rel}")
sub_url = url + latest_rel
sub_html = urllib.request.urlopen(sub_url).read().decode('utf-8')
wheels = re.findall(r'href=["\']([^"\']+\.whl)["\']', sub_html)
print(f"Found {len(wheels)} wheels in {latest_rel}:")
for w in wheels:
    print("   *", w)
