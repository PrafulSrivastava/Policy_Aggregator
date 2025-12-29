"""Jinja2 templates configuration for admin UI."""

from fastapi.templating import Jinja2Templates

# Configure Jinja2 templates
templates = Jinja2Templates(directory="admin-ui/templates")

