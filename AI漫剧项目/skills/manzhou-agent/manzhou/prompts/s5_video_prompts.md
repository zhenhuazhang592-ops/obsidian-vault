# S5: 视频生成（双平台提示词）

## 任务

基于 S4 分镜脚本，生成 Kling 和 Seedance 双版本的视频生成提示词。

## 输入

- S0-解析报告.md
- S1-风格指南.md
- S2-CDP资产包/CDP-JSON.md
- 03-分镜脚本/分镜脚本总览.md
- 03-分镜脚本/第XX集-分镜脚本.md

## 输出文件

- `04-视频生成/视频生成任务清单.md`

## 引用声明

```yaml
引用声明:
  上游步骤: S1-风格指南.md, S2-CDP资产包/CDP-JSON.md, 03-分镜脚本/分镜脚本总览.md
  引用ID列表: [char_xxx, scene_xxx, item_xxx]
  风格指南版本: [v1.0.0]
```

## 输出内容：视频生成任务清单

```yaml
视频生成任务清单:
  project_name: [项目名]
  total_episodes: [总集数]
  total_shots: [总镜头数]
  platform: [Kling / Seedance]

  tasks:
    - episode: 01
      shots:
        - shot_id: SHOT_01
          duration: X秒
          kling_prompt: |
            [Kling 平台视频生成提示词，包含:]
            - 画面描述（引用 S4 分镜脚本）
            - 角色描述（引用 S2 角色DNA）
            - 场景描述（引用 S2 场景DNA）
            - 运动描述（引用 S4 运镜规范）
            - S1 风格规范约束
          seedance_prompt: |
            [Seedance 平台视频生成提示词，同上格式]
          reference_images:
            - "[角色参考图路径]"
            - "[场景参考图路径]"
          negative_prompt: |
            [负面提示词，引用 S1 prohibition]
          seed: [随机种子，可留空]
```

## Kling 提示词规范

```
[主体描述], [场景环境], [时间/光线], [摄影机运动],
[画面风格], [氛围], [质量修饰词]
Negative: [S1禁止项]
```

## Seedance 提示词规范

```
[主体描述], [动作/表情], [场景], [光线],
[角度], [构图], [风格标签]
Negative: [S1禁止项]
```

## 约束

- 每个镜头生成 Kling 和 Seedance 两个版本的提示词
- 提示词必须引用上游 S1/S2/S4 的具体字段
- 负面提示词必须包含 S1 的所有 prohibition 项
- 时长必须与 S4 分镜脚本一致
- 必须指定参考图路径（引用 S3 资产库）
