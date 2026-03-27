# 漫舟 CDP JSON Schema

> **版本**: 2.0
> **文件名**: `manzhou-cdp-schema.md`
> **角色**: 所有 Skill 输出的共享契约基础
> **维护者**: 漫舟 Agent

---

## 版本历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2026-03-25 | 漫舟 Agent | 初始版本，Phase2 优化起点 |
| 2.0 | 2026-03-25 | 漫舟 Agent | 新增复用追踪字段（usage_count/last_used/projects） |
| 2.1 | 2026-03-25 | 漫舟 Agent | P0新增：ID校验规则（第13节）/ 角色+场景+道具三层校验 |

---

## 设计原则

1. **ID 引用优于文本名**: 所有 Skill 统一使用 ID 引用角色/场景/道具，禁止文本硬编码
2. **单向演化**: meta/settings/characters/locations/items 可复用，episodes 每次生产重新生成
3. **固定时长**: shot.durationSec 为固定值（非范围），由 settings.shotDurationSec 统一定义
4. **增量追加**: append=true 时，同名资产复用已有 ID，新资产分配新 ID

---

## 顶层结构

```yaml
manzhouCDP:
  version: "1.0"                                # 固定值，契约版本号
  format: "manzhou_comic_drama_package"         # 固定值，包格式标识
  meta: {}                                      # 项目元信息
  settings: {}                                  # 全局设置
  characters: []                                # 角色库
  locations: []                                 # 场景库
  items: []                                     # 道具库
  episodes: []                                  # 分集数组
```

---

## 1. meta（项目元信息）

```yaml
meta:
  projectId: string      # UUID，唯一项目标识
  title: string          # 项目名，如"都市悬疑：他重生了"
  totalEpisodes: number  # 总集数，如 30
  currentEpisode: number # 当前处理集数，如 1
  createdAt: string      # ISO 8601 时间戳，如 "2026-03-25T10:00:00+08:00"
  updatedAt: string      # ISO 8601 时间戳
  append: boolean        # true=增量追加，false=全新创建
```

> **append=true 时的行为**:
> - 读取已有 CDP 同名角色/场景/道具时，复用已有 ID，不重复创建
> - 新角色/场景/道具分配新 ID（取当前最大 ID 往后递增）
> - episodes 数组整体替换（或按 episodeNumber 覆盖）

---

## 2. settings（全局设置）

```yaml
settings:
  targetPlatform: string   # 目标平台: douyin | kuaishou | bilibili
  aspectRatio: string      # 画幅比例: 16:9 | 9:16 | 1:1
  stylePresetId: string    # 风格预设 ID:
                            # anime | cn_anime | cn_3d | ink | cyber |
                            # us_comics | real | horror | pixar | shinkai | miyazaki |
                            # Villeneuve_Style | WongKarwai_Style | ShortDrama_Style |
                            # SciFiWasteland_Style | ChinesePeriod_Style
  shotDurationSec: number  # 单镜头固定秒数（统一值，非范围）: 10 | 15 | 25
  episodeDurationMin: number # 每集目标时长（分钟）
  textModel: string        # AI 文本模型，如 "claude-sonnet-4-6"
  imageModel: string       # 生图模型，如 "flux-1-pro"
  videoModel: string       # 生视频模型，如 "kling-1.5"
```

> **风格预设说明**（详见 `manzhou-visual-style.md`）:
> - `anime`: 日式动漫
> - `cn_anime`: 国产动漫（古风/仙侠）
> - `cn_3d`: 国产3D动画
> - `ink`: 水墨风格
> - `cyber`: 赛博朋克
> - `us_comics`: 美式漫画
> - `real`: 真人质感
> - `horror`: 恐怖悬疑
> - `pixar`: Pixar 3D风格
> - `shinkai`: 新海诚写实风
> - `miyazaki`: 宫崎骏手绘风
> - `Villeneuve_Style`: 史诗科幻（大场面/商战/家族恩怨）
> - `WongKarwai_Style`: 情绪港风（都市情感/暧昧试探）
> - `ShortDrama_Style`: 短剧爽感（打脸逆袭/情绪爆发）
> - `SciFiWasteland_Style`: 废土科幻（末世废土/未来都市）
> - `ChinesePeriod_Style`: 古风国潮（古装/传统美学/宫廷江湖）

---

## 3. characters（角色库）

```yaml
characters:
  - id: string           # 角色 ID，格式: char_01, char_02...（共8个基准）
    name: string         # 角色中文名，如"沈墨"
    aliases: []          # 别名数组，如 ["沈小姐", "墨墨"]
    gender: string       # male | female | other
    ageRange: string     # 年龄段，如 "25-30" 或 "40左右"
    appearance: string   # 外貌描述（AI 生图用）
    clothing: string     # 服饰描述（分场景）
    persona: string      # 人设/性格描述（分集引用）
    dnaAnchors: []       # DNA 锚点（角色一致性保障）
      - type: string     # 锚点类型: 配饰 | 外貌 | 服装
        description: string  # 具体描述，如"左耳戴银色耳钉"
    referenceImage: string # 参考图路径（本地路径或 URL）
    # --- v2.0 复用追踪字段 ---
    usage_count: number  # 累计被引用次数（每次被 shots.characterIds 引用时 +1）
    last_used: string    # 最后使用时间（ISO 8601），如 "2026-03-25T10:00:00+08:00"
    projects: []         # 使用过的项目列表，如 ["格子间女人", "都市重生传"]
```

### DNA 锚点设计原则

每个角色建议设置 **3-5 个 DNA 锚点**：
- **配饰锚点**: 标志性配饰（耳钉/手表/戒指），生图时必须触发
- **外貌锚点**: 不可变特征（胎记/疤痕/眉形），生图时严格遵循
- **服装锚点**: 经典装扮（白衬衫+黑西裤），每集至少出现一次

> **别名 aliases 的作用**: 对话中可能出现角色的昵称/代称，aliases 用于别名到正式 name 的映射

---

## 4. locations（场景库）

```yaml
locations:
  - id: string           # 场景 ID，格式: loc_01, loc_02...（共8个基准）
    name: string         # 场景名，如"沈氏集团总裁办公室"
    description: string  # 氛围描述（AI 生图/视频用）
    props: []           # 场景内道具列表（文本描述，非 ID）
    moodBoard: string   # Mood Board 路径（图片）
    # --- v2.0 复用追踪字段 ---
    usage_count: number  # 累计被引用次数（每次被 shots.locationId 引用时 +1）
    last_used: string    # 最后使用时间（ISO 8601）
    projects: []         # 使用过的项目列表
```

---

## 5. items（道具库）

```yaml
items:
  - id: string           # 道具 ID，格式: item_01, item_02...（共30个基准）
    name: string         # 道具名，如"翡翠吊坠"
    description: string  # 功能描述（在剧情中的作用）
    appearance: string   # 外观描述（AI 生图用）
    referenceImage: string # 参考图路径（本地路径或 URL）
    # --- v2.0 复用追踪字段 ---
    usage_count: number  # 累计被引用次数（每次被 shots.itemIds 引用时 +1）
    last_used: string    # 最后使用时间（ISO 8601）
    projects: []         # 使用过的项目列表
```

> **道具系统的价值**:
> - 关键道具（信物/文件/武器）可跨集追踪，增强叙事连贯性
> - 生图/视频 Prompt 中引用 item ID，保证道具外观一致性
> - 相当于 TapNow/联易方舟的"资产库"机制

---

## 6. episodes（分集）

```yaml
episodes:
  - episodeNumber: number  # 集号，从 1 开始
    title: string          # 本集标题
    hook: string           # 本集钩子（开头吸引点）
    twist: string          # 本集反转点
    endingHook: string     # 结尾钩子（悬念引导下一集）
    shots: []             # 镜头数组
```

---

## 7. shots（镜头）

```yaml
shots:
  - id: string             # 镜头 ID，格式: ep{集号}_sh{序号}，如 ep01_sh01
    shotNumber: number     # 镜头序号，从 1 开始（增量追加时自动偏移）
    durationSec: number    # 固定秒数，与 settings.shotDurationSec 一致
    locationId: string     # 场景 ID 引用，如 "loc_01"（升级！原来用文本）
    characterIds: []       # 角色 ID 数组，如 ["char_01", "char_02"]（升级！原来用文本）
    itemIds: []            # 道具 ID 数组，如 ["item_01"]（新增！）
    script: string         # 镜头描述（叙事文字，非 Prompt）
    dialogue: []           # 对话数组
      - speakerId: string  # 说话角色 ID 引用，如 "char_01"（升级！原来用 name 文本）
        text: string       # 对话文本
    imagePrompt: string    # AI 生图 Prompt
    videoPrompt: string    # AI 生视频 Prompt
    objective: string      # 镜头目的（为什么拍这个镜头）
    action: string         # 时序动作（人物在做什么）
    vo: string             # 配音旁白文本
    bgm: string            # BGM 描述（如"紧张悬疑，弦乐渐强"）
    sfx: string            # 音效描述（如"门铃响起"）
    emotionCurve: string   # 情绪标注，如 "低-高-爆-回落"
    status: string         # 状态: pending | generating | completed
```

### status 状态机

```
pending → generating → completed
         ↓ (失败)
       failed
```

### emotionCurve 格式

格式: `情绪1-情绪2-情绪3-...`，描述单个镜头内的情绪变化路径。
情绪值可选: `平|低|中|高|爆`（平静-低沉-平稳-高潮-爆发）

---

## 8. ID 命名规范

| 资产类型 | 格式 | 示例 | 基准数量 |
|----------|------|------|----------|
| 角色 | `char_XX` | `char_01`, `char_08` | 8个 |
| 场景 | `loc_XX` | `loc_01`, `loc_08` | 8个 |
| 道具 | `item_XX` | `item_01`, `item_30` | 30个 |
| 镜头 | `ep{集号}_sh{序号}` | `ep01_sh01`, `ep15_sh23` | 每集动态 |

> **ID 分配规则**:
> - 基准 ID 在项目初始化时一次性分配（角色8个+场景8个+道具30个）
> - 增量追加时，新资产分配新 ID（取当前最大编号+1）
> - ID 一旦分配，永不回收和复用

---

## 9. 增量追加规则（append=true）

```
读取已有CDP
  ↓
同名角色/场景/道具 → 复用已有 ID
  ↓
新角色/场景/道具 → 分配新 ID（max+1）
  ↓
episodes 数组
  ↓
  ├─ episodeNumber 存在 → 覆盖该集
  └─ episodeNumber 不存在 → 追加新集
  ↓
shotNumber 从 1 开始，系统自动计算全局偏移
  ↓
输出新 CDP（append=true）
```

---

## 10. Skill 输出规范

### 强制要求

1. **禁止文本名硬编码**: 所有角色/场景/道具引用必须使用 ID
   - ❌ `"沈墨走进总裁办公室"`
   - ✅ `"char_01 走进 loc_01"`
2. **固定时长**: durationSec 必须等于 settings.shotDurationSec
3. **ID 引用完整性**: dialogue[].speakerId 必须指向 characters[].id
4. **字段不缺省**: shots 数组中所有字段都必须有值（即使是空字符串）

### JSON 输出约定

所有 Skill 输出的 JSON 必须符合本 Schema 定义的字段。
工具函数（如 TypeScript 类型定义）参考:

```typescript
// 顶层结构
interface ManzhouCDP {
  version: string;
  format: string;
  meta: Meta;
  settings: Settings;
  characters: Character[];
  locations: Location[];
  items: Item[];
  episodes: Episode[];
}

// 角色
interface Character {
  id: string;            // "char_01"
  name: string;          // "沈墨"
  aliases: string[];     // ["沈小姐", "墨墨"]
  gender: 'male' | 'female' | 'other';
  ageRange: string;      // "25-30"
  appearance: string;
  clothing: string;
  persona: string;
  dnaAnchors: DNAAnchor[];
  referenceImage: string;
  // v2.0 复用追踪
  usage_count: number;
  last_used: string | null;
  projects: string[];
}

interface DNAAnchor {
  type: '配饰' | '外貌' | '服装';
  description: string;
}

// 场景
interface Location {
  id: string;            // "loc_01"
  name: string;
  description: string;
  props: string[];
  moodBoard: string;
  // v2.0 复用追踪
  usage_count: number;
  last_used: string | null;
  projects: string[];
}

// 道具
interface Item {
  id: string;            // "item_01"
  name: string;
  description: string;
  appearance: string;
  referenceImage: string;
  // v2.0 复用追踪
  usage_count: number;
  last_used: string | null;
  projects: string[];
}

// 分集
interface Episode {
  episodeNumber: number;
  title: string;
  hook: string;
  twist: string;
  endingHook: string;
  shots: Shot[];
}

// 镜头
interface Shot {
  id: string;            // "ep01_sh01"
  shotNumber: number;
  durationSec: number;
  locationId: string;     // "loc_01"
  characterIds: string[]; // ["char_01", "char_02"]
  itemIds: string[];     // ["item_01"]
  script: string;
  dialogue: Dialogue[];
  imagePrompt: string;
  videoPrompt: string;
  objective: string;
  action: string;
  vo: string;
  bgm: string;
  sfx: string;
  emotionCurve: string;  // "低-高-爆-回落"
  status: 'pending' | 'generating' | 'completed';
}

interface Dialogue {
  speakerId: string;     // "char_01"
  text: string;
}
```

---

## 11. 完整示例（最小可用 CDP）

```yaml
manzhouCDP:
  version: "1.0"
  format: "manzhou_comic_drama_package"
  meta:
    projectId: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    title: "都市悬疑：他重生了"
    totalEpisodes: 30
    currentEpisode: 1
    createdAt: "2026-03-25T10:00:00+08:00"
    updatedAt: "2026-03-25T12:00:00+08:00"
    append: false

  settings:
    targetPlatform: "douyin"
    aspectRatio: "9:16"
    stylePresetId: "cn_anime"
    shotDurationSec: 15
    episodeDurationMin: 5
    textModel: "claude-sonnet-4-6"
    imageModel: "flux-1-pro"
    videoModel: "kling-1.5"

  characters:
    - id: "char_01"
      name: "沈墨"
      aliases: ["沈小姐", "墨墨"]
      gender: "female"
      ageRange: "25-30"
      appearance: "黑长直发，眉眼清冷，肤白如瓷，左耳戴银色耳钉"
      clothing: "白衬衫+黑色铅笔裙"
      persona: "表面冷艳高傲，实则内心脆弱，重生后步步为营"
      dnaAnchors:
        - type: "配饰"
          description: "左耳戴银色耳钉，是母亲遗物"
        - type: "外貌"
          description: "右眼尾有淡红色泪痣"
        - type: "服装"
          description: "永远的白衬衫，袖口卷至手腕上方两寸"
      referenceImage: "./assets/characters/char_01_ref.png"
      usage_count: 0
      last_used: null
      projects: []

  locations:
    - id: "loc_01"
      name: "沈氏集团总裁办公室"
      description: "现代简约高管办公室，落地窗外城市夜景，灯光冷白"
      props: ["黑色大理石办公桌", "整面墙书架", "威士忌酒杯"]
      moodBoard: "./assets/locations/loc_01_mood.jpg"
      usage_count: 0
      last_used: null
      projects: []

  items:
    - id: "item_01"
      name: "翡翠吊坠"
      description: "沈墨母亲遗物，藏有集团核心机密的钥匙"
      appearance: "帝王绿翡翠，鸡心形，银链"
      referenceImage: "./assets/items/item_01_ref.png"
      usage_count: 0
      last_used: null
      projects: []

  episodes:
    - episodeNumber: 1
      title: "重生"
      hook: "沈墨从ICU醒来，发现自己回到了三年前"
      twist: "前世的死对头李薇，竟是来探病的"
      endingHook: "床头柜上，手机显示：明天，董事会"
      shots:
        - id: "ep01_sh01"
          shotNumber: 1
          durationSec: 15
          locationId: "loc_01"
          characterIds: ["char_01"]
          itemIds: []
          script: "沈墨从病床上猛然睁开眼，冷汗浸透病号服"
          dialogue:
            - speakerId: "char_01"
              text: "我...还活着？"
          imagePrompt: "cinematic, hospital room, woman waking up in bed, pale skin, black straight hair, silver earring, cold sweat, dramatic lighting, cn_anime style"
          videoPrompt: "slow dolly in, woman eyes snap open, gasp breath, tense atmosphere"
          objective: "建立重生设定，传递不安感"
          action: "沈墨睁眼，手握床单，呼吸急促"
          vo: "医院的白炽灯刺得人睁不开眼。我低头看着自己的手——没有车祸后的疤痕，皮肤光洁如新。"
          bgm: "悬疑低沉，钢琴单音+弦乐震音"
          sfx: "心电监护仪持续滴声"
          emotionCurve: "低-中"
          status: "completed"
```

---

## 12. 与旧版字段对照

| 旧版字段（文本引用） | 新版字段（ID引用） | 变化说明 |
|---------------------|-------------------|----------|
| location: "总裁办公室" | locationId: "loc_01" | 文本→ID引用 |
| character: "沈墨" | characterIds: ["char_01"] | 单文本→ID数组 |
| speaker: "沈墨" | speakerId: "char_01" | name文本→ID |
| duration: "10-15秒" | durationSec: 15 | 范围→固定值 |
| 无 | itemIds: [] | 新增道具数组 |
| 无 | aliases: [] | 新增别名数组 |
| 无 | emotionCurve: string | 新增情绪曲线 |
| append: 无 | append: boolean | 新增增量追加标志 |

---

## 13. ID 校验规则（v2.0 P0强制 — ZJT核心机制）

**所有分镜脚本生成时，必须执行以下三层校验，任何一层失败则禁止生成。**

### 校验一：角色 ID 校验

```
输入：分镜脚本中的所有 characterIds[]
↓
查询：cdp-global.json → characters[].id
↓
结果：
  ✅ 全部存在 → 继续
  ❌ 存在未知ID → 报错：未知角色ID [xxx]，请先在CDP中添加或更正
```

### 校验二：场景 ID 校验

```
输入：分镜脚本中的所有 locationId[]
↓
查询：cdp-global.json → locations[].id
↓
结果：
  ✅ 全部存在 → 继续
  ❌ 存在未知ID → 报错：未知场景ID [xxx]，请先在CDP中添加或更正
```

### 校验三：道具 ID 校验

```
输入：分镜脚本中的所有 itemIds[]
↓
查询：cdp-global.json → items[].id
↓
结果：
  ✅ 全部存在 → 继续
  ❌ 存在未知ID → 报错：未知道具ID [xxx]，请先在CDP中添加或更正
```

### 校验执行时机

| 环节 | 校验范围 | 说明 |
|------|---------|------|
| 分镜脚本生成（Step7） | 全部 locationId + itemIds + characterIds | 全面校验 |
| 单镜头修改 | 当前镜头涉及的 ID | 增量校验 |
| CDP资产新增 | 新增的 ID | 新增校验 |

### 校验算法（伪代码）

```python
def validate_shot_ids(shot: dict, cdp: dict) -> tuple[bool, list[str]]:
    """
    校验镜头中所有ID引用是否存在
    返回: (is_valid, error_messages[])
    """
    errors = []
    char_ids = [c["id"] for c in cdp.get("characters", [])]
    loc_ids = [l["id"] for l in cdp.get("locations", [])]
    item_ids = [i["id"] for i in cdp.get("items", [])]

    # 角色校验
    for cid in shot.get("characterIds", []):
        if cid not in char_ids:
            errors.append(f"角色ID不存在: {cid}")

    # 场景校验
    loc = shot.get("locationId")
    if loc and loc not in loc_ids:
        errors.append(f"场景ID不存在: {loc}")

    # 道具校验
    for iid in shot.get("itemIds", []):
        if iid not in item_ids:
            errors.append(f"道具ID不存在: {iid}")

    return len(errors) == 0, errors
```

### 自动化执行规则

```
✅ 分镜脚本生成前：自动加载 cdp-global.json
✅ 逐镜头校验：每生成一个镜头立即校验
✅ 全部通过后才输出：禁止生成含无效ID的分镜脚本
❌ 不得绕过校验：禁止用 --force 参数跳过校验
❌ 不得创建幽灵ID：不允许在分镜中引用不存在的角色/场景/道具ID
```
