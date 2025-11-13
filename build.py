#!/usr/bin/env python3
"""
Build presentation slides from thetalk.org
"""
import orgparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re


def slugify(text):
    """Convert text to URL-friendly slug"""
    slug = text.lower()
    # Remove special characters and brackets
    slug = re.sub(r'[\[\]/\(\):]', '', slug)
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def shorten_slug(section_slug, child_slug):
    """Create a shortened slug for subsections"""
    # Special cases for common abbreviations
    abbreviations = {
        'documentation': 'doc',
        'dev-setup': 'dev',
        'exploration': 'exploration',
        'build-root': 'build-root',
        'build-leaves': 'build-leaves',
        'start-building': 'start-building',
        'mcp-servers': 'mcp',
    }

    # Use abbreviation if available, otherwise use full section slug
    prefix = abbreviations.get(section_slug, section_slug)

    # For special cases, return exact filename
    if section_slug == 'start-building' and 'issue' in child_slug:
        return 'dev-issue-command'
    if section_slug == 'dev-setup':
        if 'create-worktree' in child_slug:
            return 'dev-create-worktree'
        if 'worktrees' in child_slug:
            return 'dev-worktrees'
        # Handle "Workspace Creation" subsection which needs special suffix handling
        if 'workspace-creation' in child_slug and not child_slug.endswith('2'):
            # Check if this should be the base name or -2
            # If it's the first "Workspace Creation", add the suffix -2 based on position
            pass  # Will handle below
    if section_slug == 'exploration':
        if 'prompt' in child_slug:
            return 'exploration-prompt'
        if 'realpath' in child_slug:
            return 'exploration-tooling'

    # Combine prefix with child slug
    result = f"{prefix}-{child_slug}"

    return result


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


def parse_batteries_items(body):
    """Parse batteries section into 4x4 grid items"""
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

            # Handle CLAUDE markers
            if '[CLAUDE:' in heading and 'Title type slide' in heading:
                # Title slide
                if node.body:
                    body_lines = [line.strip() for line in node.body.strip().split('\n') if line.strip()]
                    if body_lines:
                        slide = {
                            'title': body_lines[0],
                            'subtitle': body_lines[1] if len(body_lines) > 1 else None,
                            'template': 'title',
                            'filename': 'title.html' if not slides else 'getting-started.html',
                        }
                        slides.append(slide)
                continue

            # Clean heading
            clean_heading = re.sub(r'\[CLAUDE:.*?\]', '', heading).strip()
            section_slug = slugify(clean_heading)

            # Check if section has body content
            has_body = bool(node.body and node.body.strip())

            # If section has body, create intro slide
            if has_body and not node.children:
                # Standalone section with no subsections
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

            elif has_body and node.children:
                # Section with body AND subsections - create intro slide
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

                        # Check for special batteries section
                        if 'Batteries' in child_heading:
                            items = parse_batteries_items(child.body)
                            slide = {
                                'title': child_heading,
                                'items': items,
                                'template': 'batteries',
                                'filename': 'batteries.html',
                            }
                            slides.append(slide)
                            is_first_child = False
                            continue

                        # Determine filename
                        if not has_body and is_first_child:
                            # First child of section without body uses section slug
                            filename = f"{section_slug}.html"
                        else:
                            # Other children use shortened prefix
                            filename = f"{shorten_slug(section_slug, child_slug)}.html"

                        # Extract content
                        code_blocks = extract_code_blocks(child.body)
                        bullets = extract_bullets(child.body)

                        # Determine if multiple code blocks should be split into separate slides
                        should_split_blocks = (
                            ('prompt' in child_slug.lower() and section_slug == 'planning') or
                            ('create-worktree' in child_slug.lower()) or
                            ('workspace-creation' in child_slug.lower())
                        )

                        if code_blocks and len(code_blocks) > 1 and should_split_blocks:
                            # Multiple code blocks - create one slide per block
                            for block_idx, code_block in enumerate(code_blocks):
                                # Determine subtitle for each block
                                if block_idx == 0:
                                    block_subtitle = child_heading
                                    block_filename = filename
                                elif block_idx == 1:
                                    if 'prompt' in child_slug.lower():
                                        block_subtitle = 'Follow-up Response'
                                    else:
                                        block_subtitle = child_heading
                                    # Second block gets different filename
                                    base = filename.replace('.html', '')
                                    if base.endswith('-prompt'):
                                        block_filename = base.replace('-prompt', '-response') + '.html'
                                    elif 'create-worktree' in base:
                                        block_filename = 'dev-workspace-creation.html'
                                    else:
                                        block_filename = f"{base}-2.html"
                                else:
                                    block_subtitle = child_heading
                                    base = filename.replace('.html', '')
                                    if 'create-worktree' in base:
                                        block_filename = 'dev-workspace-creation-2.html'
                                    else:
                                        block_filename = f"{base}-{block_idx + 1}.html"

                                slide = {
                                    'title': clean_heading,
                                    'subtitle': block_subtitle,
                                    'code_blocks': [code_block],
                                    'template': 'code',
                                    'filename': block_filename,
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

    # Setup Jinja2
    env = Environment(loader=FileSystemLoader('templates'))

    # Get filenames from slides
    filenames = [slide['filename'] for slide in slides]

    # Generate each slide
    for i, slide in enumerate(slides):
        template = env.get_template(f"{slide['template']}.html")

        # Add navigation
        slide['prev'] = filenames[i-1] if i > 0 else None
        slide['next'] = filenames[i+1] if i < len(filenames) - 1 else None
        slide['all_slides'] = filenames

        # Render
        html = template.render(**slide)
        (output_path / slide['filename']).write_text(html)

    # Generate index
    index_template = env.get_template('index.html')
    index_html = index_template.render(
        slides=[(s.get('title', 'Slide'), s['filename']) for s in slides],
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
    print(f"\nGenerated {len(filenames)} slides")
    print("\nFilenames:")
    for f in filenames:
        print(f"  {f}")
