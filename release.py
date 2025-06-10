#!/usr/bin/env python3
"""
Release Script for ModuLink-Py
Handles version bumping and release workflow
Usage: python release.py [patch|minor|major]
"""

import sys
import subprocess
import json
import re
from pathlib import Path


def run_command(command, description):
    """Execute command and handle errors"""
    try:
        print(f"🔄 {description}...")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def check_git_status():
    """Check if working directory is clean"""
    try:
        status = subprocess.run('git status --porcelain', shell=True, capture_output=True, text=True, check=True)
        if status.stdout.strip():
            print('📋 Uncommitted changes detected:')
            print(status.stdout)
            print('\n⚠️  Please commit or stash changes before releasing.')
            
            force = input("Continue anyway? (yes/no): ").lower()
            if force != 'yes':
                sys.exit(1)
        else:
            print('✅ Working directory is clean')
    except subprocess.CalledProcessError:
        print('❌ Failed to check git status')
        sys.exit(1)


def get_current_version():
    """Get current version from pyproject.toml (preferred) or setup.py"""
    # Try pyproject.toml first (modern approach)
    pyproject_toml = Path("pyproject.toml")
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    
    # Fallback to setup.py
    setup_py = Path("setup.py")
    if setup_py.exists():
        content = setup_py.read_text()
        match = re.search(r'version=["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    
    print("❌ Could not find version in pyproject.toml or setup.py")
    sys.exit(1)


def bump_version(current_version, bump_type):
    """Bump version based on type"""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        print(f"❌ Invalid bump type: {bump_type}")
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"


def update_version_in_setup_py(new_version):
    """Update version in setup.py"""
    setup_py = Path("setup.py")
    content = setup_py.read_text()
    
    # Replace version
    new_content = re.sub(
        r'version=["\'][^"\']+["\']',
        f'version="{new_version}"',
        content
    )
    
    setup_py.write_text(new_content)
    print(f"✅ Updated setup.py to version {new_version}")


def update_version_in_pyproject_toml(new_version):
    """Update version in pyproject.toml"""
    pyproject_toml = Path("pyproject.toml")
    if not pyproject_toml.exists():
        print("⚠️  pyproject.toml not found, skipping pyproject.toml update")
        return
    
    content = pyproject_toml.read_text()
    
    # Replace version in [project] section
    new_content = re.sub(
        r'version\s*=\s*["\'][^"\']+["\']',
        f'version = "{new_version}"',
        content
    )
    
    pyproject_toml.write_text(new_content)
    print(f"✅ Updated pyproject.toml to version {new_version}")


def update_changelog(new_version, bump_type):
    """Update CHANGELOG.md with new version"""
    changelog = Path("CHANGELOG.md")
    if not changelog.exists():
        print("⚠️  CHANGELOG.md not found, skipping changelog update")
        return
    
    content = changelog.read_text()
    
    # Determine if this is a breaking change
    breaking_note = ""
    if bump_type == 'major':
        breaking_note = " (BREAKING CHANGES)"
    
    # Get current date
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Add new version entry at the top
    new_entry = f"""## [{new_version}]{breaking_note} - {date_str}

### Added
- Major refactor with enhanced Chain architecture
- Timezone-aware timestamps (Python 3.13+ compatibility)
- Comprehensive testing infrastructure (236 tests)

### Changed
- Migrated from `datetime.utcnow()` to `datetime.now(timezone.utc)`
- Streamlined connection handlers with proper error handling
- Enhanced type safety and consistency across modules

### Removed
- Obsolete documentation and example files
- Duplicate utility modules and backup files

### Fixed
- DateTime deprecation warnings
- Test failures related to timezone handling
- AttributeError issues with datetime.UTC

"""
    
    # Insert new entry after the title
    lines = content.split('\n')
    title_index = 0
    for i, line in enumerate(lines):
        if line.startswith('# '):
            title_index = i
            break
    
    # Insert after title and any description
    insert_index = title_index + 1
    while insert_index < len(lines) and not lines[insert_index].startswith('## '):
        insert_index += 1
    
    lines.insert(insert_index, new_entry)
    
    changelog.write_text('\n'.join(lines))
    print(f"✅ Updated CHANGELOG.md with version {new_version}")


def main():
    """Main release function"""
    if len(sys.argv) != 2 or sys.argv[1] not in ['patch', 'minor', 'major']:
        print("Usage: python release.py [patch|minor|major]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    
    print(f"🚀 Starting {bump_type} release for ModuLink-Py")
    
    # Check git status
    check_git_status()
    
    # Get current version
    current_version = get_current_version()
    print(f"📋 Current version: {current_version}")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"📋 New version: {new_version}")
    
    # Confirm release
    if bump_type == 'major':
        print("\n⚠️  MAJOR VERSION RELEASE - This includes breaking changes!")
        print("Breaking changes in this release:")
        print("- DateTime API migration (datetime.utcnow() → datetime.now(timezone.utc))")
        print("- Chain architecture refactor") 
        print("- Removed obsolete modules")
        print("- Test structure changes")
    
    confirm = input(f"\nProceed with {bump_type} release {current_version} → {new_version}? (yes/no): ").lower()
    if confirm != 'yes':
        print("❌ Release cancelled")
        sys.exit(1)
    
    # Update version files
    update_version_in_setup_py(new_version)
    update_version_in_pyproject_toml(new_version)
    update_changelog(new_version, bump_type)
    
    # Run tests
    run_command("python -m pytest tests/ -v", "Running test suite")
    
    # Commit version changes
    run_command("git add setup.py CHANGELOG.md pyproject.toml", "Staging version files")
    run_command(f'git commit -m "chore: bump version to {new_version}"', "Committing version bump")
    
    # Create tag
    tag_message = f"Release v{new_version}"
    if bump_type == 'major':
        tag_message += " (BREAKING CHANGES)"
    
    run_command(f'git tag -a v{new_version} -m "{tag_message}"', f"Creating tag v{new_version}")
    
    # Push changes and tag
    run_command("git push origin", "Pushing changes")
    run_command(f"git push origin v{new_version}", "Pushing tag")
    
    print(f"\n🎉 Successfully released ModuLink-Py v{new_version}!")
    print(f"📦 Tag: v{new_version}")
    print("🔗 Next steps:")
    print("  - The tag has been pushed to GitHub")
    print("  - Create a GitHub release from the tag")
    print("  - Consider publishing to PyPI if configured")


if __name__ == "__main__":
    main()
