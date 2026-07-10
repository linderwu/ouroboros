# 06 · 設計理由追問（Why This Design）

> **本檔用途**：當問題是「為什麼這樣設計」「為什麼不走另一條路」「這個取捨還有效嗎」時，提供一套追問流程，把直覺、歷史、限制與證據整理成 `wiki/concepts/` 或 `wiki/comparisons/`。
> **定位**：這不是新的知識層；它是 Phase 4 起草 concept/comparison 前的詢問方法。

---

## 1. 觸發

使用本流程處理下列問題：

- 為什麼選這個架構、工具、資料流、API 邊界、部署方式或模組切分？
- 當初還有什麼選項，為什麼沒選？
- 這個設計是刻意決策、歷史包袱、限制下的妥協，還是尚未驗證的假設？
- 現在需求變了，舊決策還有效嗎？

## 2. 追問梯

依序問，不要跳到結論。每層都盡量找 `raw/`、`repos/`、`graphify/` 或 `spec/` 支撐。

| 層級 | 要問的問題 | 產出 |
|---|---|---|
| 1. 目的地 | 這個設計要達成什麼使用者/系統目的？不做會怎樣？ | 一句目的 |
| 2. 約束 | 當時有哪些硬限制：時間、相容性、成本、安全、效能、團隊熟悉度、既有系統？ | 限制清單 |
| 3. 選項 | 至少有哪些可行替代路線？包括「不改」與「延後」 | alternatives |
| 4. 取捨 | 選現在方案犧牲了什麼、換到什麼？ | pros/cons |
| 5. 證據 | 哪些 code、issue、會議記錄、spec 或事故支持這個說法？ | wikilinks |
| 6. 驗證 | 怎麼知道這個設計仍然有效？有哪些指標、測試或觀察？ | validation |
| 7. 失效條件 | 什麼情況下應該重開決策？ | invalidation triggers |

## 3. 導航比喻

把設計討論當成導航，不只問「怎麼到」，也問「為什麼這樣走」：

- 目的地：需求目的與成功條件。
- 交通工具：技術棧、架構模式、服務邊界。
- 國道/省道：速度、成本、風險、可維護性的取捨。
- 國一/國三：同類方案之間的細節差異。
- 交流道：何時切換模組、依賴或流程。
- 休息站：風險緩衝、觀測點、回滾點、人工檢查點。

這個比喻只用來幫助追問，不寫進最終 wiki 頁，除非它本身來自真實討論證據。

## 4. 判斷輸出型別

- 已經知道「選了什麼」，要補理由：寫 `wiki/concepts/`，套 `concept-template.md`。
- 還在 A/B 方案間選：寫 `wiki/comparisons/`，套 `comparison-template.md`。
- 發現是 runtime 現象而非設計決策：改寫 `wiki/patterns/`。
- 發現只是某個 actor 的責任邊界：補 `wiki/entities/`。

## 5. 起草規則

- 區分「已證實」「推測」「待確認」。推測不能偽裝成決策。
- 沒有證據時，先列為 open question，不要補故事。
- 對每個替代方案至少寫一個支持它的理由；避免只替現行方案辯護。
- 每個 concept 至少要有一個失效條件，否則未來不知道何時重開討論。
- 引用 `raw/` 時同時做來源性檢查：來源內容必須真的支撐該主張。

## 6. Concept 最小骨架

```markdown
## Summary
因為 [目的] 且受 [主要約束] 影響，所以選擇 [決策]，接受 [主要代價] 以換取 [主要收益]。

## Context
- Goal:
- Constraints:
- Evidence:

## Decision

## Alternatives Considered

## Consequences

## Validation

## Invalidation Triggers
```

## 7. 完成檢查

- 能回答「目的地在哪」與「為何不是其他路」。
- 每個主要理由都連到證據或明標為待確認。
- 有 alternatives、tradeoffs、validation、invalidation triggers。
- 若是 concept 主張，依 `04-wiki-curation.md` 過否證關。
