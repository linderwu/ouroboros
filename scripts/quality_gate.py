#!/usr/bin/env python3
"""
Ouroboros Quality Gate
Phase 4: QA Automation

在 PR merge 前自動檢查：
- Frontmatter schema 正確性
- Wikilinks 完整性
- 內容長度限制
- 標題重複檢查
"""

import os
import sys
import json
import yaml
import jsonschema
from pathlib import Path
from typing import List, Tuple

# === Config ===
import os

SKILL_DIR = Path(__file__).parent.parent
# Allow override via environment variable
WIKI_DIR = Path(os.environ.get("OUROBOROS_WIKI_DIR", SKILL_DIR.parent.parent / "wiki"))
SCHEMA_FILE = SKILL_DIR / "references" / "frontmatter_schema.json"
STALNESS_FILE = SKILL_DIR / "references" / "staleness_rules.yaml"

# === Load Schema ===
def load_schema() -> dict:
    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE) as f:
            return json.load(f)
    return {}

def load_stalness_rules() -> dict:
    if STALNESS_FILE.exists():
        with open(STALNESS_FILE) as f:
            return yaml.safe_load(f)
    return {}

# === Validation Functions ===
def validate_frontmatter(page_path: Path, schema: dict) -> Tuple[bool, List[str]]:
    """驗證 frontmatter 是否符合 schema"""
    errors = []
    
    content = page_path.read_text(errors="ignore")
    
    if not content.startswith("---"):
        return True, []  # No frontmatter is ok for some pages
    
    end = content.find("---", 3)
    if end <= 0:
        return True, []
    
    fm_text = content[3:end]
    
    # 解析 frontmatter
    fm = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    
    # 驗證 required fields
    required = schema.get("required", [])
    for field in required:
        if field not in fm:
            errors.append(f"Missing required field: {field}")
    
    # 驗證 type enum
    if "type" in fm:
        allowed_types = schema.get("properties", {}).get("type", {}).get("enum", [])
        if allowed_types and fm["type"] not in allowed_types:
            errors.append(f"Invalid type '{fm['type']}'. Must be one of: {allowed_types}")
    
    # 驗證 status enum
    if "status" in fm:
        allowed_statuses = schema.get("properties", {}).get("status", {}).get("enum", [])
        if allowed_statuses and fm["status"] not in allowed_statuses:
            errors.append(f"Invalid status '{fm['status']}'. Must be one of: {allowed_statuses}")
    
    return len(errors) == 0, errors

def check_content_length(page_path: Path, max_chars: int = 5000) -> Tuple[bool, str]:
    """檢查內容長度"""
    content = page_path.read_text(errors="ignore")
    
    # 去除 frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            content = content[end+3:]
    
    content = content.strip()
    
    if len(content) > max_chars:
        return False, f"Content too long ({len(content)} chars > {max_chars} limit)"
    
    return True, ""

def check_duplicate_titles(page_path: Path, all_titles: dict) -> Tuple[bool, str]:
    """檢查標題是否重複"""
    content = page_path.read_text(errors="ignore")
    
    # 取得標題
    title = None
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            for line in content[3:end].split("\n"):
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    break
    
    if not title:
        return True, ""
    
    if title in all_titles:
        return False, f"Duplicate title '{title}' (first seen in {all_titles[title]})"
    
    all_titles[title] = str(page_path.relative_to(WIKI_DIR))
    return True, ""

# === Wikilinks Check (from integrity_hook) ===
def check_broken_wikilinks(page_path: Path, all_files: set) -> Tuple[bool, List[str]]:
    """檢查單一頁面的 wikilinks"""
    import re
    
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
    
    errors = []
    content = page_path.read_text(errors="ignore")
    links = WIKILINK_PATTERN.findall(content)
    
    for link in links:
        link = link.strip()
        
        # 移除 anchor
        if "#" in link:
            link = link.split("#")[0]
        
        if not link:
            continue
        
        # 嘗試解析
        link_path = Path(link.replace(".", "/"))
        
        found = False
        for ext in [".md", ""]:
            candidate = link_path.name + ext
            if candidate in all_files or str(link_path) in all_files:
                found = True
                break
        
        if not found:
            errors.append(f"Broken wikilink: [[{link}]]")
    
    return len(errors) == 0, errors

# === Main Gate Check ===
def run_quality_gate(dry_run: bool = True) -> dict:
    """執行品質關卡"""
    schema = load_schema()
    stalness_rules = load_stalness_rules()
    
    results = {
        "pages_checked": 0,
        "pages_passed": 0,
        "pages_failed": 0,
        "errors": [],
        "warnings": []
    }
    
    # 收集所有檔案（用於 wikilinks 檢查）
    all_files = set()
    all_titles = {}
    
    for md_file in WIKI_DIR.rglob("*.md"):
        if md_file.stem.startswith("index"):
            continue
        relative = str(md_file.relative_to(WIKI_DIR))
        all_files.add(relative)
        all_files.add(md_file.stem)
    
    # 檢查每個頁面
    for page_path in WIKI_DIR.rglob("*.md"):
        if page_path.stem.startswith("index"):
            continue
        
        results["pages_checked"] += 1
        page_errors = []
        
        # 1. Frontmatter schema
        valid, errors = validate_frontmatter(page_path, schema)
        page_errors.extend(errors)
        
        # 2. Content length
        valid, msg = check_content_length(page_path)
        if not valid:
            page_errors.append(msg)
        
        # 3. Duplicate titles
        valid, msg = check_duplicate_titles(page_path, all_titles)
        if not valid:
            page_errors.append(msg)
        
        # 4. Broken wikilinks
        valid, errors = check_broken_wikilinks(page_path, all_files)
        page_errors.extend(errors)
        
        if page_errors:
            results["pages_failed"] += 1
            results["errors"].append({
                "page": str(page_path.relative_to(WIKI_DIR)),
                "errors": page_errors
            })
        else:
            results["pages_passed"] += 1
    
    return results

# === CLI ===
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ouroboros Quality Gate")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with error code if any check fails")
    args = parser.parse_args()
    
    print("🔍 Running Ouroboros Quality Gate...")
    print()
    
    results = run_quality_gate()
    
    print(f"Pages checked: {results['pages_checked']}")
    print(f"Pages passed: {results['pages_passed']}")
    print(f"Pages failed: {results['pages_failed']}")
    print()
    
    if results["errors"]:
        print("🔴 ERRORS:")
        for err in results["errors"][:10]:
            print(f"\n📄 {err['page']}:")
            for e in err["errors"]:
                print(f"   ❌ {e}")
        
        if len(results["errors"]) > 10:
            print(f"\n... and {len(results['errors']) - 10} more pages with errors")
        
        print()
        
        if args.strict:
            sys.exit(1)
    else:
        print("✅ All pages passed quality gate!")
    
    return results

if __name__ == "__main__":
    main()
