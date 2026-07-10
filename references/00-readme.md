# 00 · 導讀與改寫範圍聲明

> **本檔用途**：references/ 的入口。說明哪個 phase 讀哪檔、原版出處與版本基準、以及本包相對原作「哪些沿用、哪些是標準化新增」。
> **原版出處**：ouroboros，作者 roaringmoon，repo `github.com/linderwu/ouroboros`。
> **版本基準**：Trivium **v2.7**（含 execution modes 與擴展型別系統）。原作 SKILL.md 標題一度停在 v2.5、內文已推進到 v2.7——本包統一以 v2.7 為準。

---

## 1. 導讀：哪個 phase 讀哪檔

| 你在做的事 | 讀這檔 |
|---|---|
| 判斷專案規模、決定要不要動工具 | `01-size-assessment.md` |
| 把證據放進 raw/、處理攝入安全 | `02-evidence-and-code.md` |
| 跑 graphify、選依賴圖工具 | `03-graphify-tooling.md` |
| 起草 wiki 頁、跑否證關與兩層核驗 | `04-wiki-curation.md` |
| 從 code 萃 spec 契約、標 visibility | `05-spec-bridge.md` |
| 追問「為什麼這樣設計」、補決策理由與失效條件 | `06-design-rationale-inquiry.md` |
| 稽核維護（raw/ 完整性、重跑 graphify、PR 紀律） | 回 SKILL.md §4 鐵律 + 本檔 §4 |

SKILL.md 是骨架與鐵律；深度執行細節全在本目錄。SKILL.md 不重複這裡的內容，這裡不重複 SKILL.md 的鐵律（單一事實來源）。

## 2. 改寫範圍聲明（crystal 規則：標準化新增必須明標非原文）

### 2.1 沿原作（保留原設計精神，未改機制）

- **四層知識結構**（raw/graphify/wiki/spec）與各層職責——原作核心，原封保留。
- **size-gating**：「LLM 本身就擅長理解小型程式碼；工具是增強而非取代」核心句與 S/M/L 三級判準——沿 v2.5 原設計。
- **單一證據層規則**：「raw/ 是唯一 canonical evidence layer、無 wiki/raw/」——沿 v2.4.1 原文精神。
- **raw/ append-only / supersede**：既有證據不改不刪、以新增檔取代——沿原作。
- **Question Routing 表**：問什麼→查哪層的規則式路由——沿原作（本包依「單 repo」範圍精簡了跨 repo 列）。
- **wiki 走 PR、NEVER auto-merge、起草者不自審**——沿原作品質關卡精神。
- **concept never delete、mark superseded**——沿原作。
- **wikilink 表達程序架構**（`[[a]] → [[b]] → [[c]]`）——沿原作。

### 2.2 標準化新增（**非原作內容**，為對接公司框架而加，逐一明標）

以下四處在原作中不存在，是入籍時依框架慣例加入的**標準化新增**，各自在對應檔案內也重複明標：

| 新增項 | 所在檔案 | 明標位置 |
|---|---|---|
| **raw/ 頁 provenance frontmatter**（`source / ingested-by / trust / sanitized`）＋「外部文字＝注入面」攝入警語 | `02-evidence-and-code.md` | §2 開頭 |
| **wiki 全型別 status 生命週期**（原作只有 concept 有 status，本包擴到 entity/pattern/comparison 皆有） | `04-wiki-curation.md` | §1 模板表 + §2 |
| **spec 頁 `visibility: external \| internal` 欄** | `05-spec-bridge.md` | §2 |
| **設計理由追問流程**（目的、約束、選項、取捨、證據、驗證、失效條件） | `06-design-rationale-inquiry.md` | 全檔 |

### 2.3 結構重組與去重（改了組織方式，未改機制本身）

- **強制力腳本化**：原作把 staleness/wikilink 檢查寫成文字規範（v2.6 提「enforcement hooks」但 repo 未附可執行腳本）；本包把「斷鏈檢查」「過時掃描」落成 `hooks/` 下可執行的 standalone 檢查器，強制力改由 exit-code 承擔。
- **去重指回**：原作把熵管理、SPEC 生產、否證關等一併寫進單一 SKILL.md；本包改為只保留萃取管線骨架，其餘一律指回姊妹 skill（見 SKILL.md §5）、不重寫其機制內文。

### 2.4 砍掉的原作項（範圍收斂）

- **跨 repo 支援與跨 repo 合併輸出**：原作支援多個 repo 組成的 workspace，以及跨 repo 合併後的依賴圖輸出。本包範圍**收斂到單一 repo**；跨 repo 屬「踩到才加」的擴充，預設不納入。
- **語義檢索承諾**：原作 Read Workflow 提到一個外部「語義檢索 service」（no summarization）作為 chatbot 消費端。本包**不承諾任何語義檢索**——召回一律走 Question Routing 規則路由 + agent 對檔案系統的 grep/glob。

## 3. 型別系統說明（v2.7 方向）

原作 v2.7 的「擴展型別系統」把 status 生命週期從 concept 專屬推向全型別（procedure/deprecated/lifecycle 等狀態）。本包據此把 entity/concept/pattern/comparison 四型頁面**全部**納入 status 生命週期——此為順著 v2.7 方向的標準化新增，細節與明標見 `04-wiki-curation.md`。

## 4. 稽核維護（Phase 5 展開）

SKILL.md §4 鐵律的執行面補充：

- **驗 raw/ 完整性**：確認 append-only 未被破壞（既有檔的 hash/內容未變動）。以 git 歷史或 hooks 抽查。
- **驗 repos/ 與 production 一致**：盤點 repos/ 內容是否落後真實部署。
- **code 變更重跑 graphify**：這是唯一自動化再生成的部分——依賴變了就重掃，不做累積式手改（見 `03-graphify-tooling.md` §3）。
- **wiki 更新一律走 PR**：不直接 push，不 auto-merge。
- **斷鏈與過時**：交 `hooks/` 檢查器（wikilink 完整性、staleness 掃描），強制力在 exit-code。
