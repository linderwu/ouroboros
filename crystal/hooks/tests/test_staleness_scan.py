# -*- coding: utf-8 -*-
"""
wiki-staleness-scan.py 的 pytest 測試套件。

用 tmp_path 造假 workspace（含 <!-- updated: --> / <!-- staleness: Nd --> 標籤的
.md 頁面），驗證 scan_workspace() 的保鮮判斷邏輯，並用 subprocess 驗證 CLI 層
在預設模式與 --strict 模式下的 exit code 語意。

所有測試對「今天」的判斷都以顯式傳入 today 參數控制（不依賴系統當下日期），
確保測試結果不隨執行日期漂移。
"""
import datetime
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "wiki-staleness-scan.py"


def _load_scan_module():
    """檔名含連字號（wiki-staleness-scan.py）無法直接 import，
    用 importlib 從檔案路徑動態載入模組，並註冊進 sys.modules
    （避免 dataclasses 在新版 Python 上因模組不在 sys.modules 而出錯）。"""
    spec = importlib.util.spec_from_file_location("wiki_staleness_scan", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


scan = _load_scan_module()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# 固定「今天」以求測試決定性，不受實際執行日期影響
TODAY = datetime.date(2026, 7, 9)


# ---------------------------------------------------------------------------
# 案例 1：未超期 —— updated 距今天數 <= staleness，不列入警告
# ---------------------------------------------------------------------------
def test_fresh_page_not_flagged(tmp_path):
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 2026-06-20 -->\n<!-- staleness: 60d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert result.stale == []


# ---------------------------------------------------------------------------
# 案例 2：超期 —— updated 距今天數 > staleness，列入 ⚠️ 警告清單
# ---------------------------------------------------------------------------
def test_stale_page_is_flagged(tmp_path):
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 2026-01-01 -->\n<!-- staleness: 30d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert len(result.stale) == 1
    assert result.stale[0].file.name == "foo.md"
    assert result.stale[0].updated == datetime.date(2026, 1, 1)
    assert result.stale[0].staleness_days == 30


# ---------------------------------------------------------------------------
# 案例 3：邊界值 —— 剛好等於 staleness 天數不算超期（> 才算，= 不算）
# ---------------------------------------------------------------------------
def test_exactly_at_staleness_boundary_not_flagged(tmp_path):
    # TODAY = 2026-07-09；updated 往前推 30 天整 = 2026-06-09，差距剛好 30 天
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 2026-06-09 -->\n<!-- staleness: 30d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert result.stale == []


def test_one_day_past_staleness_boundary_flagged(tmp_path):
    # 差距 31 天 > 30 天 staleness，應超期
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 2026-06-08 -->\n<!-- staleness: 30d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert len(result.stale) == 1


# ---------------------------------------------------------------------------
# 案例 4：缺標籤 —— 完全沒有 updated/staleness 標籤的頁面，列入「無標籤」清單
# ---------------------------------------------------------------------------
def test_page_without_tags_listed_as_no_tags(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "完全沒有保鮮標籤的頁面內容")

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert result.stale == []
    assert len(result.no_tags) == 1
    assert result.no_tags[0].name == "foo.md"


def test_page_with_only_updated_tag_listed_as_no_tags(tmp_path):
    # 只有 updated 沒有 staleness，視為標籤不完整 → 無標籤清單
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 2026-01-01 -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert len(result.no_tags) == 1


# ---------------------------------------------------------------------------
# 案例 5：壞日期格式 —— 非 ISO 格式的日期，跳過並列出（已知漏接）
# ---------------------------------------------------------------------------
def test_non_iso_date_format_listed_as_bad_date(tmp_path):
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 2026/07/09 -->\n<!-- staleness: 30d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert result.stale == []
    assert len(result.bad_dates) == 1
    assert result.bad_dates[0].file.name == "foo.md"


def test_another_non_iso_date_format_listed_as_bad_date(tmp_path):
    _write(
        tmp_path / "wiki" / "concept" / "foo.md",
        "<!-- updated: 09-Jul-2026 -->\n<!-- staleness: 30d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert len(result.bad_dates) == 1


# ---------------------------------------------------------------------------
# 案例 6：多頁面混合情境 —— 超期＋未超期＋無標籤＋壞日期同時出現，各自歸類正確
# ---------------------------------------------------------------------------
def test_mixed_workspace_categorizes_each_page_correctly(tmp_path):
    _write(
        tmp_path / "wiki" / "a.md",
        "<!-- updated: 2026-01-01 -->\n<!-- staleness: 30d -->\n超期頁",
    )
    _write(
        tmp_path / "wiki" / "b.md",
        "<!-- updated: 2026-07-01 -->\n<!-- staleness: 30d -->\n未超期頁",
    )
    _write(tmp_path / "wiki" / "c.md", "無標籤頁")
    _write(
        tmp_path / "wiki" / "d.md",
        "<!-- updated: not-a-date -->\n<!-- staleness: 30d -->\n壞日期頁",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert len(result.stale) == 1
    assert result.stale[0].file.name == "a.md"
    assert len(result.no_tags) == 1
    assert result.no_tags[0].name == "c.md"
    assert len(result.bad_dates) == 1
    assert result.bad_dates[0].file.name == "d.md"


# ---------------------------------------------------------------------------
# 案例 7：spec/ 目錄也在掃描範圍（不只 wiki/）
# ---------------------------------------------------------------------------
def test_spec_directory_is_scanned(tmp_path):
    _write(
        tmp_path / "spec" / "module-a.md",
        "<!-- updated: 2026-01-01 -->\n<!-- staleness: 30d -->\n內容",
    )

    result = scan.scan_workspace(tmp_path, today=TODAY)

    assert len(result.stale) == 1


# ---------------------------------------------------------------------------
# CLI 層：預設模式（提醒不阻擋）與 --strict 模式的 exit code 語意
# ---------------------------------------------------------------------------
def test_cli_default_exit_0_even_with_stale_pages(tmp_path):
    _write(
        tmp_path / "wiki" / "a.md",
        "<!-- updated: 2020-01-01 -->\n<!-- staleness: 30d -->\n超期頁",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0
    assert "a.md" in result.stdout  # 仍應提醒列出


def test_cli_strict_exit_1_with_stale_pages(tmp_path):
    _write(
        tmp_path / "wiki" / "a.md",
        "<!-- updated: 2020-01-01 -->\n<!-- staleness: 30d -->\n超期頁",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path), "--strict"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1


def test_cli_strict_exit_0_when_nothing_stale(tmp_path):
    _write(
        tmp_path / "wiki" / "a.md",
        f"<!-- updated: {TODAY.isoformat()} -->\n<!-- staleness: 30d -->\n新鮮頁",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path), "--strict"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0


def test_cli_no_tags_alone_does_not_trigger_strict_failure(tmp_path):
    # 缺標籤跟「超期」是不同類別；--strict 只因「超期」而失敗，缺標籤不算超期
    _write(tmp_path / "wiki" / "a.md", "無標籤頁")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path), "--strict"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0
    assert "a.md" in result.stdout
