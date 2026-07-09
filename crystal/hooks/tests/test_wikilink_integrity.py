# -*- coding: utf-8 -*-
"""
wikilink-integrity-guard.py 的 pytest 測試套件。

用 tmp_path 造假 workspace（wiki/、spec/、raw/ 等子目錄與 .md 檔），
呼叫 wikilink_integrity_guard.scan_workspace() 驗證行為，
並用 subprocess 驗證 CLI 層的 exit code 語意。
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "wikilink-integrity-guard.py"


def _load_guard_module():
    """檔名含連字號（wikilink-integrity-guard.py）無法直接 import，
    用 importlib 從檔案路徑動態載入模組。載入前先註冊進 sys.modules，
    避免 dataclasses 在 Python 3.14 上因模組不在 sys.modules 而查無
    __module__ 對應的 namespace（AttributeError: NoneType.__dict__）。"""
    spec = importlib.util.spec_from_file_location("wikilink_integrity_guard", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = _load_guard_module()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# 案例 1：乾淨通過 —— 所有連結都指到存在的檔案
# ---------------------------------------------------------------------------
def test_clean_workspace_passes(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "見 [[wiki/concept/bar]]")
    _write(tmp_path / "wiki" / "concept" / "bar.md", "回指 [[wiki/concept/foo]]")

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


# ---------------------------------------------------------------------------
# 案例 2：單一斷鏈 —— 連結指到不存在的檔案
# ---------------------------------------------------------------------------
def test_single_broken_link_detected(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "見 [[wiki/concept/missing]]")

    broken = guard.scan_workspace(tmp_path)

    assert len(broken) == 1
    assert broken[0].target == "wiki/concept/missing"
    assert broken[0].source_file.name == "foo.md"


# ---------------------------------------------------------------------------
# 案例 3：code fence 內的連結不應被當成斷鏈掃出（已知漏接：明確排除 fence）
# ---------------------------------------------------------------------------
def test_link_inside_code_fence_is_excluded(tmp_path):
    content = (
        "一般文字沒有連結。\n"
        "```\n"
        "範例語法：[[wiki/concept/does-not-exist]]\n"
        "```\n"
    )
    _write(tmp_path / "wiki" / "concept" / "foo.md", content)

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


# ---------------------------------------------------------------------------
# 案例 4：別名語法 [[a|b]] —— 應以 `|` 前的部分作為目標路徑
# ---------------------------------------------------------------------------
def test_alias_link_checks_target_before_pipe(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "見 [[wiki/concept/bar|顯示別名]]")
    _write(tmp_path / "wiki" / "concept" / "bar.md", "存在")

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


def test_alias_link_with_broken_target_before_pipe(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "見 [[wiki/concept/missing|顯示別名]]")

    broken = guard.scan_workspace(tmp_path)

    assert len(broken) == 1
    assert broken[0].target == "wiki/concept/missing"


# ---------------------------------------------------------------------------
# 案例 5：raw/ 前綴形式的連結 —— raw/ 檔案存在則通過
# ---------------------------------------------------------------------------
def test_raw_prefixed_link_resolves(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "證據見 [[raw/2026-07-08-source-type]]")
    _write(tmp_path / "raw" / "2026-07-08-source-type.md", "原始證據")

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


def test_raw_prefixed_link_broken(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "證據見 [[raw/2026-07-08-missing]]")

    broken = guard.scan_workspace(tmp_path)

    assert len(broken) == 1
    assert broken[0].target == "raw/2026-07-08-missing"


# ---------------------------------------------------------------------------
# 案例 6：repos/ 前綴形式的連結
# ---------------------------------------------------------------------------
def test_repos_prefixed_link_resolves(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "程式碼見 [[repos/app/main]]")
    _write(tmp_path / "repos" / "app" / "main.md", "程式碼筆記")

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


# ---------------------------------------------------------------------------
# 案例 7：.md 副檔名可省略也可明寫，兩者等價
# ---------------------------------------------------------------------------
def test_explicit_md_extension_also_resolves(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "見 [[wiki/concept/bar.md]]")
    _write(tmp_path / "wiki" / "concept" / "bar.md", "存在")

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


# ---------------------------------------------------------------------------
# 案例 8：spec/**/*.md 也在掃描範圍內（不只 wiki/）
# ---------------------------------------------------------------------------
def test_spec_directory_is_scanned(tmp_path):
    _write(tmp_path / "spec" / "module-a.md", "依賴 [[spec/module-b]]")

    broken = guard.scan_workspace(tmp_path)

    assert len(broken) == 1
    assert broken[0].target == "spec/module-b"


# ---------------------------------------------------------------------------
# 案例 9：多個斷鏈 —— 每條都要列出，順序穩定（依檔案再依出現順序）
# ---------------------------------------------------------------------------
def test_multiple_broken_links_all_reported(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "[[wiki/concept/a]] 和 [[wiki/concept/b]]")

    broken = guard.scan_workspace(tmp_path)

    assert len(broken) == 2
    targets = {item.target for item in broken}
    assert targets == {"wiki/concept/a", "wiki/concept/b"}


# ---------------------------------------------------------------------------
# 案例 10：非 wiki/spec 目錄下的 .md 檔不掃描（例如 raw/ 本身的內文連結不算）
# ---------------------------------------------------------------------------
def test_files_outside_wiki_and_spec_are_not_scanned(tmp_path):
    _write(tmp_path / "raw" / "2026-07-08-note.md", "隨手寫的 [[does/not/exist]] 不該被掃到")

    broken = guard.scan_workspace(tmp_path)

    assert broken == []


# ---------------------------------------------------------------------------
# CLI 層：exit code 語意
#
# 注意：一律用 encoding="utf-8" 明確指定子行程輸出解碼方式，不用
# text=True 的隱含 locale 預設編碼（Windows 上常是 cp950/cp936）。
# 腳本內已強制 stdout 用 UTF-8 輸出（見 wikilink-integrity-guard.py 的
# reconfigure 呼叫），呼叫端也要用相符編碼解碼，兩邊才不會兜不起來。
# ---------------------------------------------------------------------------
def test_cli_exit_code_2_on_broken_link(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "[[wiki/concept/missing]]")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 2
    assert "missing" in result.stdout


def test_cli_exit_code_0_on_clean_workspace(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "沒有連結的乾淨頁面")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 0


def test_cli_reports_source_file_and_target(tmp_path):
    _write(tmp_path / "wiki" / "concept" / "foo.md", "[[wiki/concept/missing]]")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    # 輸出格式要求：檔案 → 目標，逐條列出
    assert "foo.md" in result.stdout
    assert "wiki/concept/missing" in result.stdout


def test_cli_output_is_valid_utf8_regardless_of_console_codepage(tmp_path):
    """回歸測試：主控台預設編碼（如 Windows cp950/cp936）不應導致中文輸出
    無法以 UTF-8 解碼。這條鎖定腳本內的 stdout/stderr reconfigure 行為。"""
    _write(tmp_path / "wiki" / "concept" / "foo.md", "[[wiki/concept/missing]]")

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(tmp_path)],
        capture_output=True,
        text=False,  # 拿原始 bytes 自行以 utf-8 解碼，不吃系統預設編碼
    )

    decoded = result.stdout.decode("utf-8")  # 解碼失敗會直接 raise，等同斷言
    assert "斷鏈" in decoded
