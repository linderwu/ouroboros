# ouroboros（crystal 入籍版）

## 這是什麼

把**單一 repo** 消化成四層可審計知識庫的萃取管線：`raw/`（唯一證據層，append-only）、`graphify/`（工具生成的依賴圖）、`wiki/`（curated 決策與程序架構）、`spec/`（從 code 萃取的模組現況契約）。適用於接手陌生 codebase 要建知識庫、追問「為什麼這樣設計」、或多個 agent 反覆重讀同一批 code 在浪費 context 的場景；小專案（<5 檔）不適用，LLM 直讀即可。本包移植自外部作品 ouroboros（roaringmoon 著，Trivium v2.7），改寫範圍與逐項對照見 `references/00-readme.md`。

## 包結構

```
ouroboros-crystal/
├── SKILL.md                 # ≤120 行骨架：四層定位 / 六 Phase / Question Routing / 鐵律 / 指回清單
├── README.md                # 本檔
├── references/
│   ├── 00-readme.md         # 導讀 + 原版出處 + 改寫範圍聲明（沿用 vs 標準化新增）
│   ├── 01-size-assessment.md   # Phase 0：S/M/L 判準與工具決策
│   ├── 02-evidence-and-code.md # Phase 1–2：raw/ 證據 + provenance + repos/
│   ├── 03-graphify-tooling.md  # Phase 3：依賴圖工具與安全安裝
│   ├── 04-wiki-curation.md     # Phase 4：wiki 四型頁 / 否證關 / 兩層核驗
│   ├── 05-spec-bridge.md       # Phase 4：spec 契約 / visibility / 對齊對照表
│   └── 06-design-rationale-inquiry.md # 「為什麼這樣設計」追問流程
└── hooks/                   # 強制力腳本（由另一負責人維護）
    ├── wikilink-integrity-guard.py
    ├── wiki-staleness-scan.py
    └── tests/
```

## 與原版差異總表

| 面向 | 差異 |
|---|---|
| **結構重組** | 原作機制集中在單一 SKILL.md；本包拆成 ≤120 行骨架 + references 七檔，深度細節下放 |
| **強制力腳本化** | 原作把斷鏈/過時檢查寫成文字規範（未附可執行腳本）；本包落成 `hooks/` 可執行檢查器，強制力改由 exit-code 承擔 |
| **去重指回** | 熵管理/需求 SPEC/否證關等一律指回姊妹 skill，只寫介面、不重寫其機制內文 |
| **標準化新增** | 四處：raw/ provenance 欄、wiki 全型別 status 生命週期、spec visibility 欄、設計理由追問流程（皆在對應 references 明標非原作） |
| **範圍收斂** | 砍掉跨 repo 支援與跨 repo 合併輸出、語義檢索承諾——收斂到單一 repo、召回走規則路由 |

## 協作對接

本包只裝「單一 repo → 四層知識庫」的萃取管線。下列能力由**姊妹 skill** 承擔，本包**僅以名稱與介面一句話銜接、不含其任何機制內文**：

- **索引式 memory skill**：提供保鮮標籤（`<!-- updated -->` / `<!-- staleness -->`）與索引/路由的語意慣例；本包 wiki 保鮮標籤遵其格式。
- **spec 生產鏈 skill**：負責「人寫的需求 SPEC」之起草與 gate；本包只萃取 code 現況契約，需求 SPEC 交其產與審。
- **對抗式 QE skill**：提供 wiki concept 主張的否證關（起草者≠審查者、finding 過否證才計分）；本包 wiki 入庫遵其否證流程。
- **黑箱測試 skill**：定義對外行為白名單/黑名單邊界；本包 spec `visibility: external` 供其機械抽取白名單。

> 聲明：本包不含上述任何 skill 的內容，僅以介面銜接。各能力的實作與流程以其本體 skill 為單一事實來源，本包不複製、不另訂。

## hooks 部署與部署驗收

hooks/ 兩支為 standalone CLI 檢查器（`python3 <script> <workspace-root>`），由另一負責人維護。掛載方式與已知漏接見各腳本檔首註解。

**部署驗收——先注入已知故障驗證器（裝上不等於有效）**：

```bash
# 1) wikilink 完整性：故意在 wiki/ 塞一條斷鏈，檢查器必須擋下
mkdir -p _verify/wiki
printf -- '- 壞連結：[[raw/2099-01-01-does-not-exist]]\n' > _verify/wiki/broken.md
python3 hooks/wikilink-integrity-guard.py _verify
echo "斷鏈檢查 exit code = $?   # 必須為 2（有斷鏈才算裝好；若為 0 代表驗證器沒作用）"

# 2) 過時掃描：塞一個明顯過期的保鮮標籤，--strict 下必須非 0
mkdir -p _verify/wiki
{ printf -- '<!-- updated: 2000-01-01 -->\n'; printf -- '<!-- staleness: 1d -->\n'; } > _verify/wiki/stale.md
python3 hooks/wiki-staleness-scan.py --strict _verify
echo "過時掃描 exit code = $?   # --strict 下有超期必須為 1"

# 3) 驗證器確認有效後，清掉臨時故障
rm -rf _verify
```

驗收哲學：**故意造一個已知故障，檢查器抓不到就是檢查器壞了、先修檢查器**，不是裝上就信任。斷鏈檢查器對乾淨輸入應 `exit 0`、對含斷鏈輸入應 `exit 2`；過時掃描預設 `exit 0`（提醒不阻擋）、`--strict` 有超期才 `exit 1`。

## 試點計畫（待回填）

本包 status 為 **experimental**，待首個 **MEDIUM 規模（5–20 檔）** 真實專案跑完整流程回填實戰後轉 stable。試點要驗：

- **驗什麼**：六 Phase 是否可照序落地；Question Routing 是否真能替代重讀 code；provenance / 全型別 status / visibility 三處標準化新增在實作中是否好用、有無過度設計；hooks 斷鏈與過時檢查在真 workspace 的漏接率。
- **回報格式**：規模判定（檔數/S-M-L）、各 Phase 實際產出與卡點、三處標準化新增的實用性評語、hooks 誤報/漏報清單、是否建議轉 stable。
