# S2: CDP 资产包（硬约束层）

## 任务

基于 S1 风格指南 + S0 解析报告，构建角色/场景/道具 DNA。

## 输入

- S0-解析报告.md
- S1-风格指南.md

## 输出文件

- `01-CDP资产包/CDP-JSON.md`

## 引用声明

```yaml
引用声明:
  上游步骤: S0-解析报告.md, S1-风格指南.md
  引用ID列表: [char_xxx, scene_xxx, item_xxx]
  风格指南版本: [v1.0.0]
```

## 输出内容：角色 DNA（每个角色一条）

每个角色按 schema.py 的 CHARACTER_DNA_SCHEMA 填写，示例：

```yaml
char_fugui:
  id: char_fugui
  name: 福贵
  gender: male
  age_range: "20-80"
  visual:
    face_shape: "长脸，颧骨略高，年轻时皮肤白皙，晚年黝黑粗糙 [引用S1]"
    skin_tone: "年轻时白皙微黄，中年黝黑，晚年古铜色 [引用S1色调]"
    eye_features: "眼睛有神，年轻时明亮，晚年温和 [引用S1]"
    body_type: "年轻时修长挺拔，中年弯腰驼背，晚年瘦削 [引用S1]"
    clothing:
      young: "绸衣绸裤，民国公子打扮 [引用S1-era]"
      middle: "粗布短褂，农民打扮 [引用S1-era]"
      old: "破旧棉袄，补丁衣服 [引用S1-era]"
    palette: "棕色系为主，蓝色为辅 [引用S1]"
  expression_normal: "平静温和，偶尔苦笑 [引用S1]"
  expression_strong: "悲痛时沉默，愤怒时握拳不语 [引用S1]"
  constraints:
    - "禁止画年轻时有皱纹 [S1禁止规则]"
    - "禁止画民国后的发型和服装 [S1-era]"
    - "禁止画现代眼镜 [S1-era]"
  reference_prompt: |
    [生成角色参考图的完整提示词，必须包含:]
    - S1 风格规范: [引用颜色/光线/构图规则]
    - 角色DNA visual字段全部内容
    - 角色专属色板
    - 禁止项遵守声明
    格式: "写实风格，1940年代中国农村，[角色描述]，[服装]，[光线]，[禁止项]"
  used_in_scenes: [scene_maowu, scene_tianjian, scene_chengli]
```

## 输出内容：场景 DNA（每个场景一条）

```yaml
scene_maowu:
  id: scene_maowu
  name: 茅屋
  era: "1940年代中国农村"  # 必须匹配S0
  description: "破旧的土坯茅草屋，家境贫寒的象征"
  visual:
    space_type: indoor
    architecture: "土坯墙，茅草顶，木门木窗，无玻璃"
    lighting: "自然光从门缝/窗缝透入，昏暗为主"
    color_temperature: warm
    key_props: ["破旧木桌", "土炕", "油灯"]
  constraints:
    - "禁止出现钢筋水泥"
    - "禁止出现玻璃窗"
    - "禁止出现塑料制品"
  reference_prompt: |
    [生成场景参考图的完整提示词，必须包含:]
    - S1 风格规范
    - 场景DNA visual字段全部内容
    - 时代特征物品
    - 禁止项遵守声明
```

## 输出内容：道具 DNA（关键道具一条）

```yaml
item_yuanbao:
  id: item_yuanbao
  name: 元宝/赌资
  era: "1940年代"
  description: "福贵赌博时使用的银元"
  visual:
    material: "银质/镀银"
    color: "银色光泽"
    size: "直径约3cm"
  constraints:
    - "禁止出现现代硬币"
    - "禁止出现银行卡"
  reference_prompt: "[生成道具参考图的完整提示词]"
```

## 约束

- 每条角色记录必须引用 S1 风格指南的版本号
- constraints 禁止项至少2条
- reference_prompt 必须包含 S1 规范和 S2 DNA 字段
- used_in_scenes 引用场景 DNA ID
