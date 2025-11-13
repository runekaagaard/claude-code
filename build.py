#!/usr/bin/env python3
"""
Build presentation slides from thetalk.org
Generic org-mode to HTML converter
"""
import orgparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re


def slugify(text):
    """Convert text to filename: lowercase, spaces to dashes, remove invalid chars"""
    text = re.sub(r'[^\w\s-]', '', text)  # Remove special chars
    text = text.lower().replace(' ', '-')
    text = re.sub(r'-+', '-', text)  # Collapse multiple dashes
    return text.strip('-')


def extract_bullets(body):
    """Extract bullet points from org-mode body"""
    if not body:
        return []
    bullets = []
    for line in body.strip().split('\n'):
        line = line.strip()
        if line.startswith('-'):
            bullets.append(line[1:].strip())
    return bullets


def extract_code_blocks(body):
    """Extract code blocks from org-mode body"""
    if not body:
        return []

    code_blocks = []
    pattern = r'#\+begin_src\s+(\w+)\n(.*?)#\+end_src'
    matches = re.findall(pattern, body, re.DOTALL | re.IGNORECASE)

    for lang, code in matches:
        code_blocks.append({
            'language': lang,
            'code': code.strip()
        })

    return code_blocks


def parse_grid_items(body):
    """Parse grid items from body (format: - Name: Description)"""
    if not body:
        return []

    items = []
    lines = body.strip().split('\n')

    for line in lines:
        line = line.strip()
        if line.startswith('- ') and ':' in line:
            content = line[2:].strip()
            parts = content.split(':', 1)
            if len(parts) == 2:
                name = parts[0].strip()
                description = parts[1].strip()
                items.append({'name': name, 'description': description})

    return items


def parse_org_file(org_path):
    """Parse org file and extract slide data"""
    root = orgparse.load(org_path)
    slides = []

    for node in root[1:]:
        if node.level == 1:
            heading = node.heading.strip()

            # Check for title slide marker
            is_title_slide = '[CLAUDE:' in heading and 'title' in heading.lower()

            if is_title_slide:
                # Title slide from body content
                if node.body:
                    body_lines = [line.strip() for line in node.body.strip().split('\n') if line.strip()]
                    if body_lines:
                        slide = {
                            'title': body_lines[0],
                            'subtitle': body_lines[1] if len(body_lines) > 1 else None,
                            'template': 'title',
                            'filename': slugify(body_lines[0]) + '.html',
                        }
                        slides.append(slide)
                continue

            # Clean heading
            clean_heading = re.sub(r'\[CLAUDE:.*?\]', '', heading).strip()
            section_slug = slugify(clean_heading)
            has_body = bool(node.body and node.body.strip())

            # Section with body but no children
            if has_body and not node.children:
                bullets = extract_bullets(node.body)
                code_blocks = extract_code_blocks(node.body)

                if code_blocks:
                    slide = {
                        'title': clean_heading,
                        'code_blocks': code_blocks,
                        'template': 'code',
                        'filename': f"{section_slug}.html",
                    }
                else:
                    slide = {
                        'title': clean_heading,
                        'content': bullets,
                        'template': 'bullets',
                        'filename': f"{section_slug}.html",
                    }
                slides.append(slide)

            # Section with body AND children - create intro slide
            elif has_body and node.children:
                bullets = extract_bullets(node.body)
                slide = {
                    'title': clean_heading,
                    'content': bullets,
                    'template': 'bullets',
                    'filename': f"{section_slug}.html",
                }
                slides.append(slide)

            # Process subsections
            if node.children:
                is_first_child = True
                for child in node.children:
                    if child.level == 2:
                        child_heading = child.heading.strip()
                        child_slug = slugify(child_heading)

                        # Determine filename
                        if not has_body and is_first_child:
                            # First child of section without body uses parent slug
                            filename = f"{section_slug}.html"
                        else:
                            # Other children combine parent and child slugs
                            filename = f"{section_slug}-{child_slug}.html"

                        # Extract content
                        code_blocks = extract_code_blocks(child.body)
                        bullets = extract_bullets(child.body)
                        grid_items = parse_grid_items(child.body)

                        # Determine template
                        if grid_items:
                            # Grid layout
                            slide = {
                                'title': child_heading,
                                'items': grid_items,
                                'template': 'batteries',
                                'filename': filename,
                            }
                            slides.append(slide)
                        elif code_blocks:
                            # Single code block
                            slide = {
                                'title': clean_heading,
                                'subtitle': child_heading,
                                'code_blocks': code_blocks,
                                'template': 'code',
                                'filename': filename,
                            }
                            slides.append(slide)
                        else:
                            # Bullet points
                            slide = {
                                'title': clean_heading,
                                'subtitle': child_heading,
                                'content': bullets,
                                'template': 'bullets',
                                'filename': filename,
                            }
                            slides.append(slide)

                        is_first_child = False

    return slides


def build_slides(slides, output_dir):
    """Generate HTML files from slides"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader('templates'))
    filenames = [slide['filename'] for slide in slides]

    for i, slide in enumerate(slides):
        template = env.get_template(f"{slide['template']}.html")

        slide['prev'] = filenames[i-1] if i > 0 else None
        slide['next'] = filenames[i+1] if i < len(filenames) - 1 else None
        slide['all_slides'] = filenames

        html = template.render(**slide)
        (output_path / slide['filename']).write_text(html)

    # Generate index
    index_template = env.get_template('index.html')
    index_html = index_template.render(
        slides=[(s.get('title', s.get('subtitle', 'Slide')), s['filename']) for s in slides],
        first_slide=filenames[0] if filenames else 'index.html'
    )
    (output_path / 'index.html').write_text(index_html)

    # Copy styles
    import shutil
    if Path('src/styles.css').exists():
        shutil.copy('src/styles.css', output_path / 'styles.css')

    print(f"✓ Built {len(slides)} slides to {output_dir}/")
    return filenames


if __name__ == '__main__':
    slides = parse_org_file('thetalk.org')
    filenames = build_slides(slides, 'build')
    print(f"Generated {len(filenames)} slides")
