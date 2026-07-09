#!/usr/bin/env python3
"""
Ouroboros Deduplication Hook
Phase 1: Entropy Management

檢測近義重複的 wiki 頁面。
"""

import os
import sys
import json
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Config ===
SKILL_DIR = Path(__file__).parent.parent
WORKSPACE_DIR = Path(os.environ.get("OUROBOROS_WORKSPACE_DIR", SKILL_DIR.parent.parent))
WIKI_DIR = Path(os.environ.get("OUROBOROS_WIKI_DIR", WORKSPACE_DIR / "wiki"))
SIMILARITY_THRESHOLD = 0.85  # 超過這個相似度視為重複
LOG_FILE = SKILL_DIR / ".ouroboros" / "deduplication.log"

# === Simple Text Similarity ===
def text_similarity(text1: str, text2: str) -> float:
    """計算兩個文字的相似度（使用 SequenceMatcher）"""
    # 標準化：去除空白、小寫
    t1 = " ".join(text1.lower().split())
    t2 = " ".join(text2.lower().split())
    
    return SequenceMatcher(None, t1, t2).ratio()

def title_similarity(title1: str, title2: str) -> float:
    """計算標題的相似度（更嚴格）"""
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    
    # 完全相同
    if t1 == t2:
        return 1.0
    
    # 一個包含另一個
    if t1 in t2 or t2 in t1:
        return 0.9
    
    # 單詞重疊
    words1 = set(t1.split())
    words2 = set(t2.split())
    
    if not words1 or not words2:
        return 0.0
    
    overlap = len(words1 & words2)
    union = len(words1 | words2)
    
    return overlap / union

# === Extract Page Info ===
def extract_page_info(page_path: Path) -> dict:
    """從 wiki 頁面提取資訊"""
    content = page_path.read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
    
    # 預設值
    info = {
        "path": str(page_path),
        "relative_path": str(page_path.relative_to(WIKI_DIR)),
        "title": page_path.stem.replace("-", " ").replace("_", " ").title(),
        "type": "unknown",
        "content_hash": hashlib.md5(content.encode()).hexdigest(),
        "content_length": len(content)
    }
    
    # 解析 frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm_text = content[3:end]
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    
                    if key == "title":
                        info["title"] = val
                    elif key == "type":
                        info["type"] = val
    
    return info

# === Find Duplicates ===
def find_duplicates(wiki_dir: Path, threshold: float = SIMILARITY_THRESHOLD) -> List[dict]:
    """找出近義重複的頁面"""
    # 收集所有頁面
    pages = []
    for page_path in wiki_dir.rglob("*.md"):
        # 跳過目錄頁面
        if page_path.stem.startswith("index"):
            continue
        pages.append(extract_page_info(page_path))
    
    # 比較找出重複
    duplicates = []
    checked = set()
    
    for i, page1 in enumerate(pages):
        for page2 in pages[i+1:]:
            pair_key = tuple(sorted([page1["relative_path"], page2["relative_path"]]))
            if pair_key in checked:
                continue
            checked.add(pair_key)
            
            # 檢查標題相似度
            title_sim = title_similarity(page1["title"], page2["title"])
            
            if title_sim >= threshold:
                duplicates.append({
                    "page1": page1["relative_path"],
                    "page2": page2["relative_path"],
                    "title1": page1["title"],
                    "title2": page2["title"],
                    "title_similarity": round(title_sim, 3),
                    "type1": page1["type"],
                    "type2": page2["type"]
                })
                continue
            
            # 如果類型相同且標題部分相似，進一步檢查內容
            if page1["type"] == page2["type"] and title_sim > 0.5:
                # 讀取內容進行比較
                content1 = Path(page1["path"]).read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
                content2 = Path(page2["path"]).read_text(encoding="utf-8", errors="ignore").lstrip("\ufeff")
                
                # 去除 frontmatter
                if content1.startswith("---"):
                    end1 = content1.find("---", 3)
                    if end1 > 0:
                        content1 = content1[end1+3:]
                if content2.startswith("---"):
                    end2 = content2.find("---", 3)
                    if end2 > 0:
                        content2 = content2[end2+3:]
                
                content_sim = text_similarity(content1[:2000], content2[:2000])  # 只比較前 2000 字
                
                if content_sim >= threshold:
                    duplicates.append({
                        "page1": page1["relative_path"],
                        "page2": page2["relative_path"],
                        "title1": page1["title"],
                        "title2": page2["title"],
                        "title_similarity": round(title_sim, 3),
                        "content_similarity": round(content_sim, 3),
                        "type1": page1["type"],
                        "type2": page2["type"]
                    })
    
    return duplicates

# === Log Duplicates ===
def log_duplicates(duplicates: List[dict]):
    """記錄重複頁面到日誌"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "duplicates_count": len(duplicates),
        "duplicates": duplicates
    }
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# === CLI ===
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ouroboros Deduplication Hook")
    parser.add_argument("--threshold", type=float, default=SIMILARITY_THRESHOLD,
                        help=f"Similarity threshold (default: {SIMILARITY_THRESHOLD})")
    parser.add_argument("--fix", action="store_true",
                        help="Attempt to auto-merge duplicates (NOT IMPLEMENTED)")
    args = parser.parse_args()
    
    print(f"🔍 Scanning for duplicates in {WIKI_DIR}")
    print(f"   Workspace: {WORKSPACE_DIR}")
    print(f"   Threshold: {args.threshold}")
    print()
    
    duplicates = find_duplicates(WIKI_DIR, args.threshold)
    
    if not duplicates:
        print("✅ No duplicates found!")
        return
    
    print(f"⚠️  Found {len(duplicates)} potential duplicates:\n")
    
    for dup in duplicates:
        print(f"📄 {dup['title1']} ({dup['type1']})")
        print(f"   ↔️  {dup['title2']} ({dup['type2']})")
        print(f"   Similarity: {dup.get('title_similarity', dup.get('content_similarity', 'N/A'))}")
        print()
    
    # 記錄
    log_duplicates(duplicates)
    print(f"📝 Logged to {LOG_FILE}")
    
    print("\n💡 To auto-merge, run with --fix (not yet implemented)")
    print("💡 Manual action required: review and consolidate duplicates")

if __name__ == "__main__":
    main()
