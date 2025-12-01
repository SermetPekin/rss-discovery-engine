#!/usr/bin/env python3
"""
Export the Blog Discovery Viewer to a static HTML file for GitHub Pages.
"""

from flask import Flask, render_template_string
from view import COMBINED_TEMPLATE, load_data
import os

def export():
    print("=" * 80)
    print("✦ Exporting to static HTML")
    print("=" * 80)
    
    # Load the data
    data = load_data()
    print(f"📊 Loaded {data['total_blogs']} blogs")
    
    # Create a dummy Flask app context to render the template
    app = Flask(__name__)
    with app.app_context():
        # Render the template with the data
        html_content = render_template_string(COMBINED_TEMPLATE, **data)
    
    # Save to index.html
    output_file = 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ Successfully exported to {output_file}")
    print(f"👉 You can now push {output_file} to GitHub and enable GitHub Pages!")

if __name__ == '__main__':
    export()
