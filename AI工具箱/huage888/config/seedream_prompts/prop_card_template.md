# 道具卡模板 · Seedream Prop Sheet

> 用途：qwen-max 润色填充，生成后存为 assets/library/[道具名]/prop_card.md
> 规则：②③④⑤定稿后锁死，每次出图只改⑥镜头变量

## ① 风格锚点（固定）

```
product visualization, photorealistic, ultra detailed, 8k resolution,
studio lighting, white background, isolated object, no shadows,
```

## ② 道具基础定义（定稿锁死）

```
1 single prop, [prop category, e.g. ancient Chinese jade token],
consistent prop design, same object, identical details,
```

## ③ 材质与颜色（定稿锁死）

```
[primary material, e.g. aged bronze with natural patina],
[color palette],
[surface texture description],
```

## ④ 结构细节（定稿锁死）

```
[overall shape description],
[base description],
[decorative elements description],
[functional parts description],
```

## ⑤ 尺寸比例感（定稿锁死）

```
[approximately Xcm tall, proportions description],
```

## ⑥ 镜头变量（每次出图只改这里）

```
{{ANGLE}}   # front view / side view / three-quarter view / top-down
{{SHOT}}    # full object / upper half / close-up detail of element
```

## ⑦ 质量尾缀（固定）

```
masterpiece, best quality, sharp focus, clean background
```

## 默认出图模板（⑥默认填充值）

```
[①风格锚点]
[②道具基础定义]
[③材质颜色]
[④结构细节]
[⑤尺寸比例感]
three-quarter view, full object,
[⑦质量尾缀]
```
