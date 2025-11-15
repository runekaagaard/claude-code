# Claude Code in Practice - Presentation

Programmatic slide generation from org-mode source. Vibe code with Claude Code ;)

## Quick Start

```bash
# Install dependencies (first time only)
make install

# Build slides
make build

# Serve presentation
make serve

# Clean build directory
make clean
```

## How it Works

1. **Source**: `thetalk.org` - Org-mode file with presentation content
2. **Styles**: `style.css` - Tailwind CSS with semantic element styling
3. **Parser**: `build.py` - Parses org-mode and generates clean semantic HTML
4. **Templates**: `templates/*.html` - Jinja2 templates (title, default, evolution, grid)
5. **Static**: `static/` - Images and assets (copied to `build/static/`)
6. **Output**: `build/*.html` + `build/static/` - Generated slides with compiled CSS
7. **Server**: `server.py` - FastAPI server to serve static files

## Org-Mode Structure

### Title Slides

```org
* [CLAUDE: Title type slide]
Main Title
Subtitle
```

### Bullet Point Slides

```org
* Slide Title
- Bullet point 1
- Bullet point 2
- Bullet point 3
```

### Subsections

```org
* Main Section
** Subsection Title
- Subsection bullet 1
- Subsection bullet 2
```

## Template Types

- `title.html` - Centered title slides
- `bullets.html` - Standard bullet point slides
- `index.html` - Auto-redirect to first slide

## Navigation

- Prev/Next buttons automatically generated
- Index always redirects to first slide
- Clean URLs based on slide titles

## Development

```bash
# Install Node dependencies
npm install

# Install Python dependencies
uv add orgparse fastapi jinja2 uvicorn

# Build CSS
npm run build:css

# Run build
python build.py

# Start server
uv run uvicorn server:app --reload --port 8000
```

Server runs at: http://localhost:8000

## CSS Architecture

All styling is done through Tailwind CSS with a clean separation:

- **Semantic HTML**: `build.py` generates clean semantic HTML without inline classes
- **Base Styles**: `style.css` defines styling for semantic elements (pre, code, table, ul, li, etc.)
- **Component Wrappers**: Templates use `.slide-content` wrapper for content-specific styling
- **Build Process**:
  1. Copy `static/` → `build/static/` (images and static assets)
  2. Tailwind CLI compiles `style.css` → `build/static/style.css` (minified)
