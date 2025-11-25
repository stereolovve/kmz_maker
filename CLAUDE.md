# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based web application for converting road work spreadsheets (Excel) to KML files for visualization in Google Earth. The application provides a clean, professional interface with sidebar navigation for multiple tools.

**Technology Stack:**
- Backend: Django 5.0.1 + Django REST Framework
- Frontend: Vanilla JavaScript (no frameworks)
- Database: SQLite (dev) / PostgreSQL (prod)
- Deployment: uWSGI + Nginx

## Code Style Guidelines

### Emoji Policy

**IMPORTANT: Emojis are STRICTLY PROHIBITED throughout this entire project.**

**DO NOT use emojis in:**
- HTML templates (all .html files)
- Python code (all .py files)
- JavaScript code
- CSS files
- Documentation (README, comments, docstrings)
- Git commit messages
- User-facing text
- API responses
- Error messages
- Log files

**Use these alternatives instead:**
- Icons: Use icon fonts (FontAwesome, Material Icons) or SVG icons
- Visual indicators: Use Unicode symbols (→, ×, ✓, ⚠, ⚙, ▣, ▢, #) or text labels
- Status messages: Use clear text ("Success", "Error", "Warning", "Processing")
- Buttons: Use text labels with optional Unicode symbols
- Navigation: Use text + Unicode symbols or icon fonts

**Rationale:**
- Emojis can cause rendering issues across different systems
- Not professional for enterprise applications
- Inconsistent display across browsers and devices
- Accessibility concerns
- User explicitly dislikes emojis

## Architecture

**Django Apps:**
- `obras/` - Main application for KML generation

**Key Files:**
- `obras/templates/base.html` - Base template with sidebar navigation
- `obras/templates/home.html` - KML Generator interface (linear vertical layout)
- `obras/templates/tutorial.html` - User documentation
- `obras/views.py` - View functions and API endpoints
- `obras/services.py` - Business logic for KML processing

## Development Commands

```bash
# Start development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

## UI/UX Guidelines

### Layout Principles
- **Linear Vertical Flow**: All pages use top-to-bottom linear layout
- **No Multi-Column Grids**: Avoid complex grid layouts; keep it simple and vertical
- **Clear Hierarchy**: Title → Input → Options → Action Button → Results
- **Responsive**: Mobile-first, vertical layout works on all screen sizes

### Component Order (Home Page)
1. Page Header (title + description)
2. Upload Area
3. Selected File Display
4. Process Type Selection
5. Error Alert (if any)
6. **Process Button** (always below selections)
7. Status Card (when processing)
8. Download Card (when complete)

## Notes

- Sidebar titled "KMZ Solutions" with version display in footer
- Version fetched dynamically from `/api/version/` endpoint
- Mobile responsive with hamburger menu (<768px)
- All functionality must work without JavaScript frameworks
- Keep styling embedded in templates for simplicity