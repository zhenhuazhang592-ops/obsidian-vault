# 角色卡模板 · Seedream Character Sheet

> 用途：qwen-max 润色填充，生成后存为 assets/library/[角色名]/character_card.md
> 规则：②③④定稿后锁死，每次出图只改⑤镜头变量

## ① 风格锚点（固定）

```
3D render style, ancient Chinese fantasy, cinematic quality, ultra detailed,
sharp focus, photorealistic skin texture, rich fabric detail,
```

## ② 外貌核心（定稿锁死）

```
1 woman, [age description],
[face features: oval face, almond-shaped eyes, lip color, skin tone],
Taoist bun hair, [hairpin style description],
golden pupils with flowing data streams,
blue ink brushstroke eyeliner,
same face, consistent character, identical facial features,
```

## ③ 服装细节（定稿锁死）

```
[outer robe: color + material + pattern description],
[inner garment: color + style description],
[skirt: color + gradient description],
[waist belt: color + decoration description],
same costume, identical clothing,
```

## ④ 饰品细节（定稿锁死）

```
[headdress description],
[hairpin description],
[earrings/necklace description],
same accessories,
```

## ⑤ 镜头变量（每次出图只改这里）

```
{{VIEW}}         # front view / side view / back view / three-quarter view
{{SHOT}}         # full body / upper body / close-up face
{{EXPRESSION}}   # calm / happy smile / shocked / furious / shy
{{POSE}}         # standing elegantly / sitting / turning / walking
{{BACKGROUND}}   # white studio / ancient bridge / cyber dojo
```

## ⑥ 质量尾缀（固定）

```
masterpiece, best quality, 8k resolution, professional lighting
```

## 默认出图模板（⑤默认填充值）

```
[①风格锚点]
[②外貌核心]
[③服装细节]
[④饰品细节]
front view, full body, calm, standing elegantly,
white studio background,
[⑥质量尾缀]
```
