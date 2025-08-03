<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Telegram Feed Website - Flask Project

This is a Flask web application for aggregating and displaying Telegram channel posts using Jinja2 templates.

## Project Guidelines:

- Use Flask with SQLAlchemy for database operations
- Use Jinja2 templates for rendering HTML
- Follow Flask blueprints pattern for organizing routes
- Use Bootstrap or similar CSS framework for responsive design
- Implement proper error handling and logging
- Use environment variables for configuration
- Follow PEP 8 Python style guidelines
- Use proper database migrations with Flask-Migrate

## Architecture:
- `app.py` - Main Flask application
- `models/` - SQLAlchemy database models
- `routes/` - Flask route handlers organized by blueprints
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, JS, and image files
- `services/` - Business logic and external API integrations
