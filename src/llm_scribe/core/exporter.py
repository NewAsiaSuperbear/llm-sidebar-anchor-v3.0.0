import os
import json
from datetime import datetime
from jinja2 import Template
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from llm_scribe.utils.logger import logger

class ExportEngine:
    """
    Core engine for rendering session data into various formats using templates.
    """
    
    DEFAULT_MD_TEMPLATE = """# {{ title }}

> **Created at:** {{ created_at }}
> **Tags:** {{ tags | join(', ') }}

---

{{ content }}

---
*Exported from LLM Scribe Pro on {{ export_date }}*
"""

    DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 0 20px; background-color: #f9f9f9; }
        .container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3ea6ff; padding-bottom: 10px; }
        .meta { color: #7f8c8d; font-size: 0.9em; margin-bottom: 30px; border-left: 4px solid #3ea6ff; padding-left: 15px; }
        .content { margin-top: 20px; }
        pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; }
        code { font-family: 'Consolas', monospace; }
        blockquote { border-left: 4px solid #ccc; margin: 1.5em 10px; padding: 0.5em 10px; color: #666; font-style: italic; }
        footer { margin-top: 50px; font-size: 0.8em; color: #999; text-align: center; }
        {{ pygments_css }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <div class="meta">
            <p><strong>Created:</strong> {{ created_at }}</p>
            <p><strong>Tags:</strong> {{ tags | join(', ') }}</p>
        </div>
        <div class="content">
            {{ html_content }}
        </div>
        <footer>
            Exported from LLM Scribe Pro on {{ export_date }}
        </footer>
    </div>
</body>
</html>
"""

    OBSIDIAN_TEMPLATE = """---
title: {{ title }}
created: {{ created_at }}
tags: [{{ tags | join(', ') }}]
source: LLM Scribe Pro
---

# {{ title }}

{{ content }}
"""

    LOGSEQ_TEMPLATE = """- title:: {{ title }}
- created:: {{ created_at }}
- tags:: {{ tags | join(', ') }}
- source:: LLM Scribe Pro

- # {{ title }}
{% for line in content.split('\\n') %}
  - {{ line }}
{% endfor %}
"""

    @staticmethod
    def render_markdown(session_data, template_str=None, preset=None):
        """Renders a session to Markdown format with optional presets."""
        if not template_str:
            if preset == 'obsidian':
                template_str = ExportEngine.OBSIDIAN_TEMPLATE
            elif preset == 'logseq':
                template_str = ExportEngine.LOGSEQ_TEMPLATE
            else:
                template_str = ExportEngine.DEFAULT_MD_TEMPLATE
        
        template = Template(template_str)
        return template.render(
            title=session_data.get('title', 'Untitled'),
            content=session_data.get('content', ''),
            created_at=session_data.get('created_at', 'N/A'),
            tags=session_data.get('tags', []),
            export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    @staticmethod
    def render_html(session_data, template_str=None):
        """Renders a session to HTML format with syntax highlighting."""
        md_content = session_data.get('content', '')
        
        # Convert Markdown to HTML with extensions
        html_body = markdown.markdown(md_content, extensions=['extra', 'codehilite', 'toc'])
        
        # Get Pygments CSS for code highlighting
        formatter = HtmlFormatter(style='monokai')
        pygments_css = formatter.get_style_defs('.codehilite')
        
        template = Template(template_str or ExportEngine.DEFAULT_HTML_TEMPLATE)
        return template.render(
            title=session_data.get('title', 'Untitled'),
            html_content=html_body,
            created_at=session_data.get('created_at', 'N/A'),
            tags=session_data.get('tags', []),
            pygments_css=pygments_css,
            export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

class Exporter:
    """
    High-level handler for exporting data to files.
    """
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def export_session(self, session_id, output_path, format='md', preset=None):
        """Exports a single session to the specified path and format."""
        try:
            session = self.data_manager.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            if format == 'md':
                content = ExportEngine.render_markdown(session, preset=preset)
            elif format == 'html':
                content = ExportEngine.render_html(session)
            else:
                raise ValueError(f"Unsupported format: {format}")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Successfully exported session {session_id} to {output_path} (preset: {preset})")
            return True
        except Exception as e:
            logger.error(f"Export failed for session {session_id}: {e}")
            return False

    def export_folder(self, folder_id, output_dir, format='md', preset=None):
        """Exports all sessions in a folder to a directory."""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with self.data_manager.lock:
                sessions = [s for s in self.data_manager.data["sessions"] if s.get("parent") == folder_id]
            
            success_count = 0
            for session in sessions:
                # Sanitize filename
                safe_title = "".join([c for c in session['title'] if c.isalnum() or c in (' ', '-', '_')]).strip()
                filename = f"{safe_title}.{format}"
                file_path = os.path.join(output_dir, filename)
                
                if self.export_session(session['id'], file_path, format, preset=preset):
                    success_count += 1
            
            logger.info(f"Exported {success_count}/{len(sessions)} sessions from folder {folder_id} (preset: {preset})")
            return success_count
        except Exception as e:
            logger.error(f"Folder export failed: {e}")
            return 0
