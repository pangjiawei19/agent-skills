#!/usr/bin/env bash
# Fetch WeChat public account article content with image extraction.
# Usage: ./fetch_wechat_article.sh <url> [output_dir]
# Returns: JSON with title, text, images (with paths for later analysis)
# Exit codes: 0=success, 1=error

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <wechat-article-url> [output_dir]" >&2
  exit 1
fi

URL="$1"
OUTPUT_DIR="${2:-/tmp/wechat-images}"
mkdir -p "$OUTPUT_DIR"

UA="Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.44"

# Fetch HTML and process with Python
curl -sL -H "User-Agent: ${UA}" "${URL}" | python3 -c "
import sys, re, html, os, json, urllib.request

raw = sys.stdin.read()
output_dir = '${OUTPUT_DIR}'

# Title from #activity-name
title_m = re.search(r'id=\"activity-name\"[^>]*>(.*?)</h1>', raw, re.DOTALL)
title = html.unescape(re.sub(r'<[^>]+>', '', title_m.group(1)).strip()) if title_m else 'Unknown'

# Content from #js_content
content_m = re.search(
    r'id=\"js_content\"[^>]*>(.*?)(?=</div>\s*(?:<script|<div class=\"rich_media_))',
    raw, re.DOTALL
)
if not content_m:
    start = raw.find('id=\"js_content\"')
    if start == -1:
        print(json.dumps({'error': 'Cannot extract article content'}), file=sys.stderr)
        sys.exit(1)
    pos = raw.find('>', start) + 1
    depth = 1
    i = pos
    while i < len(raw) and depth > 0:
        if raw[i:i+6].lower() == '<div ':
            depth += 1
        elif raw[i:i+8].lower() == '</div>':
            depth -= 1
            if depth == 0:
                content_html = raw[pos:i]
                break
        i += 1
    else:
        print(json.dumps({'error': 'Cannot extract article content'}), file=sys.stderr)
        sys.exit(1)
else:
    content_html = content_m.group(1)

# Extract images
img_pattern = r'<img[^>]+src=[\"\\']([^\"\\']+)[\"\\']'
img_matches = re.findall(img_pattern, content_html, re.IGNORECASE)
data_src_pattern = r'<img[^>]+data-src=[\"\\']([^\"\\']+)[\"\\']'
data_src_matches = re.findall(data_src_pattern, content_html, re.IGNORECASE)
all_imgs = list(dict.fromkeys(img_matches + data_src_matches))

# Filter and download images (no limit)
downloaded_images = []
img_positions = {}  # map from original img index to downloaded image index
for idx, img_url in enumerate(all_imgs):
    # Filter out obvious non-content images
    # Skip: icons, emojis, loading, placeholders
    if any(skip in img_url.lower() for skip in ['icon', 'emoji', 'loading', 'placeholder']):
        continue
    
    # Allow mmbiz.qpic.cn images (WeChat's image CDN)
    # Only skip specific PNG types that are usually decorative
    if 'mmbiz.qpic.cn/mmbiz_png' in img_url.lower():
        # Check if it's likely a decorative element
        if any(deco in img_url.lower() for deco in ['icon', 'qr', 'code', 'guide']):
            continue
    
    img_url_clean = img_url.split('?')[0] if '?' in img_url else img_url
    ext = 'jpg'
    if '.png' in img_url.lower():
        ext = 'png'
    elif '.gif' in img_url.lower():
        ext = 'gif'
    elif '.webp' in img_url.lower():
        ext = 'webp'
    
    filename = f'img_{idx:03d}.{ext}'
    filepath = os.path.join(output_dir, filename)
    
    try:
        req = urllib.request.Request(img_url, headers={'User-Agent': '${UA}'})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        
        if os.path.getsize(filepath) < 1024:
            os.remove(filepath)
            continue
        
        img_index = len(downloaded_images)
        downloaded_images.append({
            'index': img_index,
            'filename': filename,
            'path': filepath,
            'original_url': img_url,
            'workspace_path': f'/home/node/.openclaw/workspace/{filename}'
        })
        img_positions[img_url] = img_index
        print(f'Downloaded: {filename} ({os.path.getsize(filepath)} bytes)', file=sys.stderr)
    except Exception as e:
        print(f'Failed to download {img_url}: {e}', file=sys.stderr)
        img_index = len(downloaded_images)
        downloaded_images.append({
            'index': img_index,
            'filename': None,
            'path': None,
            'original_url': img_url,
            'workspace_path': None,
            'error': str(e)
        })
        img_positions[img_url] = img_index
        continue

# Extract plain text with image placeholders
# Replace <img> tags with [IMAGE_N] placeholders before stripping HTML
def replace_img_tag(m):
    tag = m.group(0)
    # Try data-src first (WeChat lazy-load), then src
    src_m = re.search(r'data-src=[\"\\']([^\"\\']+)[\"\\']', tag)
    if not src_m:
        src_m = re.search(r'src=[\"\\']([^\"\\']+)[\"\\']', tag)
    if src_m:
        url = src_m.group(1)
        if url in img_positions:
            return f'\n[IMAGE_{img_positions[url]}]\n'
    return ''

text = re.sub(r'<img[^>]*>', replace_img_tag, content_html, flags=re.IGNORECASE)
text = re.sub(r'<[^>]+>', '\n', text)
text = html.unescape(text)
text = re.sub(r'\n{3,}', '\n\n', text).strip()

# Build output
result = {
    'title': title,
    'text': text,
    'images': downloaded_images,
    'image_count': len(downloaded_images),
    'output_dir': output_dir,
    'usage_hint': {
        'analyze_images': 'Copy images to workspace and use image tool:',
        'example': 'cp /tmp/wechat-images/img_000.jpg /home/node/.openclaw/workspace/ && openclaw image --image /home/node/.openclaw/workspace/img_000.jpg --prompt \"分析图片内容\"'
    }
}

print(json.dumps(result, ensure_ascii=False, indent=2))
"
