# S2: CDP 资产包 — 格子间女人

> **风格指南版本**: v1.0.0
> **引用来源**: S0-解析报告.md, S1-风格指南.md

---

## 角色 DNA

### char_tanbin — 谭斌

```yaml
id: char_tanbin
name: 谭斌
gender: female
age_range: "28-32岁"
visual:
  face_shape: "鹅蛋脸，轮廓分明，干练气质 [引用S1]"
  skin_tone: "白皙，日常妆容精致但不浓艳 [引用S1]"
  eye_features: "眼神坚定有神，工作时锐利，私下柔和 [引用S1]"
  body_type: "身材修长，结实，腰腹无赘肉（常年跑步） [引用S1]"
  clothing:
    young: "深蓝色职业套装，白衬衫，干练优雅 [引用S1-era]"
    middle: "便装/居家服，卸下职业武装后柔软 [引用S1-era]"
    old: "N/A（主线在青年期）"
    palette: "冷灰+深蓝为主，红色点缀（口红/配饰） [引用S1]"
expression_normal: "职业微笑，控制情绪，不露破绽 [引用S1]"
expression_strong: "眼神坚定，嘴唇紧抿，危机中保持冷静 [引用S1]"
constraints:
  - "禁止网红锥子脸/过度美颜 [S1禁止规则]"
  - "禁止浓妆艳抹（不符合职场定位） [S1-era]"
  - "禁止穿着不符合时代的服装 [S1-era]"
reference_prompt: |
  写实都市风格，2000年代北京CBD，28岁职场女性，
  深蓝色职业套装，白衬衫，鹅蛋脸轮廓，眼神坚定，
  银灰色写字楼背景，自然光+室内灯光，冷色调为主，
  禁止：网红脸/赛博朋克光效/古装元素
used_in_scenes:
  - scene_mpl_office
  - scene_parking_lot
  - scene_china_world_hotel
  - scene_thai_restaurant
  - scene_india_kitchen
  - scene_wangjing
  - scene_subway
```

### char_chengruimin — 程睿敏

```yaml
id: char_chengruimin
name: 程睿敏（Ray/程帅）
gender: male
age_range: "35-40岁"
visual:
  face_shape: "长脸，书卷气质，面容温和但疲惫 [引用S1]"
  skin_tone: "白皙略显苍白（长期高压工作） [引用S1]"
  eye_features: "眼神深邃，被解雇后空洞绝望 [引用S1]"
  body_type: "身段高挑挺拔，深色西装熨帖合身 [引用S1]"
  clothing:
    young: "深色西装，白衬衫，领带，精英形象 [引用S1-era]"
    middle: "西装揉皱，失态时的狼狈 [引用S1-era]"
    old: "N/A"
    palette: "深灰/藏青/黑色，象征职场沉浮 [引用S1]"
expression_normal: "神采奕奕，神情专注，态度温和 [引用S1]"
expression_strong: "面如死灰，嘴角却有奇特笑意，悲壮决绝 [引用S1]"
constraints:
  - "禁止年轻化（他是职场老将） [S1-era]"
  - "禁止时尚潮流打扮（他是传统职场精英） [S1-era]"
reference_prompt: |
  写实都市风格，2000年代北京CBD，38岁职场男性高管，
  深灰色西装，白衬衫，深色领带，身形高挑挺拔，
  长脸书卷气质，眼神深邃略带疲惫，
  昏暗的地下停车场背景，暖黄色灯光，
  冷色调为主，禁止：时尚潮流/古装/赛博朋克
used_in_scenes:
  - scene_mpl_office
  - scene_parking_lot
```

### char_shenpei — 沈培

```yaml
id: char_shenpei
name: 沈培
gender: male
age_range: "26-30岁"
visual:
  face_shape: "清秀，书生气质，天真浪漫 [引用S1]"
  skin_tone: "健康小麦色（常户外写生） [引用S1]"
  eye_features: "眼神纯粹，有艺术家气质 [引用S1]"
  body_type: "修长，穿搭有品味，中式服装加分 [引用S1]"
  clothing:
    young: "剪裁合身的中式上衣，儒雅气质 [引用S1-era]"
    middle: "日常休闲装，随性自然 [引用S1-era]"
    palette: "暖色系，米白/浅灰/靛蓝 [引用S1]"
expression_normal: "温暖笑容，天真浪漫，不谙世事 [引用S1]"
expression_strong: "专注画画时的投入，忽略周围 [引用S1]"
constraints:
  - "禁止邋遢（他有品味） [S1-era]"
  - "禁止潮流前卫（他是文艺气质） [S1-era]"
reference_prompt: |
  写实都市风格，2000年代北京，28岁青年画家，
  剪裁合身中式上衣，清秀书卷气，眼神温暖纯粹，
  路灯柠黄色光晕，街头场景，
  暖色调为主，禁止：潮流前卫/古装/滤镜过度
used_in_scenes:
  - scene_india_kitchen
```

### char_wenxiaohui — 文晓慧

```yaml
id: char_wenxiaohui
name: 文晓慧
gender: female
age_range: "28-32岁"
visual:
  face_shape: "精致冷艳，网红锥子脸No（她是真实自然美） [引用S1]"
  skin_tone: "白皙，精致妆容 [引用S1]"
  eye_features: "眼神锐利，毒舌闺蜜 [引用S1]"
  body_type: "玲珑有致，身姿曼妙 [引用S1]"
  clothing:
    young: "贴身短套装，冷艳冰蓝色，紧裹身材 [引用S1-era]"
    palette: "冰蓝/银白，冷艳高冷 [引用S1]"
expression_normal: "妩媚性感，毒舌犀利 [引用S1]"
expression_strong: "大笑时不顾形象，真性情 [引用S1]"
constraints:
  - "禁止过度暴露（她是冷艳不是风尘） [S1-era]"
  - "禁止网红脸（她是自然精致） [S1禁止规则]"
reference_prompt: |
  写实都市风格，2000年代北京，30岁职场女性，
  冰蓝色贴身短套装，冷艳精致妆容，
  泰国餐厅背景热带风情，银白色调为主，
  禁止：网红脸/过度暴露/古装/赛博朋克
used_in_scenes:
  - scene_thai_restaurant
```

---

## 场景 DNA

### scene_mpl_office — MPL大厦

```yaml
id: scene_mpl_office
name: MPL大厦
era: "2000年代北京CBD"
description: "外资IT公司写字楼，格子间办公区，职场战场"
visual:
  space_type: indoor
  architecture: "现代写字楼，落地窗，格子间工位，19层高管区 [引用S1-era]"
  lighting: "日光灯+自然光，银白色调，冷灰工作环境 [引用S1]"
  color_temperature: cool
  key_props:
    - "电脑屏幕（CRT/早期LCD）"
    - "Outlook浮动窗口"
    - "实体名片"
    - "星巴克纸杯"
constraints:
  - "禁止出现智能手机（iPhone4以后） [S1-era]"
  - "禁止现代简约风（2000年代感） [S1-era]"
  - "禁止过新的装修（要有年代感） [S1-era]"
reference_prompt: |
  写实都市风格，2000年代北京CBD写字楼，
  格子间办公区，落地窗，银白色日光灯，
  员工埋头工作，冷灰色调，
  禁止：现代简约风/智能手机/扫码支付
```

### scene_parking_lot — 地下停车场

```yaml
id: scene_parking_lot
name: 地下停车场
era: "2000年代"
description: "MPL大厦地下停车场，程睿敏被解雇后失魂落魄之地"
visual:
  space_type: semi_indoor
  architecture: "混凝土柱子，停车位，车道 [引用S1-era]"
  lighting: "昏暗的暖黄色灯光，水泥地面 [引用S1]"
  color_temperature: warm
  key_props:
    - "深灰色沃尔沃S60"
    - "昏暗灯光"
    - "混凝土柱子"
constraints:
  - "禁止过亮（这是灰暗情绪场景） [S1-era]"
  - "禁止出现监控探头特写 [S1-era]"
reference_prompt: |
  写实风格，2000年代北京CBD地下停车场，
  昏暗暖黄色灯光，混凝土柱子，
  深灰色沃尔沃停放，昏暗氛围，
  冷暖对比色调，禁止：过亮/现代监控
```

### scene_china_world_hotel — 中国大饭店

```yaml
id: scene_china_world_hotel
name: 中国大饭店
era: "2000年代"
description: "国贸地区五星级酒店，谭斌召开客户会议场所"
visual:
  space_type: semi_indoor
  architecture: "五星级酒店大堂/会议室，豪华但不过度 [引用S1-era]"
  lighting: "自然光+水晶灯，暖色为主 [引用S1]"
  color_temperature: warm
  key_props:
    - "PPT投影屏"
    - "酒店会议桌"
    - "客户座位"
constraints:
  - "禁止过于奢华（是商务会议非婚礼） [S1-era]"
  - "禁止出现现代电子设备 [S1-era]"
reference_prompt: |
  写实风格，2000年代北京国贸五星级酒店会议厅，
  落地窗自然光，水晶吊灯，
  商务会议场景，专业但不奢华，
  暖色调，禁止：过度奢华/智能手机
```

### scene_thai_restaurant — 泰国餐厅

```yaml
id: scene_thai_restaurant
name: 泰国餐厅
era: "2000年代"
description: "CBD周边泰国餐厅，谭斌与文晓慧午餐聚会"
visual:
  space_type: indoor
  architecture: "异国风情泰国餐厅，热带装饰 [引用S1-era]"
  lighting: "暖黄色灯光，热带风情 [引用S1]"
  color_temperature: warm
  key_props:
    - "青花细瓷餐具"
    - "泰国菜（青木瓜沙拉）"
    - "冰水杯"
constraints:
  - "禁止泰文标识过多（要像国内泰国餐厅） [S1-era]"
  - "禁止ins风装修 [S1-era]"
reference_prompt: |
  写实风格，2000年代北京CBD周边泰国餐厅，
  暖黄色灯光，热带装饰画，青花瓷餐具，
  两职场女性对话场景，温馨闺蜜氛围，
  暖色调，禁止：ins风/过于异域
```

### scene_india_kitchen — 印度小厨

```yaml
id: scene_india_kitchen
name: 印度小厨
era: "2000年代"
description: "普通印度餐厅，沈培带谭斌吃饭的地方"
visual:
  space_type: indoor
  architecture: "普通餐厅规模，印度音乐氛围 [引用S1-era]"
  lighting: "昏黄灯光，印度风情 [引用S1]"
  color_temperature: warm
  key_props:
    - "咖喱拌饭"
    - "印度风格装饰"
    - "红茶杯"
constraints:
  - "禁止高档装修（这是平民餐厅） [S1-era]"
reference_prompt: |
  写实风格，2000年代北京普通印度餐厅，
  昏黄灯光，印度背景音乐（笛声），
  普通餐桌，咖喱饭，平民氛围，
  暖色调，禁止：高档装修/现代元素
```

---

## 道具 DNA

### item_laptop — 笔记本电脑

```yaml
id: item_laptop
name: 笔记本电脑
era: "2000年代"
description: "MPL员工办公笔记本电脑，IBM/Lenovo风格"
visual:
  material: "银灰色塑料+金属"
  color: "银灰/黑色"
  size: "14寸，有光驱"
constraints:
  - "禁止超薄本（2000年代还很厚实） [S1-era]"
  - "禁止MacBook（那是后来的） [S1-era]"
reference_prompt: |
  写实风格，2000年代IBM风格笔记本电脑，
  银灰色，厚实机身，有光驱，
  办公桌场景，禁止：MacBook/超薄本/现代设备
```

### item_card — 员工门卡

```yaml
id: item_card
name: 员工门卡
era: "2000年代"
description: "MPL电子门禁卡，解锁权限的象征"
visual:
  material: "塑料+磁条/IC芯片"
  color: "白色+MPL logo"
  size: "名片大小"
constraints:
  - "禁止闪付功能 [S1-era]"
reference_prompt: |
  写实风格，白色塑料门禁卡，
  MPL公司logo，简洁设计，
  特写镜头，禁止：闪付标识/现代芯片
```

---

**下一步**: 进入 S3 资产库，生成图像提示词
