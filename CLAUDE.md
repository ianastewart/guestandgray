# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Dev server (uses mysite.settings.dev automatically via manage.py)
python manage.py runserver

# Tests (uses mysite.settings.test, runs without migrations)
pytest
pytest path/to/tests.py::ClassName::test_method   # single test

# Lint
ruff check .
```

Settings are loaded from a `.env` file in the project root (`DATABASE_URL`, `SECRET_KEY`, `SITEMAIL`, captcha keys, etc.).

## Architecture

**Guest and Gray** is an antique shop management system built on CodeRedCMS (Wagtail). The live domain is `chinese-porcelain-art.com`.

### Apps

- **`shop`** — the central app. Contains all models, views, and business logic.
- **`website`** — Wagtail page types and content blocks.
- **`notes`** — internal staff notes.
- **`table_manager`** — shared table utilities.

### Settings

`mysite/settings/base.py` → `dev.py` / `live.py`. The `manage.py` default is `dev`. Tests use `test.py` (inherits from `dev`).

Database URL, secret key, and API keys come from `.env` via `django-environ`.

### Key models (`shop/models.py`)

- **`Item`** — the antique item (ref, name, description, category, images, price, state, library/archive flag).
- **`Category`** — hierarchical tree using `django-treebeard` (`MP_Node`). Slugs represent full path (e.g. `catalogue/ceramics/porcelain`).
- **`CustomImage`** — extends Wagtail's `AbstractImage`, linked to `Item`.
- **`Contact`** — buyers, vendors, restorers.
- **`Address`** — multiple addresses per `Contact`.
- **`Purchase`** / **`Lot`** — purchase recording (auction lots etc.).
- **`Invoice`** / **`InvoiceCharge`** — sale invoicing.
- **`Book`** / **`Compiler`** — reference bibliography.
- **`GlobalSettings`** — singleton for site-wide switches (price visibility, captcha mode).

`Item.library` distinguishes stock (`STOCK=0`), archive (`ARCHIVE=1`), and research (`RESEARCH=2`) items.

### URL structure

| Prefix | Module | Purpose |
|--------|--------|---------|
| `staff/` | `shop/views/staff_views.py`, etc. | All admin/staff views (login required) |
| `` (root) | `shop/views/public_views.py` | Public website |
| `catalogue/<slugs>/` | public | Category browsing |
| `archive/<slugs>/` | public | Archived items |
| `item/<ref>/<slug>/` | public | Item detail page |
| `admin/` | CodeRed/Wagtail | CMS admin |
| `notes/` | `notes` app | Internal notes |

### Views (`shop/views/`)

- `public_views.py` — home, catalogue, archive, item detail, search, contact, enquiry, bibliography
- `item_views.py` — staff CRUD for items
- `category_views.py` — staff category management
- `contact_views.py` — contacts, vendors, buyers, enquiries
- `purchase_views.py` — multi-step purchase recording wizard
- `cart_views.py` — cart / checkout flow
- `invoice_views.py` — invoice list and detail
- `image_views.py` — image upload and assignment
- `book_views.py` — bibliography management
- `staff_views.py` — staff home dashboard, global settings
- `legacy_views.py` — redirects from old `/acatalog/` URLs

### Access control

All staff views use `LoginRequiredMixin`. Login goes through Wagtail admin login (`LOGIN_URL = "wagtailadmin_login"`).

### Templates

`HostPage` (used for catalogue/item Wagtail pages) uses `coderedcms/pages/base.html`. Staff view templates live under `shop/templates/shop/`. The `shop` and `website` apps are declared before `coderedcms` in `INSTALLED_APPS` to allow template overrides.

### UI stack

- **Bootstrap 5** (`django_bootstrap5`, `DJANGO_TABLEAUX_LIBRARY = "bootstrap5"`)
- **HTMX** (`django-htmx`) — used for modals and partial updates in staff views
- **django-tableaux** — enhanced `django-tables2` tables
- **django-treebeard** — category tree management
- **markdownify** — `{{ content|markdownify }}` template filter for item descriptions
- **hCaptcha** — contact form spam protection (`USE_HCAPTCHA = True`)

### Markdown rendering

`django-markdownify` is used as a template filter (`{{ content|markdownify }}`). Configured in `MARKDOWNIFY` in `base.py`.

### External integrations

- **Sentry** — error tracking in production
- **Wagtail/CodeRedCMS** — CMS and page management
- **IONOS SMTP** — transactional email (`smtp.ionos.co.uk`)
- **hCaptcha** — contact/enquiry spam protection
- **Whitenoise** — static file serving
- **Wagtail cache** — page-level caching (disabled in dev)