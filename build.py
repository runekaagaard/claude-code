#!/usr/bin/env python3
"""
Build presentation slides from thetalk.org
Converts org-mode content directly to HTML
"""
import orgparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re


def slugify(text):
    """Convert text to filename"""
    text = re.sub(r'[^\w\s-]', '', text)
    text = text.lower().replace(' ', '-')
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def autolink(text):
    """Convert URLs to <a> tags"""
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'<a href="\1" class="text-claude-orange hover:underline">\1</a>', text)


def org_to_html(body):
    """Convert org-mode body to HTML"""
    if not body:
        return ""

    html_parts = []
    lines = body.strip().split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Code blocks
        if line.startswith('#+begin_src'):
            lang = line.split()[1] if len(line.split()) > 1 else ''
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('#+end_src'):
                code_lines.append(lines[i])
                i += 1
            code = '\n'.join(code_lines)
            html_parts.append(f'<div class="bg-gray-100 border border-gray-200 rounded-2xl p-8"><pre class="leading-relaxed text-gray-800"><code>{code}</code></pre></div>')
            i += 1
            continue

        # Tables
        if line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i].strip())
                i += 1
            html_parts.append(parse_org_table(table_lines))
            continue

        # Bullets
        if line.startswith('-'):
            text = autolink(line[1:].strip())
            html_parts.append(f'<p>{text}</p>')
            i += 1
            continue

        # Skip empty lines and org directives
        if line and not line.startswith('#'):
            html_parts.append(f'<p>{autolink(line)}</p>')

        i += 1

    return '\n'.join(html_parts)


def parse_org_table(lines):
    """Convert org-mode table to HTML"""
    # Remove separator lines
    lines = [line for line in lines if not set(line.replace('|', '').replace('+', '').strip()) == {'-'}]

    if len(lines) < 2:
        return ""

    # Parse rows
    rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if cells:
            rows.append(cells)

    if not rows:
        return ""

    # Build HTML table
    html = '<div class="bg-gray-100 border border-gray-200 rounded-2xl p-8">'
    html += '<table class="w-full text-lg">'

    # Header
    html += '<thead><tr class="border-b-2 border-gray-300">'
    for cell in rows[0]:
        html += f'<th class="text-left py-2 px-3">{cell}</th>'
    html += '</tr></thead>'

    # Body
    html += '<tbody>'
    for row in rows[1:]:
        html += '<tr class="border-b border-gray-200">'
        for j, cell in enumerate(row):
            if j == 0:
                html += f'<td class="py-2 px-3 font-semibold align-top">{cell}</td>'
            else:
                # Handle multi-line cells
                cell_html = cell.replace('\n', '<br>') if cell else ''
                html += f'<td class="py-2 px-3 align-top">{cell_html}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'

    return html


def parse_grid_items(body):
    """Parse grid items (format: - Name: Description)"""
    if not body:
        return []

    items = []
    for line in body.strip().split('\n'):
        line = line.strip()
        if line.startswith('- ') and ':' in line:
            content = line[2:].strip()
            parts = content.split(':', 1)
            if len(parts) == 2:
                items.append({'name': parts[0].strip(), 'description': parts[1].strip()})

    return items


def parse_org_file(org_path):
    """Parse org file and extract slides"""
    root = orgparse.load(org_path)
    slides = []

    for node in root[1:]:
        if node.level == 1:
            heading = node.heading.strip()

            # Title slides
            if '[CLAUDE:' in heading and 'title' in heading.lower():
                if node.body:
                    body_lines = [line.strip() for line in node.body.strip().split('\n') if line.strip()]
                    if body_lines:
                        slides.append({
                            'title': body_lines[0],
                            'subtitle': body_lines[1] if len(body_lines) > 1 else None,
                            'template': 'title',
                            'filename': slugify(body_lines[0]) + '.html',
                        })
                continue

            clean_heading = re.sub(r'\[CLAUDE:.*?\]', '', heading).strip()
            section_slug = slugify(clean_heading)
            has_body = bool(node.body and node.body.strip())

            # Section with body
            if has_body and not node.children:
                html_content = org_to_html(node.body)
                slides.append({
                    'title': clean_heading,
                    'html_content': html_content,
                    'template': 'content',
                    'filename': f"{section_slug}.html",
                })

            elif has_body and node.children:
                html_content = org_to_html(node.body)
                slides.append({
                    'title': clean_heading,
                    'html_content': html_content,
                    'template': 'content',
                    'filename': f"{section_slug}.html",
                })

            # Process subsections
            if node.children:
                is_first_child = True
                for child in node.children:
                    if child.level == 2:
                        child_heading = child.heading.strip()
                        child_slug = slugify(child_heading)

                        # Determine filename
                        if not has_body and is_first_child:
                            filename = f"{section_slug}.html"
                        else:
                            filename = f"{section_slug}-{child_slug}.html"

                        # Check for grid items
                        grid_items = parse_grid_items(child.body)

                        if grid_items:
                            slides.append({
                                'title': child_heading,
                                'items': grid_items,
                                'template': 'batteries',
                                'filename': filename,
                            })
                        else:
                            html_content = org_to_html(child.body)
                            slides.append({
                                'title': clean_heading,
                                'subtitle': child_heading,
                                'html_content': html_content,
                                'template': 'content',
                                'filename': filename,
                            })

                        is_first_child = False

    return slides


def build_slides(slides, output_dir):
    """Generate HTML files"""
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

    # Index
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

    print(f"✓ Built {len(slides)} slides")
    return filenames


if __name__ == '__main__':
    slides = parse_org_file('thetalk.org')
    build_slides(slides, 'build')
