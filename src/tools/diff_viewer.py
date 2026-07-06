from __future__ import annotations

"""
Diff Viewer — generates styled HTML side-by-side git diff tables for Streamlit.
Uses Python's built-in difflib to keep execution dependency-free.
"""

import difflib
import os


class DiffViewer:
    """Generate side-by-side HTML diff tables."""

    @staticmethod
    def generate_html_diff(file_path_a: str, file_path_b: str) -> str:
        """
        Generate a styled side-by-side HTML diff table.

        Args:
            file_path_a: Path to original file.
            file_path_b: Path to modified file.

        Returns:
            A string containing HTML and CSS of the diff.
        """
        if not os.path.exists(file_path_a) or not os.path.exists(file_path_b):
            return f"<p style='color:red;'>Error: File not found for diff comparison ({file_path_a} or {file_path_b})</p>"

        try:
            with open(file_path_a, "r", encoding="utf-8") as f:
                lines_a = f.readlines()
            with open(file_path_b, "r", encoding="utf-8") as f:
                lines_b = f.readlines()
        except Exception as e:
            return f"<p style='color:red;'>Error reading files: {e}</p>"

        # Use HtmlDiff to generate the table
        diff = difflib.HtmlDiff(tabsize=4)
        diff_table = diff.make_table(
            lines_a,
            lines_b,
            fromdesc="Original Code",
            todesc="Sandbox Patched Code",
            context=False
        )

        # Style the table to match Streamlit's theme (supporting dark mode)
        html_content = f"""
        <style>
            table.diff {{
                font-family: Courier, monospace;
                border: 1px solid #444;
                width: 100%;
                border-collapse: collapse;
                background-color: #0e1117;
                color: #c9d1d9;
                font-size: 13px;
            }}
            th.diff_header {{
                background-color: #1f2937;
                color: #f3f4f6;
                padding: 6px;
                border-bottom: 2px solid #444;
                font-weight: bold;
                text-align: center;
            }}
            td.diff_header {{
                background-color: #161b22;
                color: #8b949e;
                text-align: right;
                padding: 2px 8px;
                border-right: 1px solid #30363d;
                user-select: none;
                width: 40px;
            }}
            td.diff_next {{
                background-color: #161b22;
                padding: 0 4px;
                user-select: none;
                width: 10px;
            }}
            span.diff_add {{
                background-color: #2ea04326;
                color: #56d364;
                text-decoration: none;
                font-weight: bold;
            }}
            span.diff_chg {{
                background-color: #ae7c1426;
                color: #e3b341;
                text-decoration: none;
            }}
            span.diff_sub {{
                background-color: #da363326;
                color: #f85149;
                text-decoration: line-through;
                font-weight: bold;
            }}
            td {{
                padding: 2px 6px;
                white-space: pre-wrap;
                word-break: break-all;
            }}
            tr:hover {{
                background-color: #1f242c;
            }}
        </style>
        <div style="overflow-x:auto;">
            {diff_table}
        </div>
        """
        return html_content
