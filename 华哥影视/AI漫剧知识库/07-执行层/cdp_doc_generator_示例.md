---
title: "格子间女人"
version: "1.0"
format: "comic_drama_package"
generated: "2026-03-26"
---

```json
{
  "version": "1.0",
  "format": "comic_drama_package",
  "meta": {
    "runId": "demo-001",
    "append": false,
    "source": {
      "sourceType": "import_chapters",
      "sourceNovelId": "novel_001",
      "sourceNovelTitle": "格子间女人",
      "chapters": [
        { "id": "ch_1", "sortOrder": 1, "title": "第1集：职场暗涌" }
      ]
    }
  },
  "title": "短视频漫剧：格子间女人",
  "settings": {
    "targetPlatform": "抖音",
    "aspectRatio": "9:16",
    "stylePreset": "anime",
    "shotDurationSec": 15,
    "episodeDurationMin": 2
  },
  "characters": [
    {
      "id": "c_c1",
      "name": "谭斌",
      "aliases": ["Cherie", "谭女士", "糖饼"],
      "gender": "female",
      "age": "30-35",
      "appearance": "修长身材，五官精致，面带黑眼圈，表情坚毅",
      "clothing": "深蓝色职业正装，简洁干练，白色衬衫",
      "persona": "坚韧冷静，事业心强，内心敏感，面对职场动荡自我激励"
    },
    {
      "id": "c_c2",
      "name": "程睿敏",
      "aliases": ["Ray", "程总"],
      "gender": "male",
      "age": "35-40",
      "appearance": "高挑，浓眉书卷气，精干帅气，气质儒雅",
      "clothing": "深色西装，领带",
      "persona": "职场精英，沉稳内敛，善于谋略"
    },
    {
      "id": "c_c3",
      "name": "余永麟",
      "aliases": ["Tony"],
      "gender": "male",
      "age": "40-45",
      "appearance": "高大精明，五官轮廓分明",
      "clothing": "商务休闲装",
      "persona": "公司高层，老谋深算"
    }
  ],
  "locations": [
    {
      "id": "l_l1",
      "name": "MPL公司写字楼",
      "description": "现代写字楼，格子间分布，氛围压抑紧张，员工小心翼翼工作",
      "props": ["电脑", "会议桌", "办公椅", "文件柜"]
    },
    {
      "id": "l_l2",
      "name": "停车场地下车库",
      "description": "昏暗灯光下车库，空旷寂静，偶尔有车灯闪烁",
      "props": ["汽车", "门禁", "柱灯"]
    },
    {
      "id": "l_l3",
      "name": "中国大饭店会议室",
      "description": "高档酒店会议室，气氛凝重，落地窗外城市夜景",
      "props": ["长桌", "皮椅", "落地窗", "城市灯光"]
    }
  ],
  "items": [
    {
      "id": "i_i1",
      "name": "邮件通知",
      "description": "指出程睿敏离职的电子邮件，关键转折信息",
      "appearance": "电脑屏幕浮动窗口，简洁英文内容"
    },
    {
      "id": "i_i2",
      "name": "咖啡杯",
      "description": "许斌递给程睿敏的咖啡，象征温暖与关怀",
      "appearance": "白色咖啡杯，简洁设计"
    }
  ],
  "shots": [
    {
      "id": "sh_sh1",
      "shotNumber": 1,
      "durationSec": 15,
      "sourceChapterIds": ["ch_1"],
      "locationId": "l_l1",
      "characterIds": ["c_c1"],
      "itemIds": ["i_i1"],
      "script": "谭斌夜晚独自加班，电脑弹出新邮件通知，她疑惑地打开邮件看到简单的一句话：程睿敏离开公司。",
      "dialogue": [
        { "speakerId": "c_c1", "text": "程睿敏自即日起离开公司？" }
      ],
      "imagePrompt": "办公室夜景，中景拍摄，谭斌紧皱眉头看电脑屏幕，冷色调灯光下电脑界面清晰，都市职场风格",
      "videoPrompt": "中景推镜，谭斌挠头困惑，眼神紧张，手指轻点鼠标，电脑屏幕上邮件弹窗闪烁，氛围压抑",
      "objective": "钩子镜头，制造悬念和冲突，引出核心事件",
      "action": {
        "0-5s": "电脑弹窗出现，谭斌看向屏幕",
        "5-10s": "谭斌皱眉查看邮件内容",
        "10-15s": "表情震惊，镜头微微推近"
      },
      "reference": ""
    },
    {
      "id": "sh_sh2",
      "shotNumber": 2,
      "durationSec": 15,
      "sourceChapterIds": ["ch_1"],
      "locationId": "l_l1",
      "characterIds": ["c_c1", "c_c3"],
      "itemIds": [],
      "script": "谭斌拨通余永麟电话，急切说出消息，对方起初不相信，噪音干扰中两人严肃对话。",
      "dialogue": [
        { "speakerId": "c_c1", "text": "Tony，咱们的大老板Ray要离开公司了" },
        { "speakerId": "c_c3", "text": "什么？你在哪儿？" }
      ],
      "imagePrompt": "办公室内，电话对话，近景捕捉谭斌焦虑神情，电话那头余永麟在家中",
      "videoPrompt": "切换特写谭斌和余永麟，电话线连接画面，余永麟起身走向安静处，情绪升温",
      "objective": "推动剧情，展现谭斌的紧张和职场敏感性",
      "action": {
        "0-5s": "谭斌拨号准备说话",
        "5-10s": "对方断断续续回应",
        "10-15s": "双方情绪紧张，镜头左右交替"
      },
      "reference": ""
    },
    {
      "id": "sh_sh3",
      "shotNumber": 3,
      "durationSec": 15,
      "sourceChapterIds": ["ch_1"],
      "locationId": "l_l2",
      "characterIds": ["c_c2"],
      "itemIds": ["i_i1"],
      "script": "程睿敏清晨尝试进入公司被拒，门卡失效，保安冷漠阻拦，他焦躁又无助，最终只能回车场等待。",
      "dialogue": [
        { "speakerId": "c_c2", "text": "门卡不能用了？" }
      ],
      "imagePrompt": "停车场昏暗灯光下，中景拍摄程睿敏试图刷门卡，面色阴郁，保安站立冷漠",
      "videoPrompt": "固定镜头，慢速推近程睿敏焦躁的手，转向他坚定但无奈的目光，镜头带轻微抖动增加紧张感",
      "objective": "刻画困境，展现程睿敏被边缘化的处境",
      "action": {
        "0-5s": "程睿敏尝试刷门卡多次",
        "5-10s": "与保安短暂对话被拒",
        "10-15s": "无奈转身离开，慢动作"
      },
      "reference": ""
    },
    {
      "id": "sh_sh4",
      "shotNumber": 4,
      "durationSec": 15,
      "sourceChapterIds": ["ch_1"],
      "locationId": "l_l3",
      "characterIds": ["c_c2", "c_c3"],
      "itemIds": [],
      "script": "公司高层办公室内，程睿敏被执行董事长余永麟召见，气氛凝重，程睿敏脸色苍白，周围员工紧张观望。",
      "dialogue": [],
      "imagePrompt": "写字楼19层办公室全景，余永麟与程睿敏对话，员工墙边观望，气氛压抑",
      "videoPrompt": "推镜全景转特写，气氛沉重压抑，程睿敏脸色苍白缓缓转头，背景员工窃窃私语",
      "objective": "权力游戏，展现高层博弈",
      "action": {
        "0-5s": "程睿敏被带进办公室",
        "5-10s": "员工偷看议论",
        "10-15s": "程睿敏神色变化，慢镜头肖像"
      },
      "reference": ""
    },
    {
      "id": "sh_sh5",
      "shotNumber": 5,
      "durationSec": 15,
      "sourceChapterIds": ["ch_1"],
      "locationId": "l_l2",
      "characterIds": ["c_c1", "c_c2"],
      "itemIds": ["i_i2"],
      "script": "傍晚，谭斌在地下停车场遇见跌坐无力的程睿敏，主动上前帮忙开车门，并递交咖啡，两人手指触碰流露微妙情绪。",
      "dialogue": [
        { "speakerId": "c_c1", "text": "程帅，要我帮忙吗？" },
        { "speakerId": "c_c2", "text": "谢谢……" }
      ],
      "imagePrompt": "昏暗车库中景，谭斌轻扳车门，程睿敏疲惫坐车内，手指轻触咖啡杯，光线柔和",
      "videoPrompt": "慢推特写两人手指接触，手势细腻传达内心冰冷与温暖交织，背景暗部细节模糊处理",
      "objective": "情感细节，展现两人微妙关系变化",
      "action": {
        "0-5s": "谭斌伸手开车门",
        "5-10s": "递咖啡杯",
        "10-15s": "两手指轻触，光影切换"
      },
      "reference": ""
    }
  ]
}
```
