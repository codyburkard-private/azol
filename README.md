# Azol Documentation

This directory contains the Jekyll documentation site for the Azol library.

## Building the Site

### Prerequisites

- Ruby (2.7 or higher)
- Bundler gem

### Setup

1. Install dependencies:
```bash
bundle install
```

2. Build the site:
```bash
bundle exec jekyll build
```

3. Serve locally:
```bash
bundle exec jekyll serve
```

The site will be available at `http://localhost:4000`

## Structure

- `_config.yml` - Jekyll configuration
- `_layouts/` - HTML layouts
- `index.md` - Homepage
- `installation.md` - Installation instructions
- `quick-start.md` - Quick start guide
- `clients.md` - API client documentation
- `credentials.md` - Credential documentation
- `utilities.md` - Utility functions documentation
- `providers.md` - Secret provider documentation
- `caches.md` - Token cache documentation
- `models.md` - Data model documentation

## Deployment

The site can be deployed to:
- GitHub Pages
- Netlify
- Any static site hosting service

For GitHub Pages, push the `docs` folder to the `gh-pages` branch or configure it as the source directory in repository settings.

