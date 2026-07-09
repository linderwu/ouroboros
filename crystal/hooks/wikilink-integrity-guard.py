#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wikilink-integrity-guard.py

用途：
    掃描 workspace 下 wiki/**/*.md 與 spec/**/*.md 內的 [[target]] wikilink（含
    [[raw/...]]、[[repos/...]] 前綴形式與 [[a|b]] 別名語法），驗證每個連結指向
    的目標檔案是否存在（.md 副檔名可省略）。這是「存在性核驗」的機械層——只確認
    連結沒有斷鏈，不判斷引用內容是否支持頁面主張（來源性核驗需人審）。

用法：
    python wikilink-integrity-guard.py <workspace-root>

掛載建議：
    standalone CLI 檢查器，非 PreToolUse 攔截器。可掛：
      - pre-commit hook（commit 前擋斷鏈頁面進庫）
      - CI step（PR 檢查，於 wiki/spec 變更時跑）
      - PR 檢查腳本（人工觸發，merge 前手動執行一次）
    任一種掛法皆可，依專案 CI 現況選擇；本腳本不假設特定掛載環境。

exit code 語意：
    0 = 全部連結存在，通過
    2 = 發現斷鏈，逐條列出「檔案 → 目標」後中斷

已知漏接（誠實標注，非窮舉防禦）：
    1. code fence（``` 包裹區塊）內的文字不會被掃描——本腳本明確排除 fence 內容，
       視為「範例語法示範」而非真實連結；若未來需要連 fence 內都要求無斷鏈，
       這條需要重新設計。
    2. 別名語法 [[a|b]] 只驗證 `|` 之前的目標路徑，`|` 之後的顯示文字不做任何檢查
       （包含顯示文字本身若誤寫成另一個 wikilink 語法也不會被二次解析）。
    3. 只認得 [[...]] 語法本體；Markdown 一般連結 [text](path) 不在掃描範圍內，
       即使該連結實際上也指向 wiki/spec 內部頁面。
    4. 目標路徑一律以 workspace-root 為基準做相對路徑解析；不支援以來源檔案自身
       目錄為基準的相對路徑（例如 [[../sibling]] 這種上層目錄語法不保證正確解析）。
    5. 不驗證目標檔案「內容」有效（例如目標是空檔案、或已被標記 status: superseded），
       只驗證檔案本身存在於檔案系統上。
    6. stdout/stderr 的 UTF-8 強制輸出靠 io.TextIOWrapper.reconfigure()（Python 3.7+
       才有這個方法）；若在極舊版 Python（< 3.7）執行，會靜默略過強制轉碼，此時
       中文輸出的實際編碼將回退成主控台預設編碼（例如 Windows cp950/cp936），可能
       出現亂碼。本腳本已假設執行環境 ≥ Python 3.7。
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

# 掃描的子目錄（相對於 workspace-root）
SCAN_DIRS = ("wiki", "spec")

# 比對 [[target]] 或 [[target|display]] 的 wikilink 語法
# target 不含 `]`、`[`、`|`，避免跨連結誤吃
WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]|]+)(?:\|[^\[\]]*)?\]\]")

# 比對 ``` 或 ~~~ 圍住的 code fence 區塊（含語言標記行），用來排除 fence 內容
CODE_FENCE_PATTERN = re.compile(r"^(```|~~~)", re.MULTILINE)


@dataclass(frozen=True)
class BrokenLink:
    """代表一條斷鏈：來源檔案與斷掉的目標路徑（未解析副檔名前的原始字串）。"""

    source_file: Path
    target: str


def _strip_code_fences(text: str) -> str:
    """把 code fence（```...``` 或 ~~~...~~~）區塊內容替換成空白，
    保留行數與其餘文字不變，避免 fence 內的示範連結被誤判為真連結。"""
    lines = text.split("\n")
    result_lines: List[str] = []
    in_fence = False
    fence_marker = None
    for line in lines:
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = True
            fence_marker = stripped[:3]
            result_lines.append("")  # 圍籬行本身也清空（避免圍籬行誤含 [[ ]]）
            continue
        if in_fence:
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
                result_lines.append("")
            else:
                result_lines.append("")
            continue
        result_lines.append(line)
    return "\n".join(result_lines)


def _resolve_target(workspace_root: Path, target: str) -> bool:
    """判斷 target（例如 'wiki/concept/foo' 或 'raw/2026-07-08-x.md'）
    相對 workspace_root 是否存在對應檔案。.md 副檔名可省略。"""
    target = target.strip()
    candidate = workspace_root / target
    if candidate.exists() and candidate.is_file():
        return True
    if not target.endswith(".md"):
        candidate_with_md = workspace_root / f"{target}.md"
        if candidate_with_md.exists() and candidate_with_md.is_file():
            return True
    return False


def _iter_markdown_files(workspace_root: Path) -> List[Path]:
    """列出 wiki/ 與 spec/ 底下所有 .md 檔案（遞迴子目錄），排序以求輸出穩定。"""
    files: List[Path] = []
    for dir_name in SCAN_DIRS:
        base = workspace_root / dir_name
        if not base.is_dir():
            continue
        files.extend(sorted(base.rglob("*.md")))
    return files


def scan_workspace(workspace_root: Path) -> List[BrokenLink]:
    """掃描 workspace_root 下 wiki/**/*.md 與 spec/**/*.md，回傳所有斷鏈清單。
    清單順序：先依檔案（sorted），再依連結於檔案內出現的順序。"""
    broken: List[BrokenLink] = []
    for md_file in _iter_markdown_files(workspace_root):
        raw_text = md_file.read_text(encoding="utf-8")
        scan_text = _strip_code_fences(raw_text)
        for match in WIKILINK_PATTERN.finditer(scan_text):
            target = match.group(1).strip()
            if not target:
                continue
            if not _resolve_target(workspace_root, target):
                broken.append(BrokenLink(source_file=md_file, target=target))
    return broken


def _format_report(broken: List[BrokenLink], workspace_root: Path) -> str:
    lines = [f"發現 {len(broken)} 條斷鏈 wikilink：", ""]
    for item in broken:
        try:
            rel = item.source_file.relative_to(workspace_root)
        except ValueError:
            rel = item.source_file
        lines.append(f"  {rel} → [[{item.target}]]")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    # 訊息含繁體中文，強制 stdout/stderr 用 UTF-8，避免主控台編碼（例如 Windows
    # 預設 cp950/cp936）造成輸出亂碼或跨平台不一致；Python < 3.7 無 reconfigure
    # 屬已知漏接，見檔首「已知漏接」第 6 點。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    if len(argv) != 2:
        print("用法：python wikilink-integrity-guard.py <workspace-root>", file=sys.stderr)
        return 2

    workspace_root = Path(argv[1]).resolve()
    if not workspace_root.is_dir():
        print(f"錯誤：workspace-root 不是有效目錄：{workspace_root}", file=sys.stderr)
        return 2

    broken = scan_workspace(workspace_root)

    if broken:
        print(_format_report(broken, workspace_root))
        return 2

    print("wikilink 完整性檢查通過：0 條斷鏈。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
