# 05 · Spec 契約層（Phase 4）

> **本檔對應**：SKILL.md Phase 4（知識策展）的 spec 部分與四層定位的 spec/。
> **沿原作**：spec/ ＝ per-module 契約（介面/資料流/API schema）、與 code 對齊的定位沿原作。
> **標準化新增（見 §2）**：spec 頁 `visibility: external | internal` 欄為**本包新增、非原作內容**。

---

## 1. 本 skill 的 spec/ 是什麼——與需求 SPEC 分工

本包的 spec/ ＝**從 code 萃取的「模組現況契約」**：這個模組現在對外長什麼樣（介面、輸入輸出、資料流、API schema）。它描述的是 code 的**現況**，不是「應該做成什麼」的需求。

**與「人寫的需求 SPEC」分工（重要，不要混）**：

| | 本包 spec/ | 需求 SPEC |
|---|---|---|
| 來源 | 從既有 code 萃取 | 人事前寫下的意圖 |
| 回答 | 「現在是怎樣」 | 「應該做成怎樣」 |
| 歸屬 | 本 skill 產出 | **外部 spec 生產鏈 skill** |
| 本 skill 態度 | 產出並維護 | **不產、不審**——SKILL.md §5 指回該 skill |

需求 SPEC 的起草與 gate 屬 spec 生產鏈 skill 的職責，本包只以介面銜接、不重寫其流程。

## 2. spec 頁 visibility 欄（**標準化新增，非原作內容**）

> ⚠️ 本節為**標準化新增**。原作 spec 模板無 visibility 概念。加入原因：讓「哪些契約條文是對外可觀察行為」可被機械識別，供黑箱測試白名單抽取。

每條 spec 契約標 `visibility`：

```yaml
---
title: <module>-spec
type: spec
module: <module-name>
visibility: external | internal   # 標準化新增（非原作）
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- **external**：對外可觀察行為（公開 API、對外回應、可見狀態、對外遙測）。這類條文可被黑箱測試白名單**機械抽取**——黑箱席只准斷對外可觀察量，external 契約正是其合法輸入。
- **internal**：實作細節（內部狀態、私有輔助、內部欄位名/邊界值）。**黑箱不可見**——這些是「只有看過 code 才知道的值」，不得進黑箱白名單。

visibility 只標「對外可見與否」，不改契約內容；它是給下游（尤其黑箱測試）用的可見性標記。黑箱測試如何消費白名單，屬**黑箱測試 skill** 的機制，本包不展開（SKILL.md §5 指回）。

## 3. spec↔code 對齊：「條文→實作不變量→怎麼驗」對照表

spec 契約要能對回 code，建議每個模組維護一張三欄對照表，把「契約說什麼」拉到「code 裡哪個不變量保證它」再到「怎麼驗證」：

```markdown
| 契約條文 | 實作不變量（code 裡靠什麼保證） | 怎麼驗 | visibility |
|---|---|---|---|
| <對外/內部的一條契約> | <哪個函式/欄位/流程維持它> | <驗證方式：測試/斷言/觀察> | external / internal |
```

- external 列的「怎麼驗」應是對外可觀察的驗法（黑箱可執行）。
- internal 列的「怎麼驗」可涉及內部斷言（白箱）。
- 契約與實作打架時：先確認是 code 漂移還是 spec 過時，再對應修 code 或更新 spec 頁（spec 更新走 wiki 同級的 PR 紀律）。

> 這張表的「條文→實作不變量→怎麼驗」骨架，與外部 spec-readback 類 skill 的對照表精神相通；本包只描述介面用途、不複製該 skill 的內文機制（SKILL.md §5 指回）。

## 4. code 變動時的 spec 維護

- code 改了對外介面 → 對應 external 契約與對照表要跟著更新。
- code 只改內部實作、對外行為不變 → external 契約不動，可能只動 internal 契約。
- spec 更新走 PR，不直接 push（與 wiki 同紀律）。

## 5. Phase 4（spec 部分）產出檢查

- 每個被契約的模組有 spec 頁，frontmatter 含 `visibility`。
- external / internal 標記正確：對外可觀察的才標 external。
- 「條文→實作不變量→怎麼驗」對照表存在且與現況一致。
- 需求 SPEC **未**混入本層（那屬外部 spec 生產鏈）。
