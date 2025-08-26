#!/usr/bin/env python3
"""
Version Management Script for Bank Statement Processor
Updates version numbers across project files when releasing new versions.
"""

import re
import os
from datetime import datetime

def update_dockerfile_version(version):
    """Update version in Dockerfile"""
    dockerfile_path = 'Dockerfile'
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Update version label
    content = re.sub(r'LABEL version="[^"]*"', f'LABEL version="{version}"', content)
    
    with open(dockerfile_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated Dockerfile version to {version}")

def update_app_version(version):
    """Update version in app.py"""
    app_path = 'app.py'
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    # Add version info if not exists
    if 'VERSION = ' not in content:
        # Add after imports
        content = content.replace(
            'from flask import Flask, request, jsonify, send_file, render_template',
            'from flask import Flask, request, jsonify, send_file, render_template\n\n# Version information\nVERSION = "' + version + '"\nBUILD_DATE = "' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '"'
        )
    
    # Update version if exists
    else:
        content = re.sub(r'VERSION = "[^"]*"', f'VERSION = "{version}"', content)
    
    with open(app_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated app.py version to {version}")

def update_html_version(version):
    """Update version in HTML template"""
    html_path = 'templates/index.html'
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    # Update title version
    content = re.sub(r'<title>Bank Statement Processor v[^<]*</title>', 
                     f'<title>Bank Statement Processor v{version}</title>', content)
    
    # Update any version displays in the UI
    content = re.sub(r'Version: v[^<]*', f'Version: v{version}', content)
    
    with open(html_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated HTML version to {version}")

def update_readme_version(version):
    """Update version in README.md"""
    readme_path = 'README.md'
    
    with open(readme_path, 'r') as f:
        content = f.read()
    
    # Update version references
    content = re.sub(r'Version: \d+\.\d+\.\d+', f'Version: {version}', content)
    content = re.sub(r'v\d+\.\d+\.\d+', f'v{version}', content)
    
    with open(readme_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated README.md version to {version}")

def create_version_file(version):
    """Create a VERSION file"""
    with open('VERSION', 'w') as f:
        f.write(f"{version}\n")
    
    print(f"✅ Created VERSION file with {version}")

def main():
    """Main function to update version across all files"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <version>")
        print("Example: python update_version.py 1.1.0")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # Validate version format (semantic versioning)
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print("❌ Error: Version must be in format X.Y.Z (e.g., 1.0.0)")
        sys.exit(1)
    
    print(f"🔄 Updating project to version {version}...")
    
    try:
        update_dockerfile_version(version)
        update_app_version(version)
        update_html_version(version)
        update_readme_version(version)
        create_version_file(version)
        
        print(f"\n🎉 Successfully updated project to version {version}")
        print("\nNext steps:")
        print("1. Commit changes: git add . && git commit -m 'Bump version to {version}'")
        print("2. Tag release: git tag -a v{version} -m 'Release version {version}'")
        print("3. Push to GitHub: git push origin main --tags")
        print("4. Docker Hub will auto-build with new tag")
        
    except Exception as e:
        print(f"❌ Error updating version: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
