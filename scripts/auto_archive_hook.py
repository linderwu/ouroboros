#!/usr/bin/env python3
"""
Ouroboros Auto-Archive Hook
Phase 1: Entropy Management

當 wiki 頁面超過 staleness threshold，自動歸檔。
"""

import os
import sys
import json
import yaml
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# === Config ===
SKILL_DIR = Path(__file__).parent.parent
STALNESS_RULES = SKILL_DIR / "references" / "staleness_rules.yaml"
WIKI_DIR = SKILL_DIR.parent.parent / "wiki"
ARCHIVE_DIR = SKILL_DIR / ".ouroboros" / "archive"
LOG_FILE = SKILL_DIR / ".ouroboros" / "staleness.log"

# === Load Config ===
def load_config() -> dict:
    if STALNESS_RULES.exists():
        with open(STALNESS_RULES) as f:
            return yaml.safe_load(f)
    return {"staleness_rules": {}, "archive_settings": {"enabled": False}}

# === Date Parsing ===
def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(date_str.split("T")[0], fmt)
        except ValueError:
            continue
    return None

# === Check Staleness ===
def check_page_staleness(page_path: Path, rules: dict) -> tuple[str, str]:
    """
    檢查單一頁面的 staleness。
    返回 (status, reason)
    status: "ok" | "warning" | "archive" | "delete"
    """
    if not page_path.exists():
        return "error", "page_not_found"
    
    # 讀取 frontmatter
    content = page_path.read_text()
    frontmatter = {}
    
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm_text = content[3:end]
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    frontmatter[key.strip()] = val.strip()
    
    # 取得類型和更新時間
    page_type = frontmatter.get("type", "concept")
    updated_str = frontmatter.get("updated", "")
    updated = parse_date(updated_str)
    
    # 取得規則
    type_rules = rules.get(page_type, rules.get("concept", {}))
    
    if not updated:
        return "warning", "no_updated_field"
    
    days_since_update = (datetime.now() - updated).days
    
    # 檢查各級閾值
    if "delete_threshold_days" in type_rules:
        if days_since_update >= type_rules["delete_threshold_days"]:
            return "delete", f"exceeded delete threshold ({days_since_update} days)"
    
    if "archive_threshold_days" in type_rules:
        if days_since_update >= type_rules["archive_threshold_days"]:
            return "archive", f"exceeded archive threshold ({days_since_update} days)"
    
    if "warning_threshold_days" in type_rules:
        if days_since_update >= type_rules["warning_threshold_days"]:
            return "warning", f"exceeded warning threshold ({days_since_update} days)"
    
    return "ok", f"fresh ({days_since_update} days)"

# === Archive Page ===
def archive_page(page_path: Path, reason: str):
    """將頁面移至歸檔目錄"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    
    # 計算歸檔路徑
    rel_path = page_path.relative_to(WIKI_DIR)
    archive_path = ARCHIVE_DIR / rel_path
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 讀取並更新內容
    content = page_path.read_text()
    
    # 在 frontmatter 加入歸檔標記
    if content.startswith("---"):
        end = content.find("---", 3)
        fm_text = content[3:end]
        rest = content[end+3:]
        
        archived_marker = f"\narchived_at: {datetime.now().isoformat()}\narchive_reason: {reason}\n"
        content = "---\n" + fm_text + archived_marker + "---\n" + rest
    
    # 寫入歸檔
    archive_path.write_text(content)
    
    # 刪除原始
    page_path.unlink()
    
    # 記錄日誌
    log_event("archive", str(page_path), str(archive_path), reason)

# === Log Event ===
def log_event(action: str, source: str, dest: str, reason: str):
    """記錄 staleness 事件"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "source": source,
        "dest": dest,
        "reason": reason
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

# === Scan Wiki ===
def scan_wiki(dry_run: bool = True):
    """掃描整個 wiki，檢查 staleness"""
    config = load_config()
    
    if not config.get("archive_settings", {}).get("enabled", False):
        print("⚠️  Archive is disabled in config")
        return
    
    results = {"ok": [], "warning": [], "archive": [], "delete": [], "error": []}
    
    # 遍歷所有 wiki 頁面
    for page_path in WIKI_DIR.rglob("*.md"):
        # 跳過目錄頁面
        if page_path.stem.startswith("index"):
            continue
        
        status, reason = check_page_staleness(page_path, config["staleness_rules"])
        results[status].append((page_path, reason))
        
        if status in ["archive", "delete"] and not dry_run:
            archive_page(page_path, reason)
    
    # 輸出報告
    print(f"\n📊 Ouroboros Staleness Scan Report")
    print(f"{'='*50}")
    print(f"OK:       {len(results['ok'])} pages")
    print(f"Warning:  {len(results['warning'])} pages")
    print(f"Archive:  {len(results['archive'])} pages")
    print(f"Delete:   {len(results['delete'])} pages")
    print(f"Error:    {len(results['error'])} pages")
    
    if results["warning"]:
        print(f"\n⚠️  Warning (needs review):")
        for path, reason in results["warning"][:5]:
            print(f"  - {path.relative_to(WIKI_DIR)}: {reason}")
        if len(results["warning"]) > 5:
            print(f"  ... and {len(results['warning']) - 5} more")
    
    if results["archive"] or results["delete"]:
        action = "ARCHIVE" if dry_run else "archived"
        print(f"\n🔴 {action.capitalize()} (dry_run={dry_run}):")
        for path, reason in results["archive"] + results["delete"]:
            print(f"  - {path.relative_to(WIKI_DIR)}: {reason}")
    
    if dry_run and (results["archive"] or results["delete"]):
        print(f"\n💡 Run with --execute to actually archive these pages")
    
    return results

# === CLI ===
if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv
    scan_wiki(dry_run=dry_run)
