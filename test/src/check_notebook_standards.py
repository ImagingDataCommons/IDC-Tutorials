"""
Check that all notebooks (excluding deprecated/) follow IDC-Tutorials standards:
  1. Include a "## Support" section
  2. Include a "## Acknowledgments" section
  3. Reference the IDC-Tutorials repository for additional tutorials
  4. Include an "Updated: <Month> <Year>" field
  5. Include a correct Colab badge link pointing to the notebook's own path
"""

import json
import os
import re
import sys
from pathlib import Path


NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "notebooks"

# Directories to skip
SKIP_DIRS = {"deprecated"}

# Pattern for "Updated: <Month> <Year>" (e.g., "Updated: Feb 2026")
MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
UPDATED_RE = re.compile(rf"Updated:\s*{MONTH_PATTERN}\s+\d{{4}}")

IDC_TUTORIALS_URL = "github.com/ImagingDataCommons/IDC-Tutorials"

COLAB_PREFIX = "https://colab.research.google.com/github/ImagingDataCommons/IDC-Tutorials/blob/master/"
COLAB_LINK_RE = re.compile(
    r'https://colab\.research\.google\.com/github/[^">\s]+'
)


def get_markdown_sources(notebook_path):
    """Return a list of concatenated source strings for each markdown cell."""
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cells = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "markdown":
            source = cell.get("source", [])
            if isinstance(source, list):
                text = "".join(source)
            else:
                text = source
            cells.append(text)
    return cells


def check_notebook(notebook_path):
    """Check a single notebook for required standards. Returns list of issues."""
    issues = []
    rel_path = notebook_path.relative_to(NOTEBOOKS_DIR.parent)
    cells = get_markdown_sources(notebook_path)
    all_text = "\n".join(cells)

    # Check 1: "## Support" section
    if "## Support" not in all_text:
        issues.append("Missing '## Support' section")

    # Check 2: "## Acknowledgments" section (allow both spellings)
    if "## Acknowledgments" not in all_text and "## Acknowledgements" not in all_text:
        issues.append("Missing '## Acknowledgments' section")

    # Check 3: Reference to IDC-Tutorials repository
    if IDC_TUTORIALS_URL not in all_text:
        issues.append(
            f"Missing reference to IDC-Tutorials repository ({IDC_TUTORIALS_URL})"
        )

    # Check 4: "Updated: <Month> <Year>" field
    if not UPDATED_RE.search(all_text):
        issues.append("Missing 'Updated: <Month> <Year>' field (e.g., 'Updated: Feb 2026')")

    # Check 5: Colab badge link exists and points to correct path
    expected_colab_url = COLAB_PREFIX + str(rel_path)
    colab_links = COLAB_LINK_RE.findall(all_text)
    if not colab_links:
        issues.append("Missing Colab badge link")
    else:
        # Check the first colab link (the badge) points to this notebook
        badge_link = colab_links[0]
        if badge_link != expected_colab_url:
            issues.append(
                f"Colab badge link mismatch:\n"
                f"        found:    {badge_link}\n"
                f"        expected: {expected_colab_url}"
            )

    return issues


def find_notebooks(root_dir):
    """Find all .ipynb files, excluding SKIP_DIRS."""
    notebooks = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove skip dirs so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname.endswith(".ipynb") and ".ipynb_checkpoints" not in dirpath:
                notebooks.append(Path(dirpath) / fname)
    return sorted(notebooks)


def main():
    notebooks = find_notebooks(NOTEBOOKS_DIR)
    if not notebooks:
        print("ERROR: No notebooks found!")
        sys.exit(1)

    print(f"Checking {len(notebooks)} notebooks for standards compliance...\n")

    failed = {}
    for nb_path in notebooks:
        rel_path = nb_path.relative_to(NOTEBOOKS_DIR.parent)
        issues = check_notebook(nb_path)
        if issues:
            failed[str(rel_path)] = issues

    if failed:
        print("FAILED notebooks:\n")
        for path, issues in sorted(failed.items()):
            print(f"  {path}:")
            for issue in issues:
                print(f"    - {issue}")
            print()
        print(f"{len(failed)} notebook(s) failed standards checks.")
        sys.exit(1)
    else:
        print("All notebooks passed standards checks.")
        sys.exit(0)


if __name__ == "__main__":
    main()
