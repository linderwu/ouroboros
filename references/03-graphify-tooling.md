# 03 · 依賴圖工具（Phase 3）

> **本檔對應**：SKILL.md Phase 3（依賴圖）。
> **沿原作**：graphify 與依賴圖索引工具的用途分工、「code 變動重跑 graphify」的再生成規則沿原作。
> **安裝紀律**：一律版本釘選＋官方 release 簽章/checksum 驗證。**不採用「把遠端安裝腳本以管線直接餵進 shell 執行」這種未校驗直管的安裝方式。**

---

## 1. graphify/ 是什麼

graphify/ 是四層裡唯一非人工維護的部分：由外部工具掃 repos/ 產出 **function-level 依賴圖**（call graph、跨實體關係），輸出如 `graph.json`、`GRAPH_REPORT.md`，供 agent 讀取。人不手改 graphify/，改的是 code，然後重跑工具再生成。

## 2. 兩類工具的用途分工

依 Phase 0 規模決策選工具（規模判準見 `01-size-assessment.md` §3）：

| 工具類別 | 用途 | 用在哪個規模 |
|---|---|---|
| **graphify（依賴圖生成器）** | 對指定模組/整 repo 產 function-level 依賴圖 | M：只對 hub 模組局部跑；L：全 repo 跑 |
| **依賴圖索引工具（codebase-memory 類 MCP）** | 對大型 repo 建可查詢索引（find_dependents 等），省 token 探索 | L：標配；M：視需要 |

- **S**：兩者都不用，LLM 直讀。
- **M**：graphify 局部（hub/跨界介面/外部依賴密集處），索引工具視情況。
- **L**：graphify 全套 + 索引工具建全 repo 索引。

> 註：graphify（PyPI 上發佈名為 `graphifyy`）與依賴圖索引 MCP（如 `codebase-memory-mcp`）皆為**外部公開專案**，不隨本包發佈。本包只規定「如何呼叫與如何安全安裝」，不代管其版本或內容。

## 3. code 變動重跑 graphify（再生成規則）

graphify/ 的維護方式是**再生成、非累積式手改**：

- 只要 repos/ 的程式碼有實質變動（改了依賴、加/刪 function、動了模組邊界），就重跑 graphify 覆蓋舊輸出。
- 不要手動編輯 `graph.json` 或報告去「補上」新關係——那會讓依賴圖與 code 漂移。
- 這是 Phase 5 稽核的一部分：稽核時檢查「上次 graphify 之後 code 有沒有動過」，有就重跑。

## 4. 安裝紀律（版本釘選 + 官方簽章/checksum 驗證）

**禁止**：把遠端安裝腳本以管線直接餵進 shell 執行（下載即執行、中間不落地檢視的那類做法）——來源未校驗、內容可被中間人替換，且看不到將執行什麼。

**要求**：釘選版本號、下載官方 release、比對官方公佈的 checksum 或驗證簽章後才安裝。下列為指令樣板，`<VERSION>`／`<EXPECTED_SHA256>` 以官方 release 頁公佈值替換：

```bash
# 樣板一：Python 工具（版本釘選安裝）
# 釘死版本，不裝浮動最新版
uv tool install "graphifyy==<VERSION>"
# 或 pip：pip install "graphifyy==<VERSION>"

# 樣板二：下載式 binary/script（先驗 checksum 再執行，不直管）
VERSION="<VERSION>"
EXPECTED_SHA256="<EXPECTED_SHA256>"   # 取自官方 release 頁
# 1) 先下載到本地檔（不 pipe 進 shell）
curl -fsSL -o installer.sh \
  "https://<official-release-host>/download/${VERSION}/installer.sh"
# 2) 比對 checksum，不符就中止
echo "${EXPECTED_SHA256}  installer.sh" | sha256sum -c - || {
  echo "checksum 不符，中止安裝"; exit 1;
}
# 3) 人工檢視內容後才執行
less installer.sh   # 先看再跑
bash installer.sh
```

若工具提供 GPG 簽章，改用簽章驗證（`gpg --verify installer.sh.asc installer.sh`）取代或疊加 checksum 比對。**沒有可驗證的簽章或 checksum 時，視為不可信來源，不安裝。**

## 5. Phase 3 產出檢查

- 工具版本已釘選（記下實際版本號，供重現）。
- 安裝經 checksum/簽章驗證通過（保留驗證輸出）。
- graphify 輸出對應的是「當前 code 狀態」（跑之後 code 未再變動；有變動需重跑）。
- 規模對應：S 無 graphify/ 產物是正常；M/L 有對應範圍的產物。
