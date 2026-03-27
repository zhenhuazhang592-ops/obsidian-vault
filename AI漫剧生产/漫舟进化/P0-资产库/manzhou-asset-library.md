# 漫舟资产库使用规范

> **版本**: 1.0.0
> **文件名**: `manzhou-asset-library.md`
> **角色**: 所有 Skill 新项目启动时的资产查询与复用指南
> **维护者**: 漫舟 Agent

---

## 1. 资产库定位

**cdp-global.json** 是漫舟智能体的全局资产仓库，位于：

```
AI漫剧生产/漫舟进化/P0-资产库/cdp-global.json
```

**作用**:
- 跨项目复用角色/场景/道具，避免重复造资产
- 积累 usage_count，形成"哪些资产被反复使用"的数据
- 为 P1 效果追踪和 P2 Prompt进化提供底座数据

---

## 2. 新项目启动流程

```
Step 1: 检查 cdp-global.json
         ↓
Step 2: 查询是否有相似角色/场景/道具
         ↓
  ├─ 找到 → 复用已有资产，usage_count++
  └─ 未找到 → 生成新ID，追加到 cdp-global.json
         ↓
Step 3: 输出新项目 CDP（含 ID 引用）
```

### Step 1 - 查询规则

**角色复用条件**（需同时满足）:
- 相同人设类型（如"职场女强人"、"霸道总裁"）
- 相同视觉风格（如"都市正装"、"古风仙侠"）
- 相同年龄段

**场景复用条件**（需同时满足）:
- 相同场景类型（办公/居家/户外/室内）
- 相似光影风格（如"冷白日光"、"暖黄灯光"）
- 相似空间感（开阔/逼仄/高挑）

**道具复用条件**:
- 相同叙事功能（如"象征权力的钢笔"、"定情信物"）

### Step 2 - ID 分配规则

```
已有资产最大编号 → 新编号 = max + 1
例如: 已有 char_01, char_02 → 新角色 = char_03
```

---

## 3. ID 引用规范

所有 Skill 输出**禁止文本硬编码**，必须使用 ID 引用：

| 资产类型 | 格式 | 示例 |
|----------|------|------|
| 角色 | `char_XX` | `char_01`, `char_08` |
| 场景 | `loc_XX` | `loc_01`, `loc_08` |
| 道具 | `item_XX` | `item_01`, `item_30` |
| 镜头 | `ep{集号}_sh{序号}` | `ep01_sh01`, `ep15_sh23` |

**正确示例**:
```
locationId: "loc_01"         ← ID 引用
characterIds: ["char_01"]    ← ID 数组
speakerId: "char_01"         ← 对话角色 ID
```

**错误示例**:
```
locationId: "总裁办公室"      ← 文本硬编码，禁止！
characterIds: ["谭斌"]        ← 文本硬编码，禁止！
```

---

## 4. usage_count 更新规则

| 触发时机 | 更新操作 |
|---------|---------|
| 镜头引用角色 `characterIds` | `char_xx.usage_count++` |
| 镜头引用场景 `locationId` | `loc_xx.usage_count++` |
| 镜头引用道具 `itemIds` | `item_xx.usage_count++` |
| 项目完成时 | `last_used = now`，`projects.push(项目名)` |

---

## 5. cdp-global.json 结构速查

```json
{
  "version": "1.0.0",
  "meta": {
    "created": "2026-03-25",
    "project": null,
    "type": "global_asset_library",
    "append": true
  },
  "characters": [ /* char_01, char_02... */ ],
  "locations": [ /* loc_01, loc_02... */ ],
  "items": [ /* item_01, item_02... */ ]
}
```

---

## 6. 资产库维护频率

| 场景 | 维护操作 |
|------|---------|
| 新项目启动 | 查询复用，usage_count++ |
| 项目完成 | 补充 last_used + projects |
| Prompt进化成功 | 将新 Prompt 沉淀至 prompt 库 |
| 失败模式出现 | 写入 failure-log，防重复触发 |

---

## 7. 与 P1/P2 的联动

```
P0 资产库（已有资产）
    ↓ 被 P1 引用（哪些镜头用了哪些资产）
    ↓ 产出 usage_count + 评分数据
    ↓ 喂给 P2 进化引擎
    ↓ 成功 Prompt 入库 → 反哺 P0 资产库
```

---

## 8. 附录：资产库文件索引

| 文件 | 路径 |
|------|------|
| 全局资产包 | `P0-资产库/cdp-global.json` |
| Schema 定义 | `P0-资产库/cdp-global-schema.json` |
| 本规范 | `P0-资产库/manzhou-asset-library.md` |
| 迁移示例 | `P0-资产库/格子间女人-cdp-migration.json` |
