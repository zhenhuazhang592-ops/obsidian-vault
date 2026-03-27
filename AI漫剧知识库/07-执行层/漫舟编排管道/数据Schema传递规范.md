# 漫舟数据Schema传递规范

> **定位**：Step-to-Step数据契约，定义每步的输入Schema和输出Schema
> **原则**：上游输出的字段 = 下游输入的字段，字段名一一对应
> **评级**：A级
> **维护**：随SOP文件同步更新
> **版本**：v1.0.0 | 2026-03-26

---

## 数据传递总图

```
Step0 ──────────────────────────────────────────────────────────────── Step11
│                                                                      │
│  novel_raw ──→ Step1 ──→ adapted_chapters ──→ Step2 ──→ IP档案 ──→ Step3
│                                                              │
│  project_config ───────────────────────────────→ 标准化剧本 ──→ Step4
│                                                              │
│  导演控制塔 ───────────────────────────────────────────────→ 分镜脚本
│                                                              │
│  char_DNA ──→ Step5 ──→ 资产库（角色DNA/场景图/道具图） ──→ Step6 ──→ 分镜脚本
│                 │                                                    │
│                 └─────────────────────────────────────────────────────┘
│                                                                      │
│  分镜脚本 ──→ Step7 ──→ 角色参考图+场景氛围图 ──→ Step8 ──→ 视频片段
│                                                                      │
│  分镜脚本（Audio Layer） ──→ Step9 ──→ TTS+BGM+SFX ──────────────────┘
│                                                                      │
│  视频片段 + 音频轨道 ──→ Step10 ──→ 成片MP4 ──→ Step11（风控） ──→ 发布
```

### 关键传递字段一览

| 传递路径 | 关键字段 | 锚点ID |
|---------|---------|--------|
| Step0 → Step1 | `novel_raw`, `project_id` | — |
| Step1 → Step2 | `adapted_chapters`, `character_list`, `location_list` | char_XX, loc_XX |
| Step2 → Step3 | `ip_profile`（含char/loc/item档案） | char_XX, loc_XX, item_XX |
| Step3 → Step4 | `script_scenes`, `emotion_curve`, `beat_position` | char_XX, loc_XX |
| Step4 → Step6 | `director_intent`, `camera_action`, `emotion_curve`, `axis_constraint` | — |
| Step5 → Step6 | `char_dna`（外貌锁/风格锁/行为锁）, `scene_assets`, `item_assets` | char_XX, loc_XX, item_XX |
| Step6 → Step7 | `image_prompt`（含char_XX引用）, `shot_duration`, `shot_emotion` | char_XX, loc_XX |
| Step6 → Step8 | `video_prompt`（含char_XX引用+运镜指令）, `Audio_Layer` | char_XX, loc_XX |
| Step6 → Step9 | `Audio_Layer`（TTS/BGM/SFX标注） | — |
| Step7 → Step8 | `char_ref_images`（OSS URL）, `scene_ref_images`（OSS URL） | — |
| Step8 → Step10 | `video_segments`（OSS URL列表）, `shot_timings` | — |
| Step9 → Step10 | `tts_track`, `bgm_track`, `sfx_track`（OSS URL） | — |
| Step10 → Step11 | `final_video_url`, `export_config`, `srt_subtitle` | — |

---

## 每步输入/输出Schema

---

### Step 0 → Step 1

#### Step 1 输入Schema

```json
{
  "project_id": "string（项目唯一ID，格式：proj_XXXX）",
  "project_name": "string（项目/小说名称）",
  "project_type": "string（都市职场/古风/甜宠/悬疑/复仇/其他）",
  "target_platform": "string（抖音/快手/视频号/其他）",
  "style_preset": "string（16种预设之一，见下方）",
  "aspect_ratio": "string（9:16竖屏 / 16:9横屏）",
  "shot_duration": "number（单镜头秒数：8/10/15）",
  "target_episodes": "number（目标集数：6/12/24）",
  "main_view_char": "string（主视角角色ID，如char_01）",
  "budget_estimate": "string（预算估算）",
  "production_cycle": "string（制作周期）",
  "novel_raw": "string（原始小说全文，不含Step0输出内容）"
}
```

**style_preset 枚举值**：

| ID | 名称 |
|----|------|
| ShortDrama_Style | 短剧爽感 |
| Villeneuve_Style | 史诗科幻 |
| WongKarwai_Style | 情绪港风 |
| SciFiWasteland_Style | 废土科幻 |
| ChinesePeriod_Style | 古风国潮 |
| anime | 日漫 |
| cn_anime | 国风动漫 |
| cn_3d | 国风3D |
| ink | 水墨国风 |
| cyber | 赛博朋克 |
| us_comics | 美漫 |
| real | 写实 |
| horror | 恐怖惊悚 |
| pixar | 皮克斯 |
| shinkai | 新海诚 |
| miyazaki | 宫崎骏 |

#### Step 1 输出Schema（= Step 2 输入）

```json
{
  "project_id": "string",
  "adaptation_version": "string（v1.0.0）",
  "adaptation_rules_applied": {
    "compression_ratio": "string（30:1）",
    "opening_rule": "string（撞破/打脸/揭穿/威胁）",
    "dialogue_max_chars": "number（15字硬性约束）",
    "emotion_spike_interval": "string（每45秒一个爽点）"
  },
  "adapted_chapters": [
    {
      "chapter_id": "string（如 ch01）",
      "chapter_title": "string",
      "scene_count": "number",
      "total_duration_sec": "number（估算）",
      "scenes": [
        {
          "scene_id": "string（如 ch01_s01）",
          "scene_title": "string",
          "location": "string（如 办公室）",
          "time": "string（如 白天/夜晚）",
          "characters": ["char_01", "char_02"],
          "conflict": "string（核心冲突，一句话）",
          "highlight": "boolean（是否高光/爽点片段）",
          "emotion_spike_at": "string（时间点，如00:30）",
          "opening_hook": "string（开场5秒抓人描述）",
          "dialogue_count": "number",
          "avg_dialogue_chars": "number（须≤15）"
        }
      ]
    }
  ],
  "character_list": [
    {
      "char_id": "string（如 char_01）",
      "name": "string",
      "role_type": "string（主角/反派/配角/工具人）",
      "appearance_summary": "string（外貌摘要，用于后续Step引用）"
    }
  ],
  "location_list": [
    {
      "loc_id": "string（如 loc_01）",
      "name": "string",
      "type": "string（室内/室外/虚拟）",
      "atmosphere_keywords": ["string"]
    }
  ],
  "adaptation_quality_check": {
    "opening_has_conflict": "boolean",
    "all_dialogue_under_15_chars": "boolean",
    "no_inner_monologue": "boolean",
    "emotion_spikes_placed": "number"
  }
}
```

---

### Step 1 → Step 2

#### Step 2 输入Schema

> 即 Step 1 输出Schema（完整传入）

```json
{
  "project_id": "string",
  "adaptation_version": "string",
  "adapted_chapters": [...],
  "character_list": [...],
  "location_list": [...],
  "adaptation_quality_check": {...}
}
```

#### Step 2 输出Schema（= Step 3 输入）

```json
{
  "project_id": "string",
  "ip_profile_version": "string（v1.0.0）",
  "ip_name": "string",
  "ip_type": "string（都市/古风/甜宠等）",
  "characters": {
    "char_XX": {
      "id": "string（char_XX）",
      "name": "string",
      "role_type": "string（主角/反派/配角/工具人）",
      "age_range": "string（如 30-35岁）",
      "aliases": ["string"],
      "appearance": {
        "face": "string（脸型/眉形/眼形/鼻形/嘴形/肤色）",
        "body": "string（身高/体型/仪态）",
        "distinguishing": "string（标志性特征）",
        "hair": "string（发型/发色）"
      },
      "clothing": {
        "daily": "string",
        "work": "string",
        "special": "string"
      },
      "personality": {
        "traits": ["string（3-5个关键词）"],
        "speech": "string（语言风格）",
        "habits": ["string（习惯性动作/表情）"],
        "conflict_style": "string（冲突处理方式）"
      },
      "voice": {
        "timbre": "string（低沉/清脆/沙哑/磁性）",
        "speed": "string（快/中/慢）",
        "accent": "string（口音/方言）"
      },
      "relationships": [
        {
          "target": "char_XX",
          "type": "string（恋人/上司/闺蜜/对手）",
          "tension": "string（核心矛盾点）"
        }
      ]
    }
  },
  "locations": {
    "loc_XX": {
      "id": "string（loc_XX）",
      "name": "string",
      "type": "string（室内/室外/虚拟）",
      "time": "string（白天/夜晚/清晨/黄昏）",
      "weather": "string（晴天/雨天/雪天/室内无天气）",
      "atmosphere": "string（冷/暖/压抑/明快/神秘）",
      "color_temp": "string（冷色/暖色/中性）",
      "lighting": "string（自然光/人工光/混合光）",
      "key_elements": ["string（物品1）", "string（物品2）"],
      "visual_tags": ["string（AI生成标签1）", "string（标签2）"]
    }
  },
  "items": {
    "item_XX": {
      "id": "string（item_XX）",
      "name": "string",
      "type": "string（重要道具/背景道具/功能道具）",
      "owner": "string（所属角色ID，如char_XX）",
      "appearance": "string（外观描述）",
      "symbolic": "string（象征意义）",
      "key_scenes": ["loc_XX", "loc_XX"]
    }
  },
  "relationship_map": {
    "directed_graph": "object（角色关系图，供导演控制塔使用）"
  }
}
```

---

### Step 2 → Step 3

#### Step 3 输入Schema

> 即 Step 2 输出Schema（完整传入）

```json
{
  "project_id": "string",
  "ip_profile_version": "string",
  "ip_name": "string",
  "characters": {...},
  "locations": {...},
  "items": {...},
  "relationship_map": {...}
}
```

#### Step 3 输出Schema（= Step 4 输入）

```json
{
  "project_id": "string",
  "episode": "string（第N集）",
  "script_version": "string（v1.0.0）",
  "basic_info": {
    "duration_sec": "number（如 120）",
    "shot_count": "number（如 15）",
    "emotion_tone": "string（爽/虐/甜/悬疑/复仇/逆袭/甜宠）",
    "color_temp": "string（冷/暖/明/暗/对比强烈/柔和）",
    "main_view_char": "string（char_XX）"
  },
  "scene_list": [
    {
      "scene_id": "string（如 S01）",
      "location_id": "string（loc_XX）",
      "scene_name": "string",
      "scene_type": "string（室内/室外）",
      "time": "string（日/夜）",
      "characters": ["char_XX"],
      "scene_function": "string（TENSION/MOOD/REVEAL/ACTION/TRANSITION/CLIFFHANGER）",
      "emotion_value": "string（L1-L5）",
      "beat_position": "string（B01-B15）",
      "emotion_turning_point": "string（时间点，如00:30）"
    }
  ],
  "script_scenes": [
    {
      "scene_id": "string（S01）",
      "location_id": "string（loc_XX）",
      "location_name": "string",
      "content": {
        "actions": [
          {
            "actor": "char_XX",
            "action": "string（动作描述）"
          }
        ],
        "dialogues": [
          {
            "actor": "char_XX",
            "voice": "string（voice:(情绪/语速)"对白"）",
            "content": "string（≤15字）"
          }
        ]
      },
      "audio_tags": {
        "bgm": "string（[BGM: 情绪描述, 曲风, BPM, 时间点]）",
        "sfx": ["string（[SFX: 音效类型, 时间点]）"]
      }
    }
  ],
  "emotion_curve": {
    "curve_data": [
      {"time": "00:00", "level": "L1", "description": "string"},
      {"time": "00:30", "level": "L2", "description": "string"},
      {"time": "01:00", "level": "L3", "description": "string"},
      {"time": "01:30", "level": "L4", "description": "string"},
      {"time": "02:00", "level": "L5", "description": "string"}
    ],
    "turning_points": [
      {"time": "00:30", "type": "string", "description": "string"}
    ]
  }
}
```

---

### Step 3 → Step 4

#### Step 4 输入Schema

> 即 Step 3 输出Schema（完整传入）

```json
{
  "project_id": "string",
  "episode": "string",
  "script_version": "string",
  "basic_info": {...},
  "scene_list": [...],
  "script_scenes": [...],
  "emotion_curve": {...}
}
```

#### Step 4 输出Schema（= Step 6 输入之导演约束）

```json
{
  "project_id": "string",
  "episode": "string（第N集）",
  "control_tower_version": "string（v1.0.0）",
  "D1_emotion_baseline": {
    "emotion_type": "string（爽/虐/甜等）",
    "color_temp": "string",
    "narrative_pace": "string（快/中/慢）",
    "core_emotion": "string（一句话描述）",
    "emotion_turning_points": ["string（时间点列表）"]
  },
  "D2_scene_beat_table": [
    {
      "scene_id": "string（S01）",
      "scene_name": "string",
      "function": "string（TENSION/MOOD/REVEAL/ACTION/TRANSITION/CLIFFHANGER）",
      "emotion_value": "string（L1-L5）",
      "beat_position": "string（B01-B15）",
      "core_action": "string（核心动作）"
    }
  ],
  "D3_beat_tracking": [
    {
      "time_range": "string（[00:00-00:08]）",
      "shot_id": "string（P01）",
      "emotion_curve": "string（L1→L2）",
      "beat_type": "string（B01-B15）",
      "director_intent": "string（导演意图描述）"
    }
  ],
  "D4_camera_intent": [
    {
      "shot_id": "string（P01）",
      "time_range": "string（[00:00-00:08]）",
      "emotion_state": "string（L1平静）",
      "beat_position": "string（B01开场画面）",
      "camera_intent": {
        "shot_type": "string（WS/ECU/CU/MS等）",
        "camera_action": "string（固定/推进/拉远/摇/移等）",
        "lighting_note": "string（光线描述）",
        "color_note": "string（色调描述）"
      },
      "axis_constraint": {
        "enabled": "boolean（双人对话场景须为true）",
        "axis_line": "string（角色A ←→ 角色B）",
        "char_a_side": "string（char_XX在轴线左侧）",
        "char_b_side": "string（char_XX在轴线右侧）"
      },
      "prohibited": ["string（禁止使用的镜头/运镜/情绪跳变）"]
    }
  ],
  "constraint_summary": {
    "total_shots": "number",
    "emotion_jump_rules": "string（L1→L4禁止等）",
    "ecu_rules": "string（情绪未到位时禁止ECU）",
    "axis_rules": "string（180度轴线约束）"
  }
}
```

---

### Step 4 → Step 5

#### Step 5 输入Schema

> 即 Step 2 输出Schema（含char/loc/item档案） + Step 3 basic_info

```json
{
  "project_id": "string",
  "characters": {...},
  "locations": {...},
  "items": {...},
  "basic_info": {
    "emotion_tone": "string",
    "color_temp": "string",
    "main_view_char": "string"
  }
}
```

#### Step 5 输出Schema（= Step 6/7 输入之资产）

```json
{
  "project_id": "string",
  "asset_library_version": "string（v1.0.0）",
  "characters": {
    "char_XX": {
      "id": "string（char_XX）",
      "name": "string",
      "dna_lock": {
        "appearance_lock": {
          "姓名": "string",
          "性别": "string",
          "年龄区间": "string",
          "面部特征": {
            "脸型": "string",
            "眉形": "string",
            "眼形": "string",
            "鼻形": "string",
            "嘴形": "string",
            "肤色": "string"
          },
          "体型": "string",
          "标志性特征": "string",
          "发型": "string",
          "发色": "string"
        },
        "style_lock": {
          "服装风格": {
            "日常": "string",
            "职场": "string",
            "特殊场合": "string"
          },
          "妆容风格": "string",
          "配饰": ["string"],
          "道具": ["string"]
        },
        "behavior_lock": {
          "表情习惯": "string",
          "肢体语言": "string",
          "动态特征": "string",
          "声音特征": "string"
        }
      },
      "nine_grid_refs": [
        {
          "slot": "string（row1_col1/row1_col2等）",
          "oss_url": "string（上传后OSS URL）",
          "description": "string（正面标准像/日常穿搭等）",
          "scene_tag": "string（日常/职场/情绪/特殊）"
        }
      ],
      "dna_prompt_keywords": "string（逗号分隔的DNA外貌关键词，用于image_prompt）"
    }
  },
  "locations": {
    "loc_XX": {
      "id": "string（loc_XX）",
      "name": "string",
      "type": "string",
      "time": "string",
      "atmosphere_desc": {
        "光线": "string",
        "色调": "string",
        "陈设": "string"
      },
      "key_elements": ["string"],
      "atmosphere_image_oss_url": "string（氛围图OSS URL）",
      "ai_prompt_template": "string（AI生成场景图的Prompt模板）"
    }
  },
  "items": {
    "item_XX": {
      "id": "string（item_XX）",
      "name": "string",
      "appearance": "string",
      "size": "string",
      "material": "string",
      "symbolic_meaning": "string",
      "ref_image_oss_url": "string（道具图OSS URL）"
    }
  },
  "asset_check": {
    "all_chars_have_nine_grid": "boolean",
    "all_locs_have_atmosphere_image": "boolean",
    "all_items_have_ref_image": "boolean",
    "oss_upload_complete": "boolean"
  }
}
```

---

### Step 5 → Step 6

#### Step 6 输入Schema（导演约束 + 资产 + 剧本）

```json
{
  "project_id": "string",
  "director_control": {
    "D1_emotion_baseline": {...},
    "D2_scene_beat_table": [...],
    "D3_beat_tracking": [...],
    "D4_camera_intent": [...],
    "constraint_summary": {...}
  },
  "asset_library": {
    "characters": {...},
    "locations": {...},
    "items": {...}
  },
  "script": {
    "basic_info": {...},
    "scene_list": [...],
    "script_scenes": [...],
    "emotion_curve": {...}
  }
}
```

#### Step 6 输出Schema（= Step 7/8/9 输入）

```json
{
  "project_id": "string",
  "episode": "string",
  "shot_script_version": "string（v1.0.0）",
  "basic_info": {
    "total_duration_sec": "number",
    "total_shots": "number",
    "shot_duration_avg": "number（如 10秒）",
    "main_view_char": "string",
    "style_preset": "string",
    "aspect_ratio": "string"
  },
  "shots": [
    {
      "shot_id": "string（shot_01）",
      "duration_sec": "number（如 8）",
      "scene_id": "string（S01）",
      "location_id": "string（loc_XX）",
      "characters": ["char_XX"],
      "shot_metadata": {
        "shot_type": "string（WS/ECU/CU/MS/MCU/LS/EWS）",
        "camera_action": "string（固定/推dolly in/拉dolly out/摇pan/移tracking/跟follow/升降boom）",
        "axis": "string（左/右/居中）",
        "beat_position": "string（B01-B15）",
        "emotion_value": "string（L1-L5）",
        "scene_function": "string（TENSION/MOOD/REVEAL/ACTION/TRANSITION/CLIFFHANGER）",
        "emotion_curve": "string（L1→L2）"
      },
      "director_instruction": "string（导演指令，自然语言描述）",
      "content": {
        "description": "string（分场内容描述）",
        "actions": [
          {
            "actor": "char_XX",
            "action": "string"
          }
        ],
        "dialogues": [
          {
            "actor": "char_XX",
            "content": "string（≤15字）",
            "voice": "string（voice:(情绪/语速)"..."）"
          }
        ]
      },
      "image_prompt": {
        "full_prompt": "string（AI生图Prompt，含char_XX DNA关键词、loc_XX场景描述、style_preset）",
        "char_refs": ["char_XX"],
        "loc_refs": ["loc_XX"],
        "style_suffix": "string"
      },
      "video_prompt": {
        "full_prompt": "string（AI视频Prompt，含camera_action、Audio Layer标注）",
        "char_refs": ["char_XX"],
        "loc_refs": ["loc_XX"],
        "camera_action": "string",
        "camera_params": "string（如Seedance/Kling运镜参数）"
      },
      "audio_layer": {
        "tts": [
          {
            "time_range": "string（00:05-00:10）",
            "actor": "char_XX",
            "voice": "string",
            "content": "string（≤15字）"
          }
        ],
        "bgm": [
          {
            "time_range": "string",
            "description": "string（[BGM: 情绪, 曲风, BPM, 时间点]）",
            "volume": "string（60-70%）"
          }
        ],
        "sfx": [
          {
            "time": "string",
            "type": "string（[SFX: 音效类型, 时间点, 混音方式]）",
            "volume": "string"
          }
        ]
      }
    }
  ],
  "shot_script_check": {
    "all_shots_have_char_refs": "boolean",
    "all_shots_have_loc_refs": "boolean",
    "all_shots_have_camera_action": "boolean",
    "all_shots_have_emotion_value": "boolean",
    "all_dialogues_under_15_chars": "boolean",
    "all_shots_have_audio_layer": "boolean"
  }
}
```

---

### Step 6 → Step 7

#### Step 7 输入Schema

> 即 Step 6 输出Schema中的 `shots[].image_prompt` + `asset_library`

```json
{
  "project_id": "string",
  "shots": [
    {
      "shot_id": "string",
      "location_id": "string",
      "characters": ["char_XX"],
      "image_prompt": {...},
      "shot_metadata": {...}
    }
  ],
  "asset_library": {
    "characters": {...},
    "locations": {...}
  }
}
```

#### Step 7 输出Schema（= Step 8 输入之视觉参考）

```json
{
  "project_id": "string",
  "visual_generation_version": "string（v1.0.0）",
  "char_ref_images": {
    "char_XX": [
      {
        "slot": "string",
        "oss_url": "string（https://libtv-res.liblib.art/...）",
        "local_path": "string（如已下载到本地）",
        "prompt_used": "string",
        "generation_tool": "string（Seedance/Kling/Midjourney）"
      }
    ]
  },
  "scene_ref_images": {
    "loc_XX": {
      "atmosphere_image_oss_url": "string",
      "atmosphere_image_local": "string",
      "prompt_used": "string"
    }
  },
  "item_ref_images": {
    "item_XX": {
      "oss_url": "string",
      "prompt_used": "string"
    }
  },
  "shot_images": {
    "shot_XX": {
      "image_oss_url": "string（该镜头的生成图URL）",
      "used_as_video_first_frame": "boolean"
    }
  },
  "visual_generation_check": {
    "all_core_chars_have_nine_grid": "boolean",
    "all_locs_have_atmosphere_image": "boolean",
    "all_shots_have_generated_image": "boolean",
    "all_images_uploaded_to_oss": "boolean"
  }
}
```

---

### Step 7 → Step 8

#### Step 8 输入Schema

```json
{
  "project_id": "string",
  "shots": [
    {
      "shot_id": "string",
      "duration_sec": "number",
      "characters": ["char_XX"],
      "location_id": "string",
      "video_prompt": {...},
      "shot_metadata": {...}
    }
  ],
  "char_ref_images": {...},
  "scene_ref_images": {...}
}
```

#### Step 8 输出Schema（= Step 10 输入）

```json
{
  "project_id": "string",
  "video_generation_version": "string（v1.0.0）",
  "video_segments": [
    {
      "shot_id": "string（shot_01）",
      "oss_url": "string（https://libtv-res.liblib.art/...）",
      "local_path": "string（如已下载）",
      "duration_sec": "number（实际生成时长）",
      "generation_tool": "string（Seedance/Kling）",
      "session_id": "string（LibTV session ID）",
      "time_range": "string（[00:00-00:08]）",
      "status": "string（success/failed/pending）",
      "quality_check": {
        "char_consistency": "string（good/moderate/poor）",
        "camera_action_executed": "boolean",
        "scene_match": "boolean"
      }
    }
  ],
  "generation_summary": {
    "total_shots": "number",
    "success_count": "number",
    "failed_count": "number",
    "reroll_needed": ["shot_id列表"]
  }
}
```

---

### Step 6 → Step 9（音频制作）

> 注意：Step 9 的输入从 Step 6 的 `shots[].audio_layer` 提取

#### Step 9 输入Schema

```json
{
  "project_id": "string",
  "episode": "string",
  "shots": [
    {
      "shot_id": "string",
      "time_range": "string",
      "audio_layer": {
        "tts": [...],
        "bgm": [...],
        "sfx": [...]
      }
    }
  ]
}
```

#### Step 9 输出Schema（= Step 10 输入）

```json
{
  "project_id": "string",
  "episode": "string",
  "audio_production_version": "string（v1.0.0）",
  "tts_track": {
    "oss_url": "string（TTS完整音频OSS URL）",
    "local_path": "string",
    "segments": [
      {
        "shot_id": "string",
        "time_range": "string",
        "actor": "char_XX",
        "content": "string",
        "voice_params": {
          "emotion": "string",
          "speed": "string",
          "timbre": "string"
        },
        "duration_sec": "number"
      }
    ],
    "tool": "string（Azure语音/火山引擎/剪映）"
  },
  "bgm_track": {
    "oss_url": "string（BGM完整音频OSS URL）",
    "local_path": "string",
    "segments": [
      {
        "time_range": "string",
        "description": "string",
        "bpm": "number",
        "emotion": "string",
        "volume": "number（60-70%）"
      }
    ],
    "tool": "string（Suno/Udio）"
  },
  "sfx_track": {
    "oss_url": "string（SFX完整音频OSS URL）",
    "local_path": "string",
    "events": [
      {
        "time": "string",
        "type": "string",
        "description": "string",
        "duration_sec": "number"
      }
    ],
    "tool": "string（音效素材库/AI生成）"
  },
  "three_track_timeline": {
    "oss_url": "string（三轨整合后完整音频OSS URL）",
    "track_mix": {
      "tts_volume": "number（最高）",
      "bgm_volume": "number（60-70%）",
      "sfx_volume": "number（适中）"
    }
  },
  "audio_production_check": {
    "tts_complete": "boolean",
    "bgm_complete": "boolean",
    "sfx_complete": "boolean",
    "timeline_integrated": "boolean",
    "all_oss_urls_recorded": "boolean"
  }
}
```

---

### Step 8 + Step 9 → Step 10

#### Step 10 输入Schema

```json
{
  "project_id": "string",
  "episode": "string",
  "video_segments": [...],
  "audio": {
    "tts_track": {...},
    "bgm_track": {...},
    "sfx_track": {...},
    "three_track_timeline": {...}
  },
  "shot_script": {
    "basic_info": {...},
    "shots": [...]
  }
}
```

#### Step 10 输出Schema（= Step 11 输入）

```json
{
  "project_id": "string",
  "episode": "string",
  "export_version": "string（v1.0.0）",
  "final_video": {
    "oss_url": "string（成片MP4 OSS URL）",
    "local_path": "string",
    "resolution": "string（1080×1920）",
    "bitrate": "string（8000kbps+）",
    "format": "string（MP4）",
    "fps": "number（如 30）",
    "total_duration_sec": "number",
    "jianying_project_file": "string（剪映工程文件路径）"
  },
  "subtitle": {
    "oss_url": "string（SRT字幕OSS URL）",
    "local_path": "string",
    "format": "string（SRT）",
    "embedded": "boolean"
  },
  "export_config": {
    "platform": "string（抖音/快手/视频号）",
    "resolution": "1080×1920",
    "bitrate": "string",
    "duration_sec": "number",
    "aspect_ratio": "9:16竖屏"
  },
  "timeline_check": {
    "video_segments_ordered": "boolean",
    "audio_video_sync": "boolean",
    "subtitle_tts_aligned": "boolean",
    "color_grade_unified": "boolean"
  }
}
```

---

### Step 10 → Step 11

#### Step 11 输入Schema

```json
{
  "project_id": "string",
  "episode": "string",
  "final_video": {...},
  "subtitle": {...},
  "script": {
    "script_scenes": [...],
    "dialogues": [...]
  },
  "audio_copyright": {
    "bgm_license": "string（BGM授权证明）",
    "sfx_license": "string（SFX授权证明）",
    "tts_voice_license": "string（TTS音色授权）"
  },
  "source_material": {
    "novel_title": "string",
    "adaptation_authorized": "boolean",
    "authorization_document": "string（如有）"
  }
}
```

#### Step 11 输出Schema（终态）

```json
{
  "project_id": "string",
  "episode": "string",
  "risk_report_version": "string（v1.0.0）",
  "report_date": "string（YYYY-MM-DD）",
  "reviewer": "string",
  "final_video_url": "string",
  "four_dimension_check": {
    "copyright": {
      "novel_authorized": "boolean",
      "adaptation_scope_compliant": "boolean",
      "music_authorized": "boolean",
      "art_assets_authorized": "boolean",
      "overall_pass": "boolean"
    },
    "content_compliance": {
      "politically_sensitive": "boolean（true=无违规）",
      "pornographic": "boolean（true=无违规）",
      "violent": "boolean（true=无违规）",
      "superstitious": "boolean（true=无违规）",
      "contraband": "boolean（true=无违规）",
      "misinformation": "boolean（true=无违规）",
      "violations_found": ["string（如有违规，列出具体内容）"]
    },
    "portrait_rights": {
      "no_real_person": "boolean",
      "all_ai_generated": "boolean",
      "no_celebrity_likeness": "boolean",
      "no_minor_represented": "boolean",
      "overall_pass": "boolean"
    },
    "platform_specs": {
      "douyin": {
        "resolution_check": "boolean",
        "duration_check": "boolean",
        "watermark_check": "boolean",
        "pass": "boolean"
      },
      "kuaishou": {...},
      "wechat_channel": {...}
    }
  },
  "overall_verdict": {
    "pass": "boolean",
    "publish_ready": "boolean",
    "issues_to_fix": ["string（如有）"],
    "can_proceed_to_publish": "boolean"
  }
}
```

---

## 关键数据锚点

### char_XX 角色锚点

**贯穿**：Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7 → Step 8

| Step | 字段路径 | 说明 |
|------|---------|------|
| Step 2 | `characters.char_XX.id` | 首次定义，分配ID |
| Step 2 | `characters.char_XX.relationships` | 关系网 |
| Step 3 | `script_scenes[].characters[]` | 剧本中引用角色 |
| Step 4 | `D4_camera_intent[].axis_constraint` | 轴线约束涉及角色 |
| Step 5 | `characters.char_XX.dna_lock` | 三层锁完整定义 |
| Step 5 | `characters.char_XX.nine_grid_refs` | 九宫格参考图 |
| Step 6 | `shots[].characters[]` | 每镜引用角色 |
| Step 6 | `shots[].image_prompt.char_refs` | image_prompt中的角色引用 |
| Step 6 | `shots[].video_prompt.char_refs` | video_prompt中的角色引用 |
| Step 7 | `char_ref_images.char_XX` | 该角色的所有参考图OSS URL |
| Step 8 | `video_segments[].characters` | 视频片段对应的角色 |

**每次出现必须携带**：
```json
{
  "id": "char_XX",
  "name": "string",
  "dna_prompt_keywords": "string（逗号分隔外貌特征词）"
}
```

### loc_XX 场景锚点

**贯穿**：Step 2 → Step 3 → Step 5 → Step 6 → Step 7 → Step 8

| Step | 字段路径 | 说明 |
|------|---------|------|
| Step 2 | `locations.loc_XX` | 首次定义，分配ID |
| Step 3 | `scene_list[].location_id` | 剧本中引用场景 |
| Step 5 | `locations.loc_XX` | 场景资产（含AI生成模板） |
| Step 5 | `locations.loc_XX.atmosphere_image_oss_url` | 场景氛围图OSS URL |
| Step 6 | `shots[].location_id` | 每镜引用场景 |
| Step 7 | `scene_ref_images.loc_XX` | 场景参考图OSS URL |
| Step 8 | `video_segments[].location_id` | 视频片段对应的场景 |

**每次出现必须携带**：
```json
{
  "id": "loc_XX",
  "name": "string",
  "atmosphere": "string（氛围关键词）",
  "ai_prompt_keywords": "string（逗号分隔场景描述词）"
}
```

### item_XX 道具锚点

**贯穿**：Step 2 → Step 5 → Step 6（按需出现）

| Step | 字段路径 | 说明 |
|------|---------|------|
| Step 2 | `items.item_XX` | 首次定义 |
| Step 5 | `items.item_XX` + 道具图OSS URL |
| Step 6 | `shots[].content.actions` | 按需引用（剧情需要时） |

**每次出现必须携带**：
```json
{
  "id": "item_XX",
  "name": "string",
  "appearance": "string",
  "symbolic_meaning": "string"
}
```

---

## 字段兼容层（v6.x迁移策略）

### CDP @语法对齐（v6.3 → v6.4）

**当前格式（v6.3 兼容层）**：
```
char_01 女主 / loc_01 格子间 / item_01 咖啡杯
```

**目标格式（v6.4+）**：
```
@char_01 — 女主角色参考
  Appearance: [外貌锁]
  Style: [风格锁]
  Behavior: [行为锁]

@loc_01 — 格子间场景
  Time: 白天
  Mood: 压抑
  Lighting: 自然光+台灯暖黄

@item_01 — 咖啡杯道具
  Material: 陶瓷白
  Symbolic: 日常生活的隐喻
```

**迁移策略**：

| 阶段 | 版本 | 行为 |
|------|------|------|
| Phase 1 | v6.3 | 兼容层：两种格式均可识别，自动转换为目标格式 |
| Phase 2 | v6.4 | 完全迁移至@语法，旧格式报错 |
| Phase 3 | v6.5 | @语法支持嵌套引用 `@char_01.appearance_lock.face` |

**兼容层转换规则**：
- 识别正则：`char_\d+` / `loc_\d+` / `item_\d+`（独立词或后接空格/斜杠）
- 自动注入对应档案字段，生成`@char_XX`完整语法
- Step 2 输出统一为@语法，Step 3 及后续全部消费@语法

---

## Schema验证规则

### 自动验证（每步完成后强制执行）

```json
验证规则 = {
  "required_fields": "检查所有required字段非空",
  "id_format": {
    "char_XX": "char_ + 2位数字（01-99）",
    "loc_XX": "loc_ + 2位数字（01-99）",
    "item_XX": "item_ + 2位数字（01-99）",
    "shot_XX": "shot_ + 2位数字（01-99）",
    "scene_id": "S + 2位数字（如S01）"
  },
  "reference_integrity": {
    "all_char_refs_defined": "所有char_XX在Step 2的characters中已定义",
    "all_loc_refs_defined": "所有loc_XX在Step 2的locations中已定义",
    "all_item_refs_defined": "所有item_XX在Step 2的items中已定义"
  },
  "value_constraints": {
    "dialogue_max_15_chars": "所有对白content字段≤15字",
    "emotion_value_range": "L1-L5",
    "beat_position_range": "B01-B15",
    "scene_function_enum": "TENSION|MOOD|REVEAL|ACTION|TRANSITION|CLIFFHANGER",
    "shot_type_enum": "WS|ECU|CU|MCU|MS|LS|EWS"
  }
}
```

### 验证失败处理流程

```
验证失败
    │
    ▼
阻断该Step输出 ──→ 生成错误报告
    │               {
    │                 "step": "Step6",
    │                 "errors": [
    │                   {
    │                     "field": "shots[3].dialogue[0].content",
    │                     "rule": "dialogue_max_15_chars",
    │                     "value": "18字台词内容",
    │                     "severity": "blocker"
    │                   }
    │                 ]
    │               }
    ▼
进入错误恢复流程
    │
    ├── 自动修复（severity=warning）：自动截断/补齐
    │   └── 对白>15字 → 自动截断并在下一镜补完
    │
    └── 人工确认（severity=blocker）：阻断 → 修复后重跑该Step
        ├── char_ref未定义 → 回Step 2补充定义
        ├── loc_ref未定义 → 回Step 2补充定义
        └── 其他阻断项 → 修复源数据后重跑该Step
```

### 跨Step引用验证（累积检查）

| 检查时机 | 检查内容 | 失败后果 |
|---------|---------|---------|
| Step 2 完成后 | 所有char_XX/loc_XX在Step 1的character_list/location_list中已出现 | 阻断Step 2，警告新增角色未在改编稿中定义 |
| Step 6 完成后 | 所有char_ref已定义 + 所有loc_ref已定义 + 所有dialogue≤15字 | 阻断Step 6，不允许进入生成阶段 |
| Step 8 完成后 | 每个shot_XX均有OSS URL + status=success | 生成失败-shot需重跑 |
| Step 10 完成后 | 成片时长与配置单误差<1秒 | 阻断发布，需重新剪辑 |

---

## 数据Schema版本管理

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0.0 | 2026-03-26 | 初始版本，基于12个SOP文件首次建立 |

### 字段变更规则

- **新增字段**：在末尾追加，添加 `_added_in: "v1.1.0"` 元数据
- **废弃字段**：标记 `_deprecated_in: "vx.x"` + `_replacement: "新字段名"`，保留至v6.x兼容层
- **Breaking Change**：仅在大版本（v2.0.0/v3.0.0）发生，必须同步更新MEMORY.md

---

*本文件由漫舟v6.0.0 SOP规范生成，是执行层的机器可读补充文档*
*位置：`AI漫剧知识库/07-执行层/漫舟编排管道/数据Schema传递规范.md`*
