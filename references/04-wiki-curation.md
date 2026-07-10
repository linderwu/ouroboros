# 04 · Wiki 策展（Phase 4）

> **本檔對應**：SKILL.md Phase 4（知識策展）的 wiki 部分與 §4 鐵律 3–4。
> **沿原作**：entity/concept/pattern/comparison 四型頁面、wikilink 程序架構表達、concept never-delete/superseded、PR 品質關卡皆沿原作。
> **標準化新增（見 §1、§2）**：「所有型別都有 status 生命週期」為**本包新增**（原作僅 concept 有 status），順 v2.7 擴展型別方向。

---

## 1. 四型頁面與模板

wiki/ 四個子目錄，一頁一個單位：

| 型別 | 目錄 | 一頁記什麼 | 觸發時機 |
|---|---|---|---|
| entity | `wiki/entities/` | 一個 actor（service/module/外部依賴） | 盤點到一個角色 |
| concept | `wiki/concepts/` | 一個設計決策/取捨 | 做出或發現一個決策 |
| pattern | `wiki/patterns/` | runtime 經驗/debug 線索 | incident、post-mortem、效能觀察後 |
| comparison | `wiki/comparisons/` | A vs B 選項比較 | 需要在方案間取捨時 |

問「為什麼這樣設計」時，先讀 `06-design-rationale-inquiry.md` 做追問，再決定落到 concept 或 comparison。不要只寫結論；要補目的、約束、替代方案、取捨、證據、驗證與失效條件。

**共用 frontmatter**（**所有型別都含 status——此為標準化新增，見 §2**）：

```yaml
---
title: <string>
type: entity | concept | pattern | comparison
tags: [<string>]
status: active | superseded | deprecated   # 標準化新增：全型別皆有（原作僅 concept 有）
created: YYYY-MM-DD
updated: YYYY-MM-DD
<!-- updated: YYYY-MM-DD -->
<!-- staleness: Nd -->
---
```

## 2. 全型別 status 生命週期（**標準化新增，非原作內容**）

> ⚠️ 本節為**標準化新增**。原作 frontmatter 的 `status` 只掛在 concept（原文 `status: active | superseded | deprecated  # concepts only`）。本包順 v2.7「擴展型別系統/lifecycle」方向，把 status 生命週期推廣到 entity/concept/pattern/comparison **全部四型**。

- **active**：現行有效，進日常檢索。
- **superseded**：被新頁取代，保留歷史但**不進日常檢索**（SKILL.md 鐵律 4）。以 `Superseded By: [[新頁]]` 連到後繼。
- **deprecated**：已淘汰、不再適用（如某 entity 已下線的服務）。保留供歷史查詢，不進日常檢索。

**never delete**：任一型別的頁面都不刪除，改狀態即可——舊決策/舊角色/舊 pattern 的歷史是有價值的審計軌跡。

## 3. wikilink 與程序架構

wiki 頁用 wikilink 建語意連結，也用它表達「程序架構」（模組怎麼互相呼叫），維持全系統統一為 markdown、不另引流程圖 DSL：

- 引證據（唯一證據層）：`[[raw/2026-07-09-source-type]]`
- 引程式碼位置：`[[repos/<repo>/<entity>]]`
- 引其他 wiki 頁：`[[entity-name]]`
- 程序流：`Module flow: [[entity-a]] → [[entity-b]] → [[entity-c]]`
- Runbook：`Runbook: [[pattern-x]] when [[symptom-y]]; see [[entity-z]]`

wikilink 目標必須真實存在——斷鏈由 `hooks/` 的 wikilink 完整性檢查器機械擋（見 §6）。

## 4. 否證關流程（鐵律 3 展開）

wiki 頁**入庫走 PR，NEVER auto-merge**；且起草者不得自審。concept 主張尤其要過否證關：

1. **起草 agent ≠ 審查 agent**：審查交給一個**新 session**（不帶起草 context），球員不兼裁判。
2. **每條 concept 主張交獨立反駁**：審查 agent 的任務是「試著推翻這條主張」，不是「確認它對」。
3. **推不翻才 merge**：主張被推翻→退回重寫或撤下；只有真的推不翻的主張才計入、才 merge。寧可放過、不可誣告。

## 5. 兩層核驗（鐵律 3 展開）

每條引用證據的主張，入庫前過兩層，缺一不可：

1. **存在性**：wikilink 指的 `[[raw/...]]` 目標檔**真的存在**。這層可機械化——由 `hooks/` 的 wikilink 完整性檢查器擋斷鏈（見 §6）。
2. **來源性（provenance）**：被引用的證據**真的支持該主張**，不是「檔案存在但內容其實不支持」。這層機器擋不住，是**人審抽查的重點**——起草者容易拿「存在但不對題」的證據充數，審查時要開來源檔對照主張是否真被支撐。

只驗存在性會被「完美的假證據」騙過：某筆 raw/ 確實存在、wikilink 也不斷，但內容根本沒講到主張要的那件事。存在性過關、來源性當場戳破——這正是需要人審的地方。

## 6. 保鮮標籤與 hooks 分工

**保鮮標籤格式**（語意沿索引式 memory 慣例，SKILL.md §5 指回該 skill）：

```markdown
<!-- updated: YYYY-MM-DD -->
<!-- staleness: Nd -->
```

**各型別預設 staleness**（超期只 ⚠️ 提醒、不阻擋）：

| 型別 | 預設 staleness |
|---|---|
| entity | 30d |
| concept | 60d |
| pattern | 120d |
| comparison | 60d |

- `今天 − updated > staleness` → 該頁列入 ⚠️ 過時提醒清單，請人確認是否還準。
- **強制力分工**：斷鏈（存在性）由 hooks **擋**（exit 非 0）；過時由 hooks **提醒**（預設不擋）。文字規範只是說明，真正的機械檢查在 `hooks/`——掛載與已知漏接見 `hooks/` 檔首註解與 README 部署驗收節。

## 7. Phase 4（wiki 部分）產出檢查

- 每頁 frontmatter 四欄齊 + status + 保鮮標籤。
- wikilink 全部指向存在目標（跑 hooks 斷鏈檢查通過）。
- concept/comparison 回答「為什麼」時，已套 `06-design-rationale-inquiry.md` 的追問梯。
- concept 主張過否證關（有獨立審查 session 的紀錄）。
- 引用證據過來源性抽查（不是只驗存在）。
- 入庫走 PR，無 auto-merge。
