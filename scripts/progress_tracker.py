#!/usr/bin/env python3
"""
Ouroboros Progress Tracker
Phase 6: Working Memory Integration

追蹤 Ouroboros 執行進度、決策、審計日誌。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# === Config ===
SKILL_DIR = Path(__file__).parent.parent
WORKSPACE_DIR = Path(os.environ.get("OUROBOROS_WORKSPACE_DIR", SKILL_DIR.parent.parent))
PROGRESS_DIR = WORKSPACE_DIR / ".ouroboros"
PROGRESS_FILE = PROGRESS_DIR / "progress.json"
AUDIT_FILE = PROGRESS_DIR / "audit_log.jsonl"

# === Progress Tracker ===
class ProgressTracker:
    def __init__(self, progress_dir: Path = PROGRESS_DIR):
        self.progress_dir = progress_dir
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file = progress_dir / "progress.json"
        self._init()
    
    def _init(self):
        """初始化追蹤檔"""
        if not self.progress_file.exists():
            self._write({
                "version": "2.8",
                "phases": {},
                "decisions": [],
                "current_phase": None,
                "started_at": datetime.now().isoformat()
            })
    
    def _read(self) -> dict:
        """讀取進度"""
        if self.progress_file.exists():
            return json.loads(self.progress_file.read_text(encoding="utf-8"))
        return {}
    
    def _write(self, data: dict):
        """寫入進度"""
        self.progress_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    def start_phase(self, phase: str):
        """標記 Phase 開始"""
        progress = self._read()
        progress["current_phase"] = phase
        
        if "phases" not in progress:
            progress["phases"] = {}
        
        progress["phases"][phase] = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat()
        }
        
        self._write(progress)
        self._audit_log("phase_started", {"phase": phase})
    
    def complete_phase(self, phase: str, results: dict = None):
        """標記 Phase 完成"""
        progress = self._read()
        
        if phase in progress.get("phases", {}):
            progress["phases"][phase]["status"] = "completed"
            progress["phases"][phase]["completed_at"] = datetime.now().isoformat()
            if results:
                progress["phases"][phase]["results"] = results
        
        if progress.get("current_phase") == phase:
            progress["current_phase"] = None
        
        self._write(progress)
        self._audit_log("phase_completed", {"phase": phase, "results": results})
    
    def fail_phase(self, phase: str, error: str):
        """標記 Phase 失敗"""
        progress = self._read()
        
        if phase in progress.get("phases", {}):
            progress["phases"][phase]["status"] = "failed"
            progress["phases"][phase]["failed_at"] = datetime.now().isoformat()
            progress["phases"][phase]["error"] = error
        
        self._write(progress)
        self._audit_log("phase_failed", {"phase": phase, "error": error})
    
    def add_decision(self, decision: str, reason: str, impact: str = None):
        """新增決策記錄"""
        progress = self._read()
        
        if "decisions" not in progress:
            progress["decisions"] = []
        
        progress["decisions"].append({
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reason": reason,
            "impact": impact
        })
        
        self._write(progress)
        self._audit_log("decision_made", {
            "decision": decision,
            "reason": reason,
            "impact": impact
        })
    
    def get_phase_status(self, phase: str) -> Optional[dict]:
        """取得 Phase 狀態"""
        progress = self._read()
        return progress.get("phases", {}).get(phase)
    
    def get_all_phases(self) -> dict:
        """取得所有 Phase 狀態"""
        progress = self._read()
        return progress.get("phases", {})
    
    def get_current_phase(self) -> Optional[str]:
        """取得當前進行的 Phase"""
        progress = self._read()
        return progress.get("current_phase")
    
    def get_summary(self) -> str:
        """取得進度摘要"""
        progress = self._read()
        phases = progress.get("phases", {})
        
        lines = ["## Ouroboros Progress\n"]
        lines.append(f"Version: {progress.get('version', 'unknown')}\n")
        lines.append(f"Started: {progress.get('started_at', 'N/A')}\n")
        lines.append("")
        
        completed = sum(1 for p in phases.values() if p.get("status") == "completed")
        in_progress = sum(1 for p in phases.values() if p.get("status") == "in_progress")
        failed = sum(1 for p in phases.values() if p.get("status") == "failed")
        
        lines.append(f"**Completed**: {completed}")
        lines.append(f"**In Progress**: {in_progress}")
        lines.append(f"**Failed**: {failed}\n")
        
        lines.append("### Phases\n")
        for phase, info in phases.items():
            status = info.get("status", "unknown")
            emoji = "✅" if status == "completed" else "🔄" if status == "in_progress" else "❌" if status == "failed" else "⏳"
            started = info.get("started_at", "")[:10] if info.get("started_at") else ""
            lines.append(f"{emoji} {phase}: {status} (started: {started})")
        
        lines.append("\n### Recent Decisions\n")
        for dec in progress.get("decisions", [])[-5:]:
            lines.append(f"- **{dec['decision']}**: {dec.get('reason', 'N/A')[:50]}...")
        
        return "\n".join(lines)
    
    def _audit_log(self, event: str, data: dict):
        """寫入審計日誌"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **data
        }
        
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_audit_log(self, limit: int = 50) -> List[dict]:
        """讀取審計日誌"""
        if not AUDIT_FILE.exists():
            return []
        
        entries = []
        with open(AUDIT_FILE, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        return entries[-limit:]

# === CLI ===
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Ouroboros Progress Tracker")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start phase
    start_parser = subparsers.add_parser("start", help="Start a phase")
    start_parser.add_argument("phase", help="Phase name")
    
    # Complete phase
    complete_parser = subparsers.add_parser("complete", help="Complete a phase")
    complete_parser.add_argument("phase", help="Phase name")
    complete_parser.add_argument("--results", help="Results as JSON string")
    
    # Fail phase
    fail_parser = subparsers.add_parser("fail", help="Mark phase as failed")
    fail_parser.add_argument("phase", help="Phase name")
    fail_parser.add_argument("--error", required=True, help="Error message")
    
    # Add decision
    decision_parser = subparsers.add_parser("decision", help="Add a decision")
    decision_parser.add_argument("--decision", required=True, help="Decision text")
    decision_parser.add_argument("--reason", required=True, help="Reason")
    decision_parser.add_argument("--impact", help="Impact")
    
    # Show status
    status_parser = subparsers.add_parser("status", help="Show progress status")
    
    # Show audit
    audit_parser = subparsers.add_parser("audit", help="Show audit log")
    audit_parser.add_argument("--limit", type=int, default=20, help="Number of entries")
    
    args = parser.parse_args()
    
    tracker = ProgressTracker()
    
    if args.command == "start":
        tracker.start_phase(args.phase)
        print(f"🔄 Started phase: {args.phase}")
    
    elif args.command == "complete":
        results = None
        if args.results:
            results = json.loads(args.results)
        tracker.complete_phase(args.phase, results)
        print(f"✅ Completed phase: {args.phase}")
    
    elif args.command == "fail":
        tracker.fail_phase(args.phase, args.error)
        print(f"❌ Failed phase: {args.phase} — {args.error}")
    
    elif args.command == "decision":
        tracker.add_decision(args.decision, args.reason, args.impact)
        print(f"✅ Recorded decision: {args.decision}")
    
    elif args.command == "status":
        print(tracker.get_summary())
    
    elif args.command == "audit":
        entries = tracker.get_audit_log(limit=args.limit)
        for entry in entries:
            print(f"[{entry['timestamp'][:19]}] {entry['event']}: {entry}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
