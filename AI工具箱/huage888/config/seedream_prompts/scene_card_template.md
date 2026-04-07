# 场景卡模板 · Seedream Scene Sheet

> 用途：qwen-max 润色填充，生成后存为 assets/library/[场景名]/scene_card.md
> 规则：②③④定稿后锁死，每次出图只改⑤镜头变量

## ① 风格锚点（固定）

```
photorealistic, cinematic photography, detailed interior/exterior scene,
dramatic atmospheric lighting, film grain, 8k resolution,
```

## ② 场景类型（定稿锁死）

```
[scene type, e.g. misty ancient Chinese bridge over a lake],
consistent environment, same location, same spatial layout,
```

## ③ 固定道具与陈设（定稿锁死）

```
[main elements description],
[furniture/props description],
[decorative items description],
[lighting source description],
same props, same furniture arrangement, identical environment,
```

## ④ 地面与墙面材质（定稿锁死）

```
[floor description],
[wall description],
```

## ⑤ 镜头变量（每次出图只改这里）

```
{{SHOT_TYPE}}    # wide establishing shot / medium shot / extreme close-up detail
{{CAMERA_ANGLE}} # eye-level / low angle / high angle / overhead bird's eye
{{FOCUS}}        # focusing on the full scene / specific element
{{LIGHTING}}     # warm golden / cool blue moonlight / mixed candlelight
{{ATMOSPHERE}}   # moody and mysterious / serene / tense and dramatic
```

## ⑥ 人物处理（固定）

```
no characters, empty scene, no people,
```

## ⑦ 质量尾缀（固定）

```
masterpiece, best quality, ultra detailed textures, sharp focus
```

## 默认出图模板（⑤默认填充值）

```
[①风格锚点]
[②场景类型]
[③固定道具陈设]
[④地面墙面材质]
wide establishing shot, eye-level camera,
focusing on the full scene,
morning mist, cool blue moonlight atmosphere,
volumetric light rays, deep shadows,
no characters, empty scene,
[⑦质量尾缀]
```
