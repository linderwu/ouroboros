#!/usr/bin/env python3
"""
Ouroboros Wikilinks Integrity Hook
Phase 2: Enforcement

檢查所有 wikilink [[...]] 是否指向存在的頁面。
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Set, List, Tuple
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Config ===
SKILL_DIR = Path(__file__).parent.parent
WORKSPACE_DIR = Path(os.environ.get("OUROBOROS_WORKSPACE_DIR", SKILL_DIR.parent.parent))
WIKI_DIR = Path(os.environ.get("OUROBOROS_WIKI_DIR", WORKSPACE_DIR / "wiki"))
LOG_FILE = SKILL_DIR / ".ouroboros" / "wikilinks_integrity.log"

# === Extract Wikilinks ===
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

def extract_wikilinks(content: str) -> List[str]:
    """從內容中提取所有 wikilink"""
    return WIKILINK_PATTERN.findall(content)

def resolve_wikilink(link: str, wiki_dir: Path, workspace_dir: Path = WORKSPACE_DIR) -> Path:
    """
    解析 wikilink 到實際檔案路徑。
    支援：
    - [[page]] -> wiki/page.md
    - [[category/page]] -> wiki/category/page.md
    - [[raw/evidence]] -> raw/evidence.md
    - [[repos/repo/path]] -> repos/repo/path
    - [[spec/module/SPEC]] -> spec/module/SPEC.md
    - [[page|display]] -> wiki/page.md
    """
    # 清理 link
    link = link.strip()
    
    # 移除 anchor（# 後面的部分）
    if "#" in link:
        link = link.split("#")[0]
    
    if not link:
        return None
    
    # 轉換成路徑
    # [[entity/abc]] -> entity/abc.md
    # [[abc]] -> abc.md (可能在根目錄或子目錄)
    
    link_path = Path(link.replace(".", "/"))  # a.b.c -> a/b/c
    
    link_parts = link_path.parts
    if link_parts and link_parts[0] in {"raw", "repos", "spec", "graphify"}:
        root = workspace_dir
    else:
        root = wiki_dir

    # 嘗試可能的擴展名
    for ext in [".md", ""]:
        # 直接在對應目錄
        candidate = root / f"{link_path}{ext}"
        if candidate.exists():
            return candidate

        if root != wiki_dir:
            continue

        # 在根目錄搜尋（標題可能在任意位置）
        for md_file in wiki_dir.rglob(f"{link_path.name}{ext}"):
            return md_file
    
    return None

# === Scan Wikilinks ===
def scan_wikilinks(wiki_dir: Path) -> dict:
    """掃描整個 wiki 的 wikilinks"""
    
    all_links: Set[str] = set()  # 所有被引用的 link
    all_files: Set[str] = set()  # 所有存在的檔案（不含 md 副檔名）
    broken_links: List[dict] = []  # 斷掉的 link
    
    # 收集所有 wiki 頁面
    for md_file in wiki_dir.rglob("*.md"):
        if md_file.stem.startswith("index"):
            continue
        
        # 記錄為存在的檔案（去除 .md）
        relative = md_file.relative_to(wiki_dir)
        all_files.add(str(relative.with_suffix("")).replace("\\", "/"))
        
        # 提取 wikilinks
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        links = extract_wikilinks(content)
        
        for link in links:
            all_links.add(link.strip())
            
            # 檢查是否能解析到檔案
            resolved = resolve_wikilink(link, wiki_dir)
            
            if resolved is None or not resolved.exists():
                broken_links.append({
                    "source": str(md_file.relative_to(wiki_dir)),
                    "link": link,
                    "resolved": str(resolved) if resolved else "NOT_FOUND"
                })
    
    return {
        "total_files": len(all_files),
        "total_links": len(all_links),
        "broken_links": broken_links,
        "all_files": sorted(all_files),
        "all_links": sorted(all_links)
    }

# === Generate Report ===
def generate_report(results: dict) -> str:
    """生成完整性報告"""
    report = []
    report.append("=" * 60)
    report.append("Ouroboros Wikilinks Integrity Report")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("=" * 60)
    report.append("")
    report.append(f"Total wiki files: {results['total_files']}")
    report.append(f"Total wikilinks: {results['total_links']}")
    report.append(f"Broken links: {len(results['broken_links'])}")
    report.append("")
    
    if results["broken_links"]:
        report.append("🔴 BROKEN LINKS:")
        report.append("-" * 40)
        
        # 按來源分組
        by_source = {}
        for bl in results["broken_links"]:
            source = bl["source"]
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(bl["link"])
        
        for source, links in sorted(by_source.items()):
            report.append(f"\n📄 {source}")
            for link in links:
                report.append(f"   ❌ [[{link}]]")
        
        report.append("")
        report.append("💡 FIX: Update or remove broken wikilinks")
    else:
        report.append("✅ All wikilinks are valid!")
    
    return "\n".join(report)

# === Log Results ===
def log_results(results: dict):
    """記錄到日誌"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 只記錄 broken links
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "total_files": results["total_files"],
        "total_links": results["total_links"],
        "broken_count": len(results["broken_links"]),
        "broken_links": results["broken_links"]
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# === CLI ===
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ouroboros Wikilinks Integrity Check")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-fix broken links (replace with warning)")
    args = parser.parse_args()
    
    print("🔍 Scanning wikilinks integrity...")
    print(f"Workspace: {WORKSPACE_DIR}")
    print(f"Wiki: {WIKI_DIR}")
    print()
    
    results = scan_wikilinks(WIKI_DIR)
    report = generate_report(results)
    print(report)
    
    # 記錄
    log_results(results)
    
    # 如果有斷鏈，退出碼非零
    if results["broken_links"]:
        print(f"\n📝 Logged to {LOG_FILE}")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
