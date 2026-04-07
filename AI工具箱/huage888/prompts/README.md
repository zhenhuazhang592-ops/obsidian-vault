# prompts/README.md — Prompt 模板系统

> 统一管理视频生成 Prompt 模板，支持 {{变量}} 占位符渲染

---

## 模板位置

```
prompts/
└── templates/
    ├── character-motion.txt          # 角色动作镜头模板
    ├── cyber-ink-video.txt           # 赛博墨韵完整视频模板
    ├── camera-template.txt           # 运镜 Prompt 库
    ├── mo-mei-character.txt          # 漠玫角色一致性
    ├── sun-wukong-transformations.txt # 大圣三变体
    ├── cyber-bamboo-forest.txt       # 赛博竹林场景
    └── lighting-library.txt           # 光影 Prompt 库
```

## 渲染示例

```bash
# 使用模板
python3 scripts/video_pipeline.py \
  --video --provider doubao \
  --template character-motion \
  --vars "character=漠玫,scene=赛博竹林,action=睁眼" \
  --output /tmp/v001.mp4

# 直接文本
python3 scripts/video_pipeline.py \
  --video --provider doubao \
  --prompt "$(cat prompts/templates/mo-mei-character.txt)" \
  --output /tmp/v001.mp4
```

## 新增模板

在 `prompts/templates/` 下新增 `.txt` 文件即可：

```markdown
# 模板名称
{{variable1}} 在 {{variable2}} 中 {{action}}
光影：{{lighting}}，{{mood}}
```

使用 `--vars "variable1=值1,variable2=值2,action=值3"` 渲染。
