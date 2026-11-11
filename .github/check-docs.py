#!/usr/bin/env python3
"""
check-docs
==========
Consistency checks for the Markdown documentation. Run from the repository root:

    python3 .github/check-docs.py

Checks:

1. Every relative link in README.md, CONTRIBUTING.md and docs/**/*.md points to
   an existing file, and every #anchor to an existing heading (GitHub slug
   rules). External links are not checked.
2. Every script in the repository (top-level *.sh, scripts/*.py, scripts/*.sh)
   is mentioned in docs/scripts.md.

Exits with status 1 if any check fails.
"""

import glob
import os
import re
import sys

errors = []


def slugify(heading):
    """GitHub's anchor for a Markdown heading."""
    s = heading.strip().lower()
    s = re.sub(r'[^\w\- ]', '', s)
    return s.replace(' ', '-')


def anchors(path):
    """All anchors defined by the headings of a Markdown file."""
    result = set()
    counts = {}
    inCode = False
    for line in open(path, encoding='utf-8'):
        if line.startswith('```'):
            inCode = not inCode
            continue
        m = re.match(r'^#{1,6}\s+(.*?)\s*#*\s*$', line)
        if m and not inCode:
            slug = slugify(m.group(1))
            n = counts.get(slug, 0)
            counts[slug] = n + 1
            result.add(slug if n == 0 else '{}-{}'.format(slug, n))
    return result


def checkLinks(path):
    text = open(path, encoding='utf-8').read()
    text = re.sub(r'```.*?```', '', text, flags=re.S)  # ignore code blocks
    for target in re.findall(r'\]\(([^)\s]+)\)', text):
        if re.match(r'^[a-z]+:', target):  # http:, https:, mailto:
            continue
        file, _, fragment = target.partition('#')
        dest = os.path.normpath(os.path.join(os.path.dirname(path), file)) if file else path
        if not os.path.exists(dest):
            errors.append('{}: broken link to {}'.format(path, target))
            continue
        if fragment and dest.endswith('.md') and fragment not in anchors(dest):
            errors.append('{}: no heading for anchor #{} in {}'.format(path, fragment, dest))


docs = ['README.md', 'CONTRIBUTING.md'] + glob.glob('docs/**/*.md', recursive=True)
for doc in docs:
    checkLinks(doc)

reference = open('docs/scripts.md', encoding='utf-8').read()
scripts = glob.glob('*.sh') + glob.glob('scripts/*.py') + glob.glob('scripts/*.sh')
for script in sorted(scripts):
    name = os.path.basename(script)
    if name not in reference:
        errors.append('docs/scripts.md: script {} is not documented'.format(script))

for error in errors:
    print(error)
print('{} documentation files checked, {} problem(s) found.'.format(len(docs), len(errors)))
sys.exit(1 if errors else 0)
