# S3: 资产库（图像生成层）

## 任务

基于 S2 CDP 资产包，生成角色参考图和场景参考图的 AI 图像生成提示词。

## 输入

- S0-解析报告.md
- S1-风格指南.md
- S2-风格指南.md
- 01-CDP资产包/CDP-JSON.md

## 输出文件

- `02-资产库/生成任务表.md`
- `02-资产库/角色资产.md`
- `02-资产库/场景资产.md`

## 引用声明

```yaml
引用声明:
  上游步骤: S0-解析报告.md, S1-风格指南.md, S2-CDP资产包/CDP-JSON.md
  引用ID列表: [char_xxx, scene_xxx, item_xxx]
  风格指南版本: [v1.0.0]
```

## 输出内容：角色参考图任务

```yaml
角色参考图生成任务:
  - char_id: char_fugui
    name: 福贵
    life_stages:
      - stage: young
        age: "20-25岁"
        reference_prompt: |
          [完整的图像生成提示词，包含:]
          - S1 风格规范（颜色/光线/构图）
          - S2 角色DNA visual字段
          - S2 角色 constraints
          - 时代特征
      - stage: middle
        age: "40-50岁"
        reference_prompt: |
          [同上格式]
      - stage: old
        age: "60-70岁"
        reference_prompt: |
          [同上格式]
```

## 输出内容：场景参考图任务

```yaml
场景参考图生成任务:
  - scene_id: scene_maowu
    name: 茅屋
    reference_prompt: |
      [完整的图像生成提示词，包含:]
      - S1 风格规范
      - S2 场景DNA visual字段
      - S2 场景 constraints
    color_reference: "[场景主色调建议]"
```

## 约束

- 每条提示词必须引用 S1 和 S2 的具体字段
- 提示词格式统一：中文描述 + 英文关键词
- 必须包含禁止项遵守声明
- 场景图需包含多个角度建议
