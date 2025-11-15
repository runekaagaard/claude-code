# Presentation Build System Spec

## Goal

Generate HTML presentation slides from `thetalk.org` (org-mode source) that match `src/*.html` exactly.

## The Truth

- **Source of truth**: `thetalk.org` (org-mode file with presentation content)
- **Reference implementation**: `src/*.html` (42 slides we're matching)
- **Expected output**: `build/*.html` (generated slides)

## What's Built

✅ **Core system**
- `build.py` - Parses org-mode, renders Jinja2 templates
- `server.py` - FastAPI server for `build/`
- `Makefile` - Build, serve, clean commands

✅ **Templates**
- `title.html` - Centered title slides with gradient
- `bullets.html` - Two-column layout (title left, bullets right)
- `code.html` - Two-column with code blocks
- `code_centered.html` - Centered code (like "npm install")
- `base.html` - Common layout, navigation, keyboard shortcuts

✅ **Parser features**
- Subsections (level 2 headings) → individual slides
- Code block extraction (`#+begin_src`)
- Bullet point extraction
- Slug generation for URLs

✅ **Current output**: 39 slides generated

## What's Missing

❌ **Slide count**: 39/42 slides (missing 3)
❌ **Slide naming**: Generated slugs don't match `src/` filenames exactly
❌ **Special templates**:
  - `batteries.html` - 4x4 card grid layout
  - Intro slides for sections with subsections
❌ **Navigation order**: Need to match exact sequence from `src/_header.html`

## Validation

### 1. Count Check
```bash
# Should be 42 slides + index = 43 files
ls -1 build/*.html | wc -l
```

### 2. Filename Check
```bash
# All filenames from src/_header.html should exist in build/
cat src/_header.html | grep "'.html'" | sort > /tmp/expected.txt
ls -1 build/*.html | sed 's/build\///' | sort > /tmp/actual.txt
diff /tmp/expected.txt /tmp/actual.txt
```

### 3. Structure Check
Pick 5 random slides and compare:
```bash
# Visual inspection - should have same sections
diff <(grep -o '<h[12]' src/about.html) <(grep -o '<h[12]' build/about.html)
```

### 4. Navigation Check
```bash
# All slides should have prev/next/index working
curl http://localhost:8000/about.html | grep -q "prev-link"
```

### 5. Content Spot Check
Manually verify these key slides match:
- `title.html` - Gradient title
- `batteries.html` - 4x4 grid
- `mcp-value-proposition.html` - Code blocks
- `planning-response.html` - Multi-paragraph response

## The Plan

1. **Fix slide naming** - Map org sections to exact src/ filenames
2. **Create missing templates** - 4x4 cards for batteries
3. **Add intro slides** - Sections like "Planning" need a parent slide
4. **Match navigation** - Use exact order from `src/_header.html`
5. **Validate** - Run all 5 checks above

## Success Criteria

- [ ] 43 files in build/ (42 slides + index.html)
- [ ] All filenames match `src/_header.html` navigation array
- [ ] `make build` completes in < 2 seconds
- [ ] All slides have working prev/next navigation
- [ ] Visual spot check: 5 random slides match src/

## Non-Goals

- Don't parse every org-mode feature (just what we use)
- Don't handle images yet (future enhancement)
- Don't optimize for speed (current speed is fine)
- Don't add features beyond src/ functionality
