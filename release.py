#!/usr/bin/env python3
"""
Release Script for ModuLink-Py
Handles version bumping and release workflow
Usage: python release.py [patch|minor|major] [--release-notes <str|file>] [--changelog <str|file>] [--yes] [--force]
Defaults to major version bump if no argument is provided
"""

import sys
import subprocess
import json
import re
from pathlib import Path
import shutil
import argparse


def run_command(command, description):
    """Execute command and handle errors"""
    try:
        print(f"🔄 {description}...")
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Release ModuLink-Py with automation-friendly options.")
    parser.add_argument("bump", nargs="?", choices=["patch", "minor", "major"], default="major", help="Version bump type")
    parser.add_argument("--release-notes", type=str, help="Release notes (string or @file)")
    parser.add_argument("--changelog", type=str, help="Changelog entry (string or @file)")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm all prompts")
    parser.add_argument("--force", action="store_true", help="Auto-continue on uncommitted changes or version mismatch")
    parser.add_argument("--rollback", action="store_true", help="Rollback last release")
    return parser.parse_args()

def read_arg_content(val):
    if val and val.startswith("@"):
        with open(val[1:], "r") as f:
            return f.read()
    return val


def check_git_status(args):
    """Check if working directory is clean"""
    try:
        status = subprocess.run(
            "git status --porcelain",
            shell=True,
            capture_output=True,
            text=True,
            check=True,
        )
        if status.stdout.strip():
            print("📋 Uncommitted changes detected:")
            print(status.stdout)
            print("\n⚠️  Please commit or stash changes before releasing.")
            if args.force or args.yes:
                print("--force or --yes provided, continuing despite uncommitted changes.")
            else:
                force = input("Continue anyway? (yes/no): ").lower()
                if force != "yes":
                    sys.exit(1)
        else:
            print("✅ Working directory is clean")
    except subprocess.CalledProcessError:
        print("❌ Failed to check git status")
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
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        print(f"❌ Invalid bump type: {bump_type}")
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def validate_version_bump(current_version, new_version, bump_type):
    """Validate that the version bump is reasonable and not skipping versions"""
    current_parts = list(map(int, current_version.split(".")))
    new_parts = list(map(int, new_version.split(".")))
    
    current_major, current_minor, current_patch = current_parts
    new_major, new_minor, new_patch = new_parts
    
    # Check for reasonable version progression
    if bump_type == "major":
        expected_major = current_major + 1
        if new_major != expected_major:
            print(f"❌ Invalid major version bump!")
            print(f"   Current: {current_version}")
            print(f"   Expected: {expected_major}.0.0")
            print(f"   Got: {new_version}")
            print(f"   This would skip from version {current_major} to {new_major}")
            return False
        if new_minor != 0 or new_patch != 0:
            print(f"❌ Major version bump should reset minor and patch to 0")
            return False
    
    elif bump_type == "minor":
        if new_major != current_major:
            print(f"❌ Minor version bump should not change major version")
            print(f"   Current: {current_version}")
            print(f"   Expected: {current_major}.{current_minor + 1}.0")
            print(f"   Got: {new_version}")
            return False
        expected_minor = current_minor + 1
        if new_minor != expected_minor:
            print(f"❌ Invalid minor version bump!")
            print(f"   This would skip from {current_major}.{current_minor}.x to {current_major}.{new_minor}.x")
            return False
        if new_patch != 0:
            print(f"❌ Minor version bump should reset patch to 0")
            return False
    
    elif bump_type == "patch":
        if new_major != current_major or new_minor != current_minor:
            print(f"❌ Patch version bump should not change major or minor version")
            return False
        expected_patch = current_patch + 1
        if new_patch != expected_patch:
            print(f"❌ Invalid patch version bump!")
            print(f"   This would skip from {current_version} to {new_version}")
            return False
    
    return True


def get_latest_git_tag():
    """Get the latest git tag to compare with current version"""
    try:
        result = subprocess.run(
            "git describe --tags --abbrev=0",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().lstrip('v')  # Remove 'v' prefix if present
    except subprocess.CalledProcessError:
        # No tags found
        return None


def update_version_in_setup_py(new_version):
    """Update version in setup.py"""
    setup_py = Path("setup.py")
    content = setup_py.read_text()

    # Replace version
    new_content = re.sub(
        r'version=["\'][^"\']+["\']', f'version="{new_version}"', content
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
        r'version\s*=\s*["\'][^"\']+["\']', f'version = "{new_version}"', content
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
    if bump_type == "major":
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
    lines = content.split("\n")
    title_index = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title_index = i
            break

    # Insert after title and any description
    insert_index = title_index + 1
    while insert_index < len(lines) and not lines[insert_index].startswith("## "):
        insert_index += 1

    lines.insert(insert_index, new_entry)

    changelog.write_text("\n".join(lines))
    print(f"✅ Updated CHANGELOG.md with version {new_version}")


def get_commit_log_since_last_tag():
    try:
        last_tag = subprocess.run(
            "git describe --tags --abbrev=0",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        if last_tag:
            log_cmd = f"git log {last_tag}..HEAD --pretty=format:'- %s'"
        else:
            log_cmd = "git log --pretty=format:'- %s'"
        log = subprocess.run(
            log_cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        return log
    except subprocess.CalledProcessError:
        return None


def prompt_and_update_file(filename, prompt_text, arg_val=None, auto_changelog=False):
    if arg_val is not None:
        content = read_arg_content(arg_val)
        with open(filename, "w") as f:
            f.write(content.strip() + "\n")
        subprocess.run(f"git add {filename}", shell=True)
        print(f"✅ {filename} updated and staged (from argument).")
        return
    if auto_changelog and filename == "CHANGELOG.md":
        log = get_commit_log_since_last_tag()
        if log:
            print("Auto-generating changelog from commit history:")
            print(log)
            content = log + "\n"
            with open(filename, "w") as f:
                f.write(content)
            subprocess.run(f"git add {filename}", shell=True)
            print(f"✅ {filename} updated and staged (auto changelog from git log).")
            return
    print(f"\n--- {filename} not staged. Please enter content below. End input with a single '.' on a line ---")
    print(prompt_text)
    lines = []
    while True:
        line = input()
        if line.strip() == ".":
            break
        lines.append(line)
    content = "\n".join(lines) + "\n"
    with open(filename, "w") as f:
        f.write(content)
    subprocess.run(f"git add {filename}", shell=True)
    print(f"✅ {filename} updated and staged.")

def check_release_notes_and_changelog(args):
    result = subprocess.run("git diff --name-only --cached", shell=True, capture_output=True, text=True)
    staged = set(result.stdout.strip().splitlines())
    required = {"release-notes.md", "CHANGELOG.md"}
    missing = required - staged
    if missing:
        for fname in missing:
            if fname == "release-notes.md":
                prompt_and_update_file(fname, "Enter release notes for this version:", args.release_notes)
            elif fname == "CHANGELOG.md":
                prompt_and_update_file(fname, "Enter changelog entry for this version:", args.changelog, auto_changelog=True)
    else:
        print("✅ release-notes.md and CHANGELOG.md are staged for release.")

def rollback_release():
    """Rollback the most recent release commit and tag, and clean build artifacts."""
    def get_latest_tag():
        out = subprocess.run("git describe --tags --abbrev=0", shell=True, capture_output=True, text=True)
        return out.stdout.strip()
    tag = get_latest_tag()
    if not tag:
        print("No tags found. Nothing to rollback.")
        sys.exit(1)
    print(f"Latest tag: {tag}")
    confirm = input(f"Delete tag {tag} and reset last commit? (yes/no): ").lower()
    if confirm != "yes":
        print("Rollback cancelled.")
        sys.exit(0)
    run_command(f"git tag -d {tag}", f"Delete local tag {tag}")
    run_command(f"git push --delete origin {tag}", f"Delete remote tag {tag}")
    run_command("git reset --hard HEAD~1", "Reset last commit (version bump)")
    # Clean up build artifacts
    for artifact in ["dist", "build", "modulink_py.egg-info"]:
        try:
            shutil.rmtree(artifact)
            print(f"✅ Removed {artifact}/")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"⚠️  Could not remove {artifact}/: {e}")
    print("\n🎯 Rollback complete. Repo is now at previous state and all build artifacts are removed.")


def main():
    args = parse_args()
    if args.rollback:
        rollback_release()
        return
    check_release_notes_and_changelog(args)
    bump_type = args.bump
    print(f"🚀 Starting {bump_type} release for ModuLink-Py")
    check_git_status(args)
    run_command("python -m pytest modulink/tests/ -v", "Running test suite BEFORE release")
    current_version = get_current_version()
    print(f"📋 Current version in files: {current_version}")
    latest_tag = get_latest_git_tag()
    if latest_tag:
        print(f"📋 Latest git tag: v{latest_tag}")
        if latest_tag != current_version:
            print(f"⚠️  WARNING: Version in files ({current_version}) differs from latest tag ({latest_tag})")
            print("   This might indicate the files were manually updated")
            if args.force or args.yes:
                print("--force or --yes provided, continuing despite version mismatch.")
            else:
                proceed = input("   Continue anyway? (yes/no): ").lower()
                if proceed != "yes":
                    print("❌ Release cancelled")
                    sys.exit(1)
    else:
        print("📋 No git tags found - this will be the first tagged release")
    new_version = bump_version(current_version, bump_type)
    print(f"📋 New version: {new_version}")
    if not validate_version_bump(current_version, new_version, bump_type):
        print(f"\n❌ Version bump validation failed!")
        print(f"   This prevents accidentally skipping versions")
        print(f"   Current: {current_version}")
        print(f"   Attempted: {new_version}")
        print(f"   Bump type: {bump_type}")
        sys.exit(1)
    print(f"✅ Version bump validation passed")
    if bump_type == "major":
        print("\n⚠️  MAJOR VERSION RELEASE - This includes breaking changes!")
        print("Breaking changes in this release:")
        print("- DateTime API migration (datetime.utcnow() → datetime.now(timezone.utc))")
        print("- Chain architecture refactor")
        print("- Removed obsolete modules")
        print("- Test structure changes")
    if args.yes:
        print("--yes provided, auto-confirming release.")
        confirm = "yes"
    else:
        confirm = input(f"\nProceed with {bump_type} release {current_version} → {new_version}? (yes/no): ").lower()
    if confirm != "yes":
        print("❌ Release cancelled")
        sys.exit(1)
    update_version_in_setup_py(new_version)
    update_version_in_pyproject_toml(new_version)
    update_changelog(new_version, bump_type)
    run_command("python -m build", "Building wheel and sdist")
    run_command("git add setup.py CHANGELOG.md pyproject.toml", "Staging version files")
    run_command(f'git commit -m "chore: bump version to {new_version}"', "Committing version bump")
    tag_message = f"Release v{new_version}"
    if bump_type == "major":
        tag_message += " (BREAKING CHANGES)"
    run_command(f'git tag -a v{new_version} -m "{tag_message}"', f"Creating tag v{new_version}")
    run_command("git push origin", "Pushing changes")
    run_command(f"git push origin v{new_version}", "Pushing tag")
    print(f"\n🎉 Successfully released ModuLink-Py v{new_version}!")
    print(f"📦 Tag: v{new_version}")
    print("🔗 Next steps:")
    print("  - The tag has been pushed to GitHub")
    print("  - Create a GitHub release from the tag")
    print("  - Consider publishing to PyPI if configured")


def main_release(*args, **kwargs):
    main(*args, **kwargs)

if __name__ == "__main__":
    main()
