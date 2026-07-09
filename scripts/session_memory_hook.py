#!/usr/bin/env python3
"""
Ouroboros Session Memory Hook
Phase 6: Working Memory Integration

在每次 Ouroboros 執行後，自動更新 session memory。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Config ===
SKILL_DIR = Path(__file__).parent.parent
WORKSPACE_DIR = Path(os.environ.get("OUROBOROS_WORKSPACE_DIR", SKILL_DIR.parent.parent))
MEMORY_DIR = WORKSPACE_DIR / "memory"

# === Session Memory Management ===
class SessionMemory:
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def _today_file(self) -> Path:
        """取得今日的 memory 檔案"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.memory_dir / f"{today}.md"
    
    def _ensure_today_file(self):
        """確保今日檔案存在"""
        today_file = self._today_file()
        if not today_file.exists():
            today_file.write_text(f"# {datetime.now().strftime('%Y-%m-%d')}\n\n", encoding="utf-8")
        return today_file
    
    def append_entry(self, entry: str, category: str = "General"):
        """新增 entry 到今日 memory"""
        today_file = self._ensure_today_file()
        
        timestamp = datetime.now().strftime("%H:%M")
        content = f"\n## [{timestamp}] {category}\n\n{entry}\n"
        
        with open(today_file, "a", encoding="utf-8") as f:
            f.write(content)
    
    def record_phase_completion(self, phase: str, results: dict):
        """記錄 Phase 完成狀態"""
        results_str = json.dumps(results, ensure_ascii=False, indent=2)
        entry = f"""
**Phase**: {phase}
**Status**: completed
**Results**:
```json
{results_str}
```
"""
        self.append_entry(entry, category="Ouroboros Phase")
    
    def record_decision(self, decision: str, reason: str):
        """記錄關鍵決策"""
        entry = f"""
**Decision**: {decision}
**Reason**: {reason}
"""
        self.append_entry(entry, category="Decision")
    
    def record_issue(self, issue: str, severity: str = "medium"):
        """記錄問題"""
        entry = f"""
**Issue**: {issue}
**Severity**: {severity}
"""
        self.append_entry(entry, category="Issue")
    
    def get_today_summary(self) -> str:
        """取得今日摘要"""
        today_file = self._today_file()
        if today_file.exists():
            return today_file.read_text(encoding="utf-8")
        return ""

# === CLI ===
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ouroboros Session Memory Hook")
    parser.add_argument("--phase", help="Record phase completion")
    parser.add_argument("--decision", help="Record a decision")
    parser.add_argument("--reason", help="Reason for decision")
    parser.add_argument("--issue", help="Record an issue")
    parser.add_argument("--severity", default="medium", help="Issue severity")
    parser.add_argument("--entry", help="Custom entry text")
    parser.add_argument("--category", default="General", help="Entry category")
    args = parser.parse_args()
    
    memory = SessionMemory()
    
    if args.phase:
        memory.record_phase_completion(args.phase, {"status": "ok"})
        print(f"✅ Recorded phase completion: {args.phase}")
    
    if args.decision:
        reason = args.reason or "N/A"
        memory.record_decision(args.decision, reason)
        print(f"✅ Recorded decision: {args.decision}")
    
    if args.issue:
        memory.record_issue(args.issue, args.severity)
        print(f"⚠️  Recorded issue: {args.issue} ({args.severity})")
    
    if args.entry:
        memory.append_entry(args.entry, args.category)
        print(f"✅ Recorded entry in {args.category}")
    
    if not any([args.phase, args.decision, args.issue, args.entry]):
        # Show today's summary
        summary = memory.get_today_summary()
        if summary:
            print(summary)
        else:
            print("No memory entries for today yet.")

if __name__ == "__main__":
    main()
