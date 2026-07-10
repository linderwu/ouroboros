---
name: ouroboros
description: 把單一 repo 消化成四層知識庫（raw 證據/graphify 依賴圖/wiki 決策/spec 模組契約）的萃取管線。觸發：接手陌生 codebase、要建可審計的專案知識庫、需要追問並記錄「為什麼這樣設計」、或 agent 反覆重讀同一批程式碼在浪費 context 時。小專案（少於 5 檔）不觸發——LLM 直讀即可。
---

> **狀態**：experimental；待首個 MEDIUM 規模（5–20 檔）真實專案跑完整流程回填實戰後再轉 stable。
> **血統**：本 skill 移植自外部作品 ouroboros（roaringmoon 著，Trivium v2.7）。基準版本 v2.7，含 execution modes 與擴展型別系統。
> **改寫範圍一句話**：結構重組＋強制力腳本化＋去重指回；管線機制本身未改。四層定位、size-gating、單一證據層、Question Routing、append-only/supersede 全數沿原作精神。改寫逐項對照見 `references/00-readme.md`。
> **experimental 待驗證什麼**：入籍後尚未在任一 MEDIUM 規模（5–20 檔）真實專案跑完整流程回填；hooks 強制力已附測試但未接真實 CI。首戰後回報效果再轉 stable。

## 何時使用

先做規模前置判斷——這是觸發判斷的一部分，不是進來後才做：

| 規模 | 檔數（掃 `.py/.ts/.js/.cpp/.h/.java/.go/.rs`） | 動作 |
|---|---|---|
| S | <5 檔 | **不用本 skill**。LLM 直讀即懂，建知識庫是淨負擔 |
| M | 5–20 檔 | 用本 skill，Phase 3 只對 hub 模組局部 graphify |
| L | >20 檔 | 用本 skill，Phase 3 全套（graphify + 索引工具） |

觸發情境：接手陌生 codebase 要建可審計知識庫、多個 agent／session 反覆重讀同一批 code 在燒 context、需要「決策為什麼這樣做」有據可查。

## 1. 四層定位

單一 repo 消化成四個知識層（各層職責單一、不重疊）：

- **raw/**（Grammar）：唯一證據層。PM spec、會議記錄、外部參考——**append-only，immutable**。非 code。系統裡證據只存在這一處。
- **graphify/**（Logic）：依賴圖。function-level call graph，**由工具生成**、非人工維護；code 一變就重跑再生成。
- **wiki/**（Rhetoric）：決策與程序架構。entity/concept/pattern/comparison 四型頁面，**curated、走 PR**、非自動生成；用 `[[raw/...]]` wikilink 回引證據。
- **spec/**（Logic）：模組現況契約。從 code 萃取的 per-module 介面/資料流契約（與「人寫的需求 SPEC」分工，見 references/05）。

（`repos/` 是編輯發生地、production source of truth，**不是知識層**，不對應上表。）

## 2. 六 Phase 骨架

預設 **iterative** 模式（非強制單向；v2.7 另有 incremental mode，踩到再展開）。各 phase 細節下放 references：

| Phase | 名稱 | 一句話 | 細節 |
|---|---|---|---|
| 0 | 規模評估 | 數檔決定 S/M/L，定後續工具用不用 | references/01 |
| 1 | 證據保全 | 證據入 raw/，`YYYY-MM-DD-source-type.md`，append-only | references/02 |
| 2 | 程式碼盤點 | 原始碼放 repos/`<repo>`/，這是改 code 的地方 | references/02 |
| 3 | 依賴圖 | 依規模條件式跑 graphify（S 跳過/M 局部/L 全套） | references/03 |
| 4 | 知識策展 | 起草 wiki 四型頁 + spec 契約，開 PR | references/04、05 |
| 5 | 稽核維護 | 驗 raw/ 未被改、code 變更重跑 graphify、wiki 一律走 PR | references/00 |

## 3. Question Routing

問什麼→查哪層（本 skill 獨有價值：不靠語義檢索，靠規則路由）：

| 你問什麼 | 去哪找 |
|---|---|
| 為什麼這樣設計／當初決策 | 先用 `references/06-design-rationale-inquiry.md` 追問，再寫 `wiki/concepts/` |
| 這模組跟誰連動／call graph／改了影響誰 | `graphify/` |
| API schema／介面契約 | `spec/` |
| 程式碼在哪／怎麼改 | `repos/<repo>/` |
| 證據來源／會議記錄／外部參考 | `raw/`（唯一證據層） |
| 程序架構／模組關係／運作脈絡 | `wiki/` + `graphify/` |
| 這是 bug 還是故意的 | `graphify/` → `spec/` → `wiki/`（依序） |

## 4. 鐵律

1. **raw/ 不可變**：append-only；既有證據檔不改、不覆寫、不刪。要取代舊證據＝新增檔（`YYYY-MM-DD-superseded.md`），不動舊檔。
2. **單一證據層**：全系統只有一處 raw/；無 `wiki/raw/`、無任何平行證據目錄。證據能被追加、被讀為真相，都只在這一處。
3. **wiki 頁入庫走 PR＋否證關**：起草 agent 不得自審；每條 concept 主張交獨立 agent 反駁，推不翻才 merge。過「存在性＋來源性」兩層核驗（見 references/04）。
4. **superseded 頁不進日常檢索**：標記 `status: superseded` 的頁保留歷史，但不列入日常召回。
5. **強制力在 hooks 的 exit-code，不在本文字**：斷鏈與過時偵測靠 `hooks/` 的檢查器（非 0 exit 才擋），文字只是規範。

## 5. 指回清單

以下能力由姊妹 skill 承擔，本 skill **只遵其慣例、不重寫其機制**（介面一句話）：

- **熵管理／保鮮標籤格式**：遵索引式 memory skill 慣例（`<!-- updated -->` / `<!-- staleness -->` 標籤語意由該 skill 定義）。
- **需求 SPEC 生產與 gate**：遵 spec 生產鏈 skill；本 skill 不產不審需求 SPEC，只萃取 code 現況契約。
- **wiki 主張否證**：遵對抗式 QE skill 的否證關（起草者≠審查者、finding 過否證才計分）。
- **spec 對外行為白名單供給**：遵黑箱測試 skill 的白名單/黑名單邊界（visibility: external 供其機械抽取）。

*本 skill 只裝「單一 repo → 四層知識庫」的萃取管線骨架。規模判準與工具決策見 references/01；證據攝入與 provenance 見 references/02；graphify 工具見 references/03；wiki 策展與否證關見 references/04；spec 契約與 visibility 見 references/05；「為什麼這樣設計」的追問流程見 references/06。上列姊妹能力一律指回、不在本包重複定義。*
