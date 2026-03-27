# S1: 全局设置（规范锚点）

## 任务

基于 S0 解析报告，生成全局风格指南。这是全链路的规范锚点，后续所有步骤必须引用。

## 输入

- S0-解析报告.md

## 输出文件

- `00-项目信息/全局设置.md`
- `S1-风格指南.md`

## 引用声明

```yaml
引用声明:
  上游步骤: S0-解析报告.md
  引用ID列表: []
  风格指南版本: v1.0.0
```

## 输出内容：全局设置

```yaml
项目名: [从小说名提取]
原作: [小说名]
作者: [作者名]

全局配置:
  style: [写实/动漫/水墨/漫画风]
  aspect_ratio: "9:16"
  shot_duration_sec: 15
  total_eps: [集数]
  total_shots: [估算总镜头数]

统计:
  characters: [角色数量]
  scenes: [场景数量]
  episodes: [集数]
```

## 输出内容：风格指南（必须完整）

```yaml
style_guide:
  version: "v1.0.0"  # 固定格式，后续引用此版本

  color_palette:
    dominant: [主色调描述，如"暖黄色，如1930年代老照片"]
    secondary: [辅助色描述]
    accent: [点缀色描述]
    prohibition: [禁用色列表]

  lighting_rules:
    type: [natural/hard/soft/mixed]
    time_of_day: [如"自然光为主，室内用暖色灯光"]
    prohibition:
      - [如"禁止霓虹灯效果"]
      - [如"禁止现代补光设备"]

  camera_rules:
    standard_lens: [标准镜头，如"中景镜头为主"]
    movement_patterns:
      - [如"横移用于场景转换"]
      - [如"推镜头用于强调"]
    prohibition:
      - [如"禁止快速摇镜"]
      - [如"禁止航拍俯冲"]

  sound_rules:
    bgm_style: [如"忧伤的小提琴配乐，节奏缓慢"]
    sfx_types: [音效类型列表]
    prohibition:
      - [如"禁止电子音乐"]

  character_design_rules:
    proportions: [如"写实比例，接近真人"]
    prohibition:
      - [如"禁止日漫大眼"]
      - [如"禁止网红脸"]

  era_constraints:
    allowed_eras: [[1940s, 1960s]]
    prohibition:
      - [如"禁止出现塑料制品"]
      - [如"禁止水泥地面"]
      - [如"禁止钢筋混凝土建筑"]
```

## 约束

- 这是规范锚点，后续所有步骤必须引用 `style_guide.version`
- 所有规则必须具体，不能写"视情况而定"
- prohibition 列表至少3条，针对具体禁止项
