#!/usr/bin/env python3
"""
Build presentation slides from thetalk.org
Uses org-python to convert org-mode to HTML
"""
import orgparse
from orgpython import to_html
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re

def slugify(text):
    """Convert text to filename"""
    text = re.sub(r'[^\w\s-]', '', text)
    text = text.lower().replace(' ', '-')
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def org_body_to_html(body):
    """Convert org-mode body to clean semantic HTML"""
    if not body:
        return ""

    # Convert org to HTML (org-python handles org-mode links natively)
    html = to_html(body, toc=False, highlight=False)

    # Fix org-python bug: add space after links when followed by non-whitespace
    html = re.sub(r'</a>([^\s<])', r'</a> \1', html)

    # Wrap pre contents with code tags for highlight.js
    def wrap_code(match):
        import html
        attrs = match.group(1)
        content = match.group(2).strip()

        # HTML escape the content to prevent XML/HTML tags from being interpreted
        content = html.escape(content)

        # Extract language from class="src src-bash" and convert to language-bash
        lang_match = re.search(r'src-(\w+)', attrs)
        if lang_match:
            lang = lang_match.group(1)
            code_class = f' class="language-{lang}"'
            # Remove src classes from pre, keep other attributes
            attrs = re.sub(r'\s*class="[^"]*src[^"]*"', '', attrs)
        else:
            code_class = ''

        return f'<pre{attrs}><code{code_class}>{content}</code></pre>'

    html = re.sub(
        r'<pre([^>]*)>(.*?)</pre>',
        wrap_code,
        html, flags=re.DOTALL
    )

    return html

def parse_grid(body):
    """Parse grid items (format: - Name: Description)"""

    items = []
    for line in body.strip().split('\n'):
        line = line.strip()
        if line.startswith('- ') and ':' in line:
            content = line[2:].strip()
            parts = content.split(':', 1)
            if len(parts) == 2:
                items.append({'name': parts[0].strip(), 'description': parts[1].strip()})

    return items

def parse_images_property(images_prop):
    """Parse IMAGES property: img1.jpg|Caption 1;img2.jpg|Caption|Subcaption"""
    if not images_prop:
        return []

    images = []
    for img_spec in images_prop.split(';'):
        img_spec = img_spec.strip()
        if not img_spec:
            continue

        parts = img_spec.split('|')
        if len(parts) >= 2:
            src = parts[0].strip()
            captions = [p.strip().strip('"') for p in parts[1:]]

            image = {
                'src': src,
                'alt': captions[0] if captions else '',
                'caption_main': captions[0] if captions else None,
                'caption_italic': captions[0].startswith('"') if captions else False,
                'caption_sub': captions[1] if len(captions) > 1 else None,
            }
            images.append(image)

    return images

def parse_evolution(body):
    """Parse evolution timeline bullets into structured data"""
    items = []
    for line in body.strip().split('\n'):
        line = line.strip()
        if line.startswith('- '):
            content = line[2:].strip()
            # Check if line starts with a year
            match = re.match(r'^(\d{4}s?)\s+(.+)$', content)
            if match:
                year, text = match.groups()
                items.append({'year': year, 'text': text})
            else:
                items.append({'text': content})
    return items

def process_node(node, parent_title=None):
    """Process a single org node and return slide data if it has body"""
    # Skip nodes without body
    body = node.get_body(format='raw')
    if not body or not body.strip():
        return None

    heading = node.heading.strip()
    template = node.properties.get('TEMPLATE', '').lower() if node.properties else ''

    # Build slide data
    title = parent_title if parent_title else heading
    subtitle = heading if parent_title else None
    filename = slugify(f"{parent_title}-{heading}" if parent_title else heading) + '.html'

    slide_data = {
        'title': title,
        'subtitle': subtitle,
        'images': parse_images_property(node.properties.get('IMAGES', '') if node.properties else ''),
        'filename': filename,
    }

    # Process based on template type
    if template == 'title':
        slide_data['html_content'] = org_body_to_html(body)
        slide_data['template'] = 'title'
        slide_data['title_hide'] = node.properties.get('TITLE_HIDE', '').lower() == 'true' if node.properties else False
        slide_data['images'] = []  # No images for title slides

    elif template == 'evolution':
        slide_data['items'] = parse_evolution(body)
        slide_data['template'] = 'evolution'

    elif template == 'grid':
        slide_data['items'] = parse_grid(body)
        slide_data['template'] = 'grid'

    else:
        # Default template
        slide_data['html_content'] = org_body_to_html(body)
        slide_data['template'] = 'default'

    return slide_data

def parse_org_file(org_path):
    """Parse org file and extract slides"""
    root = orgparse.load(org_path)
    slides = []

    for node in root[1:]:
        if node.level == 1:
            # Process level 1 node
            slide = process_node(node)
            if slide:
                slides.append(slide)

            # Process level 2 children
            for child in node.children:
                if child.level == 2:
                    slide = process_node(child, parent_title=node.heading.strip())
                    if slide:
                        slides.append(slide)

    return slides

def build_slides(slides, output_dir):
    """Generate HTML files"""
    output_path = Path(output_dir)

    env = Environment(loader=FileSystemLoader('templates'))
    filenames = [slide['filename'] for slide in slides]

    for i, slide in enumerate(slides):
        template = env.get_template(f"{slide['template']}.html")

        slide['prev'] = filenames[i - 1] if i > 0 else None
        slide['next'] = filenames[i + 1] if i < len(filenames) - 1 else None
        slide['all_slides'] = filenames

        html = template.render(**slide)
        (output_path / slide['filename']).write_text(html)

    # Index
    index_template = env.get_template('index.html')
    index_html = index_template.render(
        slides=[(s.get('title', s.get('subtitle', 'Slide')), s['filename']) for s in slides],
        first_slide=filenames[0] if filenames else 'index.html')
    (output_path / 'index.html').write_text(index_html)

    print(f"✓ Built {len(slides)} slides")

if __name__ == '__main__':
    slides = parse_org_file('thetalk.org')
    build_slides(slides, 'build')
