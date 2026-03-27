# 第1集 - SFX音效标注表

> 项目名：格子间女人
> 集数：第1集 / 共12集
> 本集主题：雨夜惊变 - 程睿敏突然出局

---

## SFX六维参数规范

每条SFX标注包含：
- **Type**：环境音(EV) / 动效(FX) / 界面音(UI) / 音乐(MUSIC)
- **Source**：现实采集 / 合成器 / 资料库
- **Position**：左(L) / 中(C) / 右(R) / 环绕(SUR)
- **Time**：出现时间点
- **Duration**：持续时长
- **Mix Level**：混音电平（dB，相对于对话）

---

## 逐镜头SFX标注

### 镜头 01/01 【环境建立】

| 参数 | 值 |
|------|-----|
| Type | EV（环境音）|
| Description | 北京CBD都市夜声：远处车流、空调外机、深夜城市白噪音 |
| Source | 资料库（北京城市环境音，shutterstock/soundjay）|
| Position | SUR（环绕，主导）|
| Time | 0:00 |
| Duration | 0:03（持续至01:02）|
| Mix Level | -18dB（极轻背景）|

---

### 镜头 01/02 【键盘敲击】

| 参数 | 值 |
|------|-----|
| Type | FX（动效）|
| Description | 机械键盘敲击声，节奏规律，每秒约4次 |
| Source | 合成器/资料库（机械键盘SoundEffect）|
| Position | C（居中）|
| Time | 0:03 |
| Duration | 持续（0:03-0:15）|
| Mix Level | -6dB（主导声音）|
| 备注 | 需节奏均匀，不可有打字机效果 |

---

### 镜头 01/03 【邮件提示音】

| 参数 | 值 |
|------|-----|
| Type | UI（界面音）|
| Description | 电脑邮件提示音，轻微"叮"声 |
| Source | 系统音效/资料库 |
| Position | C |
| Time | 0:15 |
| Duration | 0.5秒 |
| Mix Level | -3dB（清晰但不刺耳）|
| 备注 | 参考Mac邮件提示音 |

---

### 镜头 01/04 【键盘继续】

| 参数 | 值 |
|------|-----|
| Type | FX（动效）|
| Description | 键盘敲击（继续01:02）|
| Position | C |
| Time | 0:15 |
| Duration | 持续至0:20 |
| Mix Level | -9dB（让位给VO）|

---

### 镜头 01/05 【旁白+键盘停止】

| 参数 | 值 |
|------|-----|
| Type | FX（动效）|
| Description | 键盘敲击声渐弱消失（最后几声，然后停止）|
| Position | C |
| Time | 0:20 |
| Duration | 0:05（渐弱）|
| Mix Level | -12dB渐弱 |
| 备注 | 为旁白让路 |

---

### 镜头 01/07-01/09 【情绪爆发段】

| 参数 | 值 |
|------|-----|
| Type | EV + FX |
| Description | 环境音突然消失，制造"世界停止"的听觉真空 |
| Position | C（突然消失）|
| Time | 0:45 |
| Duration | 2秒（完全静默）|
| Mix Level | -∞（完全切除）|
| 备注 | **核心音效设计**：用"无声音"制造震惊感 |

---

### 镜头 01/08 【心跳音效】（情绪引爆）

| 参数 | 值 |
|------|-----|
| Type | FX（动效）|
| Description | 心脏跳动声，低沉有力，渐强 |
| Source | 资料库（heartbeat sound effect）|
| Position | C |
| Time | 0:50 |
| Duration | 1.5秒 |
| Mix Level | -6dB（渐强）|
| 备注 | 配合邮件揭示画面，制造冲击感 |

---

### 镜头 01/10 【城市夜声回归】

| 参数 | 值 |
|------|-----|
| Type | EV（环境音）|
| Description | 城市夜声渐回：远处车流、风声 |
| Source | 资料库 |
| Position | SUR |
| Time | 1:05 |
| Duration | 持续 |
| Mix Level | -15dB（淡入）|
| 备注 | 与01/01呼应 |

---

### 镜头 01/14 【电话场景环境】

| 参数 | 值 |
|------|-----|
| Type | EV（环境音）|
| Description | 电视嘈杂背景音（综艺节目/电视剧声），家庭客厅感 |
| Source | 合成器/资料库 |
| Position | SUR（背景）|
| Time | 1:30 |
| Duration | 持续至1:45 |
| Mix Level | -15dB（背景）|
| 备注 | 余永麟在家中，暗示其家庭生活 |

---

### 镜头 01/14 【电话拨出音】

| 参数 | 值 |
|------|-----|
| Type | UI（界面音）|
| Description | 手机拨出音，短促"滴——" |
| Source | 合成器 |
| Position | C |
| Time | 1:25 |
| Duration | 0.3秒 |
| Mix Level | -3dB |

---

### 镜头 01/16 【电视突然安静】

| 参数 | 值 |
|------|-----|
| Type | EV（环境音）|
| Description | 电视声突然降低（余永麟换房间）|
| Position | SUR |
| Time | 1:42 |
| Duration | 0.5秒 |
| Mix Level | -30dB（突然压低）|
| 备注 | 为01/17 TanBin严肃台词铺垫 |

---

### 镜头 01/17 【电话场景】

| 参数 | 值 |
|------|-----|
| Type | FX（动效）|
| Description | 脚步声（余永麟走向书房/关门声）|
| Source | 合成器 |
| Position | L/R |
| Time | 1:43 |
| Duration | 0.5秒 |
| Mix Level | -6dB |

---

### 镜头 01/20 【手机跌落】

| 参数 | 值 |
|------|-----|
| Type | FX（动效）|
| Description | 手机跌落在皮质沙发上的冲击声 + 轻微弹起 |
| Source | 合成器/资料库 |
| Position | C |
| Time | 2:20 |
| Duration | 0.5秒 |
| Mix Level | 0dB（强音效，本集最大SFX峰值）|
| 备注 | **本集SFX高潮点** |

---

### 镜头 01/22 【断点钩子】

| 参数 | 值 |
|------|-----|
| Type | EV（环境音）|
| Description | 城市夜声极轻持续，模拟深夜 |
| Position | SUR |
| Time | 3:40 |
| Duration | 持续至结束 |
| Mix Level | -24dB（极轻）|
| 备注 | 完全静默后留极轻城市夜声，制造悬念 |

---

## SFX制作清单

| 编号 | 名称 | 类型 | 时长 | 备注 |
|------|------|------|------|------|
| SFX-01 | 都市夜环境 | EV | 0:30 | 循环，可拼接 |
| SFX-02 | 机械键盘 | FX | 0:20 | 规律节奏 |
| SFX-03 | 邮件提示音 | UI | 0.3秒 | 参考Mac |
| SFX-04 | 心脏跳动 | FX | 1.5秒 | 渐强版 |
| SFX-05 | 电视背景 | EV | 0:30 | 循环 |
| SFX-06 | 电话拨出 | UI | 0.3秒 | 标准 |
| SFX-07 | 脚步+关门 | FX | 0.5秒 | 室内 |
| SFX-08 | 手机跌落 | FX | 0.5秒 | 皮革冲击 |
| SFX-09 | 城市深夜 | EV | 0:20 | 极轻循环 |

---

## 推荐SFX资源库

| 资源 | 用途 |
|------|------|
| freesound.org | 键盘声、心跳声、脚步声 |
| zapsplat.com | 界面音、冲击音效 |
| shutterstock.com | 城市环境音（北京）|
| 哔哔词典 (bibiget.com) | 中文TTS旁白 |
