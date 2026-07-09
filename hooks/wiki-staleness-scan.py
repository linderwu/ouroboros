#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wiki-staleness-scan.py

用途：
    掃描 workspace 下 wiki/**/*.md 與 spec/**/*.md 頁面內的保鮮標籤
    `<!-- updated: YYYY-MM-DD -->` 與 `<!-- staleness: Nd -->`，計算
    「今天 - updated > staleness」的頁面並列成 ⚠️ 超期清單。這是提醒機制，
    不是內容正確性驗證——標籤過期只代表「該回頭確認是否仍然有效」，不代表
    內容已經錯誤。

用法：
    python wiki-staleness-scan.py <workspace-root> [--strict]

掛載建議：
    standalone CLI 檢查器，非 PreToolUse 攔截器。可掛：
      - CI step（定期排程跑一次，出報告不擋 PR；若要擋 PR 才用 --strict）
      - pre-commit hook（--strict 模式，防止已知超期頁面被夾帶進新 commit
        而未被注意到；一般開發流程建議不掛 --strict，避免每次 commit 都卡關）
      - PR 檢查腳本（人工觸發，複審 wiki/spec 健康度時跑一次）
    預設模式（不含 --strict）就是提醒用途，適合排程或人工執行；--strict
    才具備阻擋能力，掛進強制流程前請先確認團隊能接受它擋 commit/PR。

exit code 語意：
    預設（不含 --strict）：一律 exit 0，只列出提醒清單，不阻擋。
    --strict 且發現至少一頁超期：exit 1。
    --strict 但無任何超期頁面（即使有缺標籤或壞日期頁面）：exit 0。

已知漏接（誠實標注，非窮舉防禦）：
    1. 日期格式非 ISO 8601（YYYY-MM-DD）者一律跳過並列入「壞日期」清單，
       不嘗試猜測其他格式（例如 2026/07/09、09-Jul-2026 都會被跳過）。
    2. 只認得 `updated` 與 `staleness` 兩個標籤名稱，且要求兩者同時存在才
       納入超期判斷；只有其中一個標籤的頁面一律歸類為「無標籤」（標籤不完整
       等同沒有標籤，不做部分判斷）。
    3. staleness 格式只認得 `<整數>d`（例如 30d、60d）；若寫成其他單位
       （例如 4w、2m）或缺少 `d` 後綴，會被當成缺標籤頁面處理，不會嘗試
       換算單位。
    4. 標籤必須各自獨立成一行 HTML 註解（`<!-- updated: ... -->`），不支援
       同一行塞兩個標籤或標籤被包在其他 HTML 註解內的巢狀寫法。
    5. 不驗證 staleness 天數本身是否「合理」（例如寫 99999d 這種近乎永不
       過期的值），只單純做數字比較。
    6. stdout/stderr 的 UTF-8 強制輸出靠 io.TextIOWrapper.reconfigure()
       （Python 3.7+ 才有）；極舊版 Python 會靜默略過，回退主控台預設編碼。
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# 掃描的子目錄（相對於 workspace-root），與 wikilink-integrity-guard.py 一致
SCAN_DIRS = ("wiki", "spec")

UPDATED_TAG_PATTERN = re.compile(r"<!--\s*updated:\s*(.+?)\s*-->")
STALENESS_TAG_PATTERN = re.compile(r"<!--\s*staleness:\s*(\d+)d\s*-->")

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class StalePage:
    """代表一個已超期的頁面：檔案、其 updated 日期、staleness 門檻天數、實際差距天數。"""

    file: Path
    updated: datetime.date
    staleness_days: int
    days_since_update: int


@dataclass(frozen=True)
class BadDatePage:
    """代表一個 updated 標籤存在但日期格式無法解析（非 ISO 8601）的頁面。"""

    file: Path
    raw_value: str


@dataclass
class ScanResult:
    """一次掃描的完整分類結果。"""

    stale: List[StalePage] = field(default_factory=list)
    no_tags: List[Path] = field(default_factory=list)
    bad_dates: List[BadDatePage] = field(default_factory=list)


def _iter_markdown_files(workspace_root: Path) -> List[Path]:
    """列出 wiki/ 與 spec/ 底下所有 .md 檔案（遞迴子目錄），排序以求輸出穩定。"""
    files: List[Path] = []
    for dir_name in SCAN_DIRS:
        base = workspace_root / dir_name
        if not base.is_dir():
            continue
        files.extend(sorted(base.rglob("*.md")))
    return files


def _parse_iso_date(raw_value: str) -> Optional[datetime.date]:
    """把字串解析成 date；非 ISO 8601（YYYY-MM-DD）格式一律回傳 None
    （呼叫端據此歸類為壞日期，不嘗試猜測其他格式——見檔首已知漏接第 1 點）。"""
    if not ISO_DATE_PATTERN.match(raw_value):
        return None
    try:
        return datetime.date.fromisoformat(raw_value)
    except ValueError:
        return None


def _classify_page(md_file: Path, text: str, today: datetime.date) -> tuple:
    """回傳 ('stale', StalePage) / ('no_tags', None) / ('bad_date', BadDatePage) / ('fresh', None) 之一。"""
    updated_match = UPDATED_TAG_PATTERN.search(text)
    staleness_match = STALENESS_TAG_PATTERN.search(text)

    if not updated_match or not staleness_match:
        return ("no_tags", None)

    raw_date = updated_match.group(1).strip()
    parsed_date = _parse_iso_date(raw_date)
    if parsed_date is None:
        return ("bad_date", BadDatePage(file=md_file, raw_value=raw_date))

    staleness_days = int(staleness_match.group(1))
    days_since_update = (today - parsed_date).days

    if days_since_update > staleness_days:
        return (
            "stale",
            StalePage(
                file=md_file,
                updated=parsed_date,
                staleness_days=staleness_days,
                days_since_update=days_since_update,
            ),
        )
    return ("fresh", None)


def scan_workspace(workspace_root: Path, today: Optional[datetime.date] = None) -> ScanResult:
    """掃描 workspace_root 下 wiki/**/*.md 與 spec/**/*.md，依保鮮標籤分類。
    today 未提供時使用系統當下日期（CLI 呼叫走這條路；測試一律顯式傳入 today
    以求結果決定性，不隨執行日期漂移）。"""
    if today is None:
        today = datetime.date.today()

    result = ScanResult()
    for md_file in _iter_markdown_files(workspace_root):
        text = md_file.read_text(encoding="utf-8")
        kind, payload = _classify_page(md_file, text, today)
        if kind == "stale":
            result.stale.append(payload)
        elif kind == "no_tags":
            result.no_tags.append(md_file)
        elif kind == "bad_date":
            result.bad_dates.append(payload)
        # kind == "fresh"：不列入任何清單
    return result


def _relative(path: Path, workspace_root: Path) -> Path:
    try:
        return path.relative_to(workspace_root)
    except ValueError:
        return path


def _format_report(result: ScanResult, workspace_root: Path) -> str:
    lines: List[str] = []

    if result.stale:
        lines.append(f"⚠️ 超期頁面（{len(result.stale)} 筆）：")
        for item in result.stale:
            rel = _relative(item.file, workspace_root)
            lines.append(
                f"  {rel} → updated: {item.updated.isoformat()}, "
                f"staleness: {item.staleness_days}d, "
                f"已過 {item.days_since_update} 天"
            )
        lines.append("")
    else:
        lines.append("⚠️ 超期頁面：0 筆。")
        lines.append("")

    if result.no_tags:
        lines.append(f"無標籤頁面（{len(result.no_tags)} 筆，未納入保鮮判斷）：")
        for path in result.no_tags:
            rel = _relative(path, workspace_root)
            lines.append(f"  {rel}")
        lines.append("")

    if result.bad_dates:
        lines.append(f"壞日期格式頁面（{len(result.bad_dates)} 筆，已跳過保鮮判斷）：")
        for item in result.bad_dates:
            rel = _relative(item.file, workspace_root)
            lines.append(f"  {rel} → updated 原始值：{item.raw_value!r}")
        lines.append("")

    return "\n".join(lines).rstrip("\n")


def main(argv: List[str]) -> int:
    # 訊息含繁體中文與 emoji，強制 stdout/stderr 用 UTF-8，避免主控台編碼
    # （例如 Windows 預設 cp950/cp936）造成輸出亂碼或跨平台不一致。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="wiki-staleness-scan.py",
        description="掃描 wiki/spec 頁面保鮮標籤，列出超期清單（預設僅提醒，--strict 才阻擋）。",
    )
    parser.add_argument("workspace_root", help="workspace 根目錄路徑")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="有超期頁面時以 exit 1 阻擋（預設不阻擋，只提醒）",
    )
    args = parser.parse_args(argv[1:])

    workspace_root = Path(args.workspace_root).resolve()
    if not workspace_root.is_dir():
        print(f"錯誤：workspace-root 不是有效目錄：{workspace_root}", file=sys.stderr)
        return 2

    result = scan_workspace(workspace_root)
    print(_format_report(result, workspace_root))

    if args.strict and result.stale:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
