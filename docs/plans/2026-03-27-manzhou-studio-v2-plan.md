# 漫剧工业化创作站 v2.0 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 manzhou-studio 从单流程生成工具重构为具备双风格库、文件上传、IP智能解析、角色/场景可视化展示、两层分镜Prompt的完整创作平台。

**Architecture:** 单文件 HTML + 内嵌 React/Babel，保持向后兼容。新增模块化组件，数据通过 localStorage 持久化，Prompt 按双风格库+DNA锚点机制重构。

**Tech Stack:** React 18.2 + Babel Standalone，无构建依赖

---

## 实施顺序

> 按依赖顺序执行，TDD 逻辑：先定义数据结构 → 再构建UI层 → 最后调试Prompt

---

### Task 1: 添加风格库常量 + 视频比例常量

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html:31-33`

**Step 1: 添加动漫风格库**

在 `STYLE_PRESETS` 后新增动漫常量：

```javascript
// 动漫风格库（12个）
const ANIME_STYLES = [
  { id: "anime_realistic", label: "写实厚涂", keywords: "光影真实 笔触厚重 质感强烈", scene: "成人向 电影感" },
  { id: "anime_celluloid", label: "赛璐璐平涂", keywords: "线条清晰 色彩饱和 边缘锐利", scene: "抖音爆款 古风甜宠" },
  { id: "anime_ink", label: "水墨写意", keywords: "国风水墨 晕染留白 意境深远", scene: "古风 文艺" },
  { id: "anime_3d_hybrid", label: "厚涂伪3D", keywords: "3D辅助 手绘质感 细节丰富", scene: "大制作 高端" },
  { id: "anime_jp_fresh", label: "日系清新", keywords: "低饱和 柔光 空气感 柔焦", scene: "女性受众 治愈" },
  { id: "anime_ancient_water", label: "古风水韵", keywords: "水彩晕染 工笔线条 淡雅", scene: "古装 仙侠" },
  { id: "anime_american", label: "美式漫画", keywords: "强对比 高饱和 动态张力 粗线条", scene: "泛娱乐 超英" },
  { id: "anime_steampunk", label: "蒸汽朋克", keywords: "机械 齿轮 维多利亚 铜色", scene: "奇幻 冒险" },
  { id: "anime_cyberpunk", label: "赛博朋克", keywords: "霓虹 数字 废土 暗调", scene: "科幻 未来" },
  { id: "anime_picture_book", label: "绘本插画风", keywords: "几何色块 低多边形 简洁", scene: "儿童 教育" },
  { id: "anime_ukiyoe", label: "浮世绘风", keywords: "日本传统 波浪 浮世美人", scene: "古风 日系" },
  { id: "anime_gothic", label: "厚描插画", keywords: "质感厚重 细节丰富 暗部深遂", scene: "成人向 哥特" },
];

// 电影风格库（11个）
const MOVIE_STYLES = [
  { id: "movie_wkw", label: "王家卫", keywords: "霓虹夜雨 琥珀暖调 慢动作 潮湿感", scene: "《花样年华》《重庆森林》" },
  { id: "movie_hollywood", label: "好莱坞商业片", keywords: "高对比 色域宽广 升格镜头 冲击力", scene: "漫威 DC" },
  { id: "movie_art_house", label: "文艺剧情片", keywords: "低饱和 长镜头 浅景深 叙事感", scene: "贾樟柯 是枝裕和" },
  { id: "movie_noir", label: "黑色电影", keywords: "高反差 光影戏剧化 青灰调 神秘", scene: "《七宗罪》《唐人街》" },
  { id: "movie_korean", label: "韩式电影", keywords: "柔光 暖调 情绪感 柔焦", scene: "奉俊昊 朴赞郁" },
  { id: "movie_japanese", label: "日式电影", keywords: "侘寂 留白 淡色调 静谧", scene: "小津 北野武" },
  { id: "movie_chinese_period", label: "国产古装大片", keywords: "浓墨重彩 构图对称 史诗感", scene: "张艺谋 陈凯歌" },
  { id: "movie_european", label: "欧洲艺术电影", keywords: "疏离感 冷调 长镜头 诗意", scene: "安哲罗普洛斯" },
  { id: "movie_documentary", label: "纪录片质感", keywords: "自然光 手持感 真实场景 噪点", scene: "纪实短剧" },
  { id: "movie_horror", label: "惊悚/恐怖", keywords: "低光源 冷色调 浅焦 压迫感", scene: "悬疑 惊悚" },
  { id: "movie_wuxia", label: "武侠动作", keywords: "快速剪辑 动态模糊 动感构图 凌厉", scene: "武侠 动作" },
];

// 视频比例选项
const VIDEO_RATIOS = [
  { id: "9:16", label: "9:16 竖屏", size: "1080×1920", platforms: "抖音 / 快手 / 小红书 / 视频号" },
  { id: "16:9", label: "16:9 横屏", size: "1920×1080", platforms: "B站 / YouTube" },
  { id: "1:1", label: "1:1 方屏", size: "1080×1080", platforms: "Instagram" },
  { id: "4:3", label: "4:3 经典", size: "1440×1080", platforms: "复古风格 老电影感" },
];
```

**Step 2: 替换 STEP 配置标签**

```javascript
const STEPS = [
  { id: 0, label: "项目配置", icon: "⚙️", short: "S00" },
  { id: 1, label: "小说改编", icon: "📖", short: "S01" },
  { id: 2, label: "IP解析", icon: "🧬", short: "S02" },
  { id: 3, label: "剧本生成", icon: "🎬", short: "S03" },
  { id: 4, label: "角色&场景", icon: "🎭", short: "S04" },
  { id: 5, label: "分镜脚本", icon: "🎞️", short: "S05" },
  { id: 6, label: "操作文档", icon: "📄", short: "OUT" },
];
```

**Step 3: 验证文件语法正确**

打开浏览器开发者工具 → Console，确保无 SyntaxError

---

### Task 2: Step 00 重构 — 双风格库 + 视频比例选择

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` Step 00 区块（约 line 542-570）

**Step 1: 新增 cfg 状态字段**

在 `cfg` useState 的默认对象中新增：

```javascript
// cfg 默认值扩展
{
  title: s.title || "",
  type: s.type || "动画",
  platform: s.platform || "小红书",
  duration: s.duration || "120",
  episodes: s.episodes || "10",
  style: s.style || "anime_jp_fresh",
  animeStyle: s.animeStyle || "anime_jp_fresh",    // 新增：动漫风格ID
  movieStyle: s.movieStyle || "movie_wkw",          // 新增：电影风格ID
  ratio: s.ratio || "9:16",                         // 新增：视频比例
}
```

**Step 2: 重构 Step 00 UI — 添加风格选择区**

将 `视觉风格预设` 行替换为双风格库选择：

```javascript
// Step 00 风格选择区（在单集目标时长行后添加）
<Field label="动漫风格 (Anime Style)">
  <div style={{ display: "grid", gridTemplateColumns: "repeat 4, 1fr", gap: 8 }}>
    {ANIME_STYLES.map(s => {
      const on = cfg.animeStyle === s.id;
      return (
        <button key={s.id} onClick={() => saveCfg({ ...cfg, animeStyle: s.id })}
          style={{
            padding: "8px 10px", borderRadius: 8,
            border: `1px solid ${on ? "#6366f1" : "#2a2d3a"}`,
            background: on ? "rgba(99,102,241,0.2)" : "transparent",
            color: on ? "#a5b4fc" : "#94a3b8", fontSize: 12,
            cursor: "pointer", textAlign: "left", lineHeight: 1.4,
            transition: "all 0.2s"
          }}>
          <div style={{ fontWeight: 600, marginBottom: 2 }}>{s.label}</div>
          <div style={{ fontSize: 10, opacity: 0.7 }}>{s.scene}</div>
        </button>
      );
    })}
  </div>
</Field>

<Field label="电影风格 (Film Style)">
  <div style={{ display: "grid", gridTemplateColumns: "repeat 4, 1fr", gap: 8 }}>
    {MOVIE_STYLES.map(s => {
      const on = cfg.movieStyle === s.id;
      return (
        <button key={s.id} onClick={() => saveCfg({ ...cfg, movieStyle: s.id })}
          style={{
            padding: "8px 10px", borderRadius: 8,
            border: `1px solid ${on ? "#f59e0b" : "#2a2d3a"}`,
            background: on ? "rgba(245,158,11,0.15)" : "transparent",
            color: on ? "#fcd34d" : "#94a3b8", fontSize: 12,
            cursor: "pointer", textAlign: "left", lineHeight: 1.4,
            transition: "all 0.2s"
          }}>
          <div style={{ fontWeight: 600, marginBottom: 2 }}>{s.label}</div>
          <div style={{ fontSize: 10, opacity: 0.7 }}>{s.scene}</div>
        </button>
      );
    })}
  </div>
</Field>

<Field label="视频比例 (Aspect Ratio)">
  <div style={{ display: "grid", gridTemplateColumns: "repeat 4, 1fr", gap: 12 }}>
    {VIDEO_RATIOS.map(r => {
      const on = cfg.ratio === r.id;
      return (
        <button key={r.id} onClick={() => saveCfg({ ...cfg, ratio: r.id })}
          style={{
            padding: "12px 8px", borderRadius: 10,
            border: `1px solid ${on ? "#10b981" : "#2a2d3a"}`,
            background: on ? "rgba(16,185,129,0.1)" : "transparent",
            color: on ? "#34d399" : "#94a3b8", fontSize: 13,
            cursor: "pointer", textAlign: "center", transition: "all 0.2s"
          }}>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{r.id}</div>
          <div style={{ fontSize: 10, opacity: 0.7 }}>{r.platforms.split(" ")[0]}</div>
        </button>
      );
    })}
  </div>
</Field>
```

**Step 3: 验证 — 打开 Step 00，确认三个选择区都正确渲染**

---

### Task 3: Step 01 重构 — 文件上传 + 字数统计

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` Step 01 区块（约 line 573-591）

**Step 1: 新增文件上传状态**

在 `const [novel, setNovel]` 后添加：

```javascript
const [fileName, setFileName] = useState("");
const [wordCount, setWordCount] = useState(0);
const [fileError, setFileError] = useState("");
```

**Step 2: 添加文件处理函数**

在 `genStep1` 函数前添加：

```javascript
const MAX_WORDS = 100000; // 10万字上限

function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  setFileError("");

  if (!["text/plain", "text/markdown"].includes(file.type) && !file.name.match(/\.(txt|md)$/i)) {
    setFileError("仅支持 .txt 或 .md 格式文件");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    const text = e.target.result;
    const chars = text.length;
    // 粗估中文字数（英文按单词计）
    const words = Math.ceil(chars / 2);
    setWordCount(words);
    setFileName(file.name);

    if (words > MAX_WORDS) {
      setFileError(`文件 ${Math.round(words/10000)} 万字，超出10万字限制，已截断`);
      const truncated = text.slice(0, MAX_WORDS * 2);
      setNovel(truncated);
    } else {
      setNovel(text);
    }
  };
  reader.readAsText(file);
}
```

**Step 3: 重构 Step 01 UI — 替换文本区**

```javascript
{/* Step 1: Novel Adaptation */}
{step === 1 && (
  <StepPanel title="Step 01 · 小说改编" icon="📖">
    {/* 文件上传区 */}
    <div style={{
      border: `2px dashed ${fileError ? "#ef4444" : "#2a2d3a"}`,
      borderRadius: 12, padding: "24px", textAlign: "center",
      marginBottom: 20, background: fileError ? "rgba(239,68,68,0.05)" : "#0f1117",
      transition: "all 0.2s"
    }}>
      {fileName ? (
        <div>
          <div style={{ color: "#10b981", fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
            📁 {fileName}
          </div>
          <div style={{ color: "#64748b", fontSize: 13, marginBottom: 12 }}>
            字数：{Math.round(wordCount/10000, 1)} 万字
            {wordCount > MAX_WORDS && <span style={{ color: "#ef4444" }}>（已截断至10万字）</span>}
          </div>
          <button onClick={() => { setFileName(""); setWordCount(0); setNovel(""); }}
            style={{ color: "#94a3b8", fontSize: 12, background: "none", border: "none", cursor: "pointer" }}>
            移除文件，改用手动粘贴
          </button>
        </div>
      ) : (
        <div>
          <div style={{ color: "#94a3b8", fontSize: 28, marginBottom: 12 }}>📂</div>
          <div style={{ color: "#94a3b8", fontSize: 14, marginBottom: 8 }}>
            拖拽上传 .txt / .md 文件
          </div>
          <div style={{ color: "#475569", fontSize: 12, marginBottom: 16 }}>
            支持 ≤10万字小说文本
          </div>
          <label style={{
            display: "inline-block", padding: "8px 20px", borderRadius: 8,
            background: "#6366f1", color: "#fff", fontSize: 13, cursor: "pointer"
          }}>
            选择文件
            <input type="file" accept=".txt,.md" onChange={handleFileUpload} style={{ display: "none" }} />
          </label>
        </div>
      )}
      {fileError && (
        <div style={{ color: "#ef4444", fontSize: 12, marginTop: 8 }}>{fileError}</div>
      )}
    </div>

    {/* 分隔线 */}
    <div style={{ textAlign: "center", color: "#475569", fontSize: 12, margin: "12px 0" }}>
      — 或直接粘贴文本 —
    </div>

    {/* 文本粘贴区 */}
    <Field label="粘贴原始文本" hint={`字数：${Math.round(novel.length/2).toLocaleString()} 字（建议不超过10万字）`}>
      <Input value={novel} onChange={v => { setNovel(v); setFileName(""); setWordCount(0); }} multiline rows={8}
        placeholder="在此粘贴小说或文案原文..." />
    </Field>

    <GenerateBtn onClick={genStep1} loading={loading["s1"]} label="✨ 开始提炼剧本" />
    <OutputBox content={outputs["s1"]} loading={loading["s1"]} />
    {outputs["s1"] && !loading["s1"] && (
      <button onClick={() => setStep(2)} ...> 提取 IP 资产 → </button>
    )}
  </StepPanel>
)}
```

**Step 4: 验证 — 上传一个 .txt 文件，确认字数统计和截断正确**

---

### Task 4: Step 02 重构 — IP 解析结果结构化展示

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` — App 组件 + Step 02

**Step 1: 新增解析结果状态**

```javascript
const [charList, setCharList] = useState([]);   // 角色列表
const [sceneList, setSceneList] = useState([]); // 场景列表
```

**Step 2: 新增 AI 解析后自动填充函数**

在 `genStep2` 之后添加：

```javascript
function parseCharacterFromAI(text) {
  // 简单解析：从AI输出中提取角色信息
  // 期望格式：## 角色1: xxx | 外貌: xxx | 服装: xxx
  const lines = text.split("\n");
  const chars = [];
  const scenes = [];
  let currentChar = null;
  let currentScene = null;

  for (const line of lines) {
    // 角色提取：匹配 ## 角色 或 ### 角色
    const charMatch = line.match(/角色[：:]\s*(.+)/);
    if (charMatch) {
      currentChar = { id: chars.length, name: charMatch[1], desc: "", clothing: "", dna: "" };
      chars.push(currentChar);
    }
    // 场景提取
    const sceneMatch = line.match(/场景[：:]\s*(.+)/);
    if (sceneMatch) {
      currentScene = { id: scenes.length, name: sceneMatch[1], desc: "", atmosphere: "", dna: "" };
      scenes.push(currentScene);
    }
    // 外貌/服装描述
    const descMatch = line.match(/(外貌|服装|外观)[：:]\s*(.+)/);
    if (descMatch && currentChar) {
      if (RegExp.$1 === "外貌") currentChar.desc = descMatch[2];
      else currentChar.clothing = descMatch[2];
    }
  }

  // 如果解析为空，尝试按段落数量均分
  if (chars.length === 0 && lines.length > 0) {
    const names = ["角色A", "角色B", "角色C", "角色D", "角色E"];
    for (let i = 0; i < Math.min(parseInt(charCount), 5); i++) {
      chars.push({ id: i, name: names[i], desc: "（详见AI输出）", clothing: "（详见AI输出）", dna: "" });
    }
  }
  if (scenes.length === 0 && lines.length > 0) {
    const names = ["场景A", "场景B", "场景C", "场景D"];
    for (let i = 0; i < Math.min(parseInt(sceneCount), 4); i++) {
      scenes.push({ id: i, name: names[i], desc: "（详见AI输出）", atmosphere: "（详见AI输出）", dna: "" });
    }
  }

  setCharList(chars);
  setSceneList(scenes);
}
```

**Step 3: 在 genStep2 的 onDone 回调中调用解析**

修改 `gen` 函数逻辑，对 s2 增加解析：

```javascript
function gen(key, system, user) {
  saveOutputs(key, "");
  setLoading(p => ({ ...p, [key]: true }));
  sendToAPI(system, user,
    (chunk) => saveOutputs(key, (outputsRef.current[key] || "") + chunk),
    () => {
      setLoading(p => ({ ...p, [key]: false }));
      // s2 完成后自动解析角色/场景
      if (key === "s2") {
        const text = outputsRef.current["s2"] || "";
        parseCharacterFromAI(text);
      }
    }
  );
}
```

**Step 4: 重构 Step 02 UI — 添加角色/场景编辑区**

在 Step 02 的 `OutputBox` 后添加：

```javascript
{/* 角色列表编辑 */}
{outputs["s2"] && !loading["s2"] && charList.length > 0 && (
  <div style={{ marginTop: 24 }}>
    <h3 style={{ color: "#818cf8", fontSize: 15, fontWeight: 700, marginBottom: 16, letterSpacing: "0.05em" }}>
      👥 角色列表（共 {charList.length} 个）
    </h3>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 24 }}>
      {charList.map((c, i) => (
        <div key={i} style={{ background: "#1a1d2e", border: "1px solid #2a2d3a", borderRadius: 10, padding: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <input value={c.name} onChange={e => {
              const updated = [...charList]; updated[i].name = e.target.value; setCharList(updated);
            }} style={{ background: "transparent", border: "none", color: "#e2e8f0", fontSize: 14, fontWeight: 700, outline: "none", flex: 1 }} />
            <button onClick={() => setCharList(p => p.filter((_, idx) => idx !== i))}
              style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: 12 }}>✕</button>
          </div>
          <textarea value={c.desc} onChange={e => {
            const updated = [...charList]; updated[i].desc = e.target.value; setCharList(updated);
          }} placeholder="外貌描述..." rows={2}
            style={{ width: "100%", background: "transparent", border: "none", color: "#94a3b8", fontSize: 12, resize: "none", outline: "none", fontFamily: "inherit" }} />
        </div>
      ))}
      <button onClick={() => setCharList(p => [...p, { id: p.length, name: "新角色", desc: "", clothing: "", dna: "" }])}
        style={{ background: "transparent", border: "1px dashed #2a2d3a", borderRadius: 10, color: "#475569", cursor: "pointer", fontSize: 13, padding: 14 }}>
        + 添加角色
      </button>
    </div>

    {/* 场景列表编辑 */}
    <h3 style={{ color: "#818cf8", fontSize: 15, fontWeight: 700, marginBottom: 16, letterSpacing: "0.05em" }}>
      🎬 场景列表（共 {sceneList.length} 个）
    </h3>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
      {sceneList.map((s, i) => (
        <div key={i} style={{ background: "#1a1d2e", border: "1px solid #2a2d3a", borderRadius: 10, padding: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <input value={s.name} onChange={e => {
              const updated = [...sceneList]; updated[i].name = e.target.value; setSceneList(updated);
            }} style={{ background: "transparent", border: "none", color: "#e2e8f0", fontSize: 14, fontWeight: 700, outline: "none", flex: 1 }} />
            <button onClick={() => setSceneList(p => p.filter((_, idx) => idx !== i))}
              style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: 12 }}>✕</button>
          </div>
          <textarea value={s.desc} onChange={e => {
            const updated = [...sceneList]; updated[i].desc = e.target.value; setSceneList(updated);
          }} placeholder="场景描述..." rows={2}
            style={{ width: "100%", background: "transparent", border: "none", color: "#94a3b8", fontSize: 12, resize: "none", outline: "none", fontFamily: "inherit" }} />
        </div>
      ))}
      <button onClick={() => setSceneList(p => [...p, { id: p.length, name: "新场景", desc: "", atmosphere: "", dna: "" }])}
        style={{ background: "transparent", border: "1px dashed #2a2d3a", borderRadius: 10, color: "#475569", cursor: "pointer", fontSize: 13, padding: 14 }}>
        + 添加场景
      </button>
    </div>
  </div>
)}
```

**Step 5: 验证 — 运行 Step 02，确认 AI 输出后出现可编辑的角色/场景卡片**

---

### Task 5: Step 04 重构 — 角色&场景展示层 + 全局一致性

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` — Step 04

**Step 1: 新增资产展示状态**

```javascript
const [assetPrompts, setAssetPrompts] = useState({}); // { char_0_prompt: "", scene_0_prompt: "" }
```

**Step 2: 重构 Step 04 — 构建角色/场景展示卡片**

将 Step 04 的简单 `GenerateBtn` 替换为：

```javascript
{/* Step 4: Visual Assets */}
{step === 4 && (
  <StepPanel title="Step 04 · 角色 & 场景资产构建" icon="🎭">

    {/* 全局 DNA 锚点信息条 */}
    <div style={{
      background: "linear-gradient(135deg, rgba(99,102,241,0.15), rgba(245,158,11,0.1))",
      border: "1px solid #2a2d3a", borderRadius: 12, padding: "16px 20px",
      marginBottom: 24, display: "flex", gap: 24, alignItems: "center"
    }}>
      <div style={{ color: "#94a3b8", fontSize: 12 }}>
        <div style={{ color: "#a5b4fc", fontWeight: 600, marginBottom: 4 }}>动漫风格</div>
        <div style={{ color: "#e2e8f0", fontSize: 14 }}>{ANIME_STYLES.find(s => s.id === cfg.animeStyle)?.label || "—"}</div>
      </div>
      <div style={{ width: 1, background: "#2a2d3a", height: 40 }} />
      <div style={{ color: "#94a3b8", fontSize: 12 }}>
        <div style={{ color: "#fcd34d", fontWeight: 600, marginBottom: 4 }}>电影风格</div>
        <div style={{ color: "#e2e8f0", fontSize: 14 }}>{MOVIE_STYLES.find(s => s.id === cfg.movieStyle)?.label || "—"}</div>
      </div>
      <div style={{ width: 1, background: "#2a2d3a", height: 40 }} />
      <div style={{ color: "#94a3b8", fontSize: 12 }}>
        <div style={{ color: "#34d399", fontWeight: 600, marginBottom: 4 }}>视频比例</div>
        <div style={{ color: "#e2e8f0", fontSize: 14 }}>{cfg.ratio}</div>
      </div>
      <div style={{ flex: 1, textAlign: "right" }}>
        <div style={{ color: "#64748b", fontSize: 11 }}>全局一致性锚点已锁定</div>
      </div>
    </div>

    <GenerateBtn onClick={genStep4} loading={loading["s4"]} label="🎨 生成一致性资产 Prompt" />
    <OutputBox content={outputs["s4"]} loading={loading["s4"]} />

    {/* 角色资产卡片 */}
    {charList.length > 0 && (
      <div style={{ marginTop: 24 }}>
        <h3 style={{ color: "#818cf8", fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
          👥 角色资产（共 {charList.length} 个）
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {charList.map((c, i) => (
            <div key={i} style={{
              background: "#0f1117", border: "1px solid #2a2d3a", borderRadius: 12, padding: 18,
              position: "relative"
            }}>
              <div style={{
                position: "absolute", top: 14, right: 14,
                background: "rgba(99,102,241,0.2)", borderRadius: 6, padding: "2px 8px",
                fontSize: 10, color: "#a5b4fc", fontWeight: 600
              }}>
                角色 {i + 1}
              </div>
              <div style={{ color: "#e2e8f0", fontSize: 16, fontWeight: 700, marginBottom: 8, marginTop: 4 }}>
                {c.name}
              </div>
              <div style={{ color: "#64748b", fontSize: 12, marginBottom: 10 }}>
                外貌：{c.desc || "（见AI输出）"}
              </div>
              <div style={{ background: "#0a0c14", borderRadius: 8, padding: 12, marginBottom: 10 }}>
                <div style={{ color: "#60a5fa", fontSize: 11, fontWeight: 600, marginBottom: 6, letterSpacing: "0.05em" }}>
                  🎬 一致性生图 Prompt（EN）
                </div>
                <div style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.6 }}>
                  {assetPrompts[`char_${i}`] || `等待生成... ${c.name} character portrait, ${ANIME_STYLES.find(s => s.id === cfg.animeStyle)?.keywords || ""}, ${MOVIE_STYLES.find(s => s.id === cfg.movieStyle)?.keywords || ""}, consistent identity`}
                </div>
              </div>
              <div style={{ background: "#0a0c14", borderRadius: 8, padding: 12 }}>
                <div style={{ color: "#60a5fa", fontSize: 11, fontWeight: 600, marginBottom: 6, letterSpacing: "0.05em" }}>
                  🎬 一致性生图 Prompt（ZH）
                </div>
                <div style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.6 }}>
                  {c.name}角色正面肖像，{ANIME_STYLES.find(s => s.id === cfg.animeStyle)?.label || ""}风格，{MOVIE_STYLES.find(s => s.id === cfg.movieStyle)?.label || ""}质感，{c.desc || ""}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* 场景资产卡片 */}
    {sceneList.length > 0 && (
      <div style={{ marginTop: 24 }}>
        <h3 style={{ color: "#818cf8", fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
          🎬 场景资产（共 {sceneList.length} 个）
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {sceneList.map((s, i) => (
            <div key={i} style={{
              background: "#0f1117", border: "1px solid #2a2d3a", borderRadius: 12, padding: 18,
              position: "relative"
            }}>
              <div style={{
                position: "absolute", top: 14, right: 14,
                background: "rgba(245,158,11,0.2)", borderRadius: 6, padding: "2px 8px",
                fontSize: 10, color: "#fcd34d", fontWeight: 600
              }}>
                场景 {i + 1}
              </div>
              <div style={{ color: "#e2e8f0", fontSize: 16, fontWeight: 700, marginBottom: 8, marginTop: 4 }}>
                {s.name}
              </div>
              <div style={{ color: "#64748b", fontSize: 12, marginBottom: 10 }}>
                氛围：{s.desc || "（见AI输出）"}
              </div>
              <div style={{ background: "#0a0c14", borderRadius: 8, padding: 12 }}>
                <div style={{ color: "#60a5fa", fontSize: 11, fontWeight: 600, marginBottom: 6, letterSpacing: "0.05em" }}>
                  🎬 场景生图 Prompt（EN）
                </div>
                <div style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.6 }}>
                  {assetPrompts[`scene_${i}`] || `等待生成... ${s.name} scene, ${ANIME_STYLES.find(sa => sa.id === cfg.animeStyle)?.keywords || ""}, ${MOVIE_STYLES.find(sm => sm.id === cfg.movieStyle)?.keywords || ""}, cinematic`}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}

    {outputs["s4"] && !loading["s4"] && (
      <button onClick={() => setStep(5)} ...> 打磨最终分镜表 → </button>
    )}
  </StepPanel>
)}
```

**Step 3: 验证 — Step 04 生成后，显示风格锚点条 + 角色/场景卡片网格**

---

### Task 6: Step 05 重构 — 分镜脚本两层 Prompt 分离

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` — Step 05

**Step 1: 新增分镜状态**

```javascript
const [storyboardPrompts, setStoryboardPrompts] = useState({ shot_prompts: [], video_prompts: [] });
```

**Step 2: 重构 genStep5 — 两层 Prompt 生成**

修改 `genStep5` 函数，替换为：

```javascript
function genStep5() {
  const ip = outputs["s2"] || "";
  const script = outputs["s3"] || "";
  const assets = outputs["s4"] || "";
  const animeKw = ANIME_STYLES.find(s => s.id === cfg.animeStyle)?.keywords || "";
  const movieKw = MOVIE_STYLES.find(s => s.id === cfg.movieStyle)?.keywords || "";
  const ratio = cfg.ratio;

  gen("s5",
    `你是资深分镜导演。请严格按以下格式输出两层分镜内容。`,
    `根据以下素材，生成按秒切分的完整分镜脚本。
【格式要求】必须严格按以下 YAML 结构输出，每一镜包含 shot_prompt（生图）和 video_prompt（视频）两个字段：

\`\`\`yaml
shots:
  - shot_number: 1
    duration: 3
    camera: "推镜头"
    description: "画面描述"
    character_dna: "角色名 + 核心外貌"
    scene_dna: "场景名 + 氛围"
    style_lock: "动漫风格 + 电影风格关键词"
    ratio: "${ratio}"
    shot_prompt: "分镜图生成Prompt（用于生成参考图，包含角色DNA+场景DNA+运镜，中英双语）"
    video_prompt: "视频生成Prompt（在shot_prompt基础上，增加时间节奏、运动描述、镜头语言，送入AI视频工具）"
  - shot_number: 2
  ...

---剧本---
${script}
---资产档案---
${assets}
---IP档案---
${ip}
---风格锚点---
动漫：${animeKw}
电影：${movieKw}
比例：${ratio}
---`
  );
}
```

**Step 3: 重构 Step 05 UI — 展示两层 Prompt**

将 Step 05 的 `OutputBox` 替换为分镜表格展示：

```javascript
{/* Step 5: Storyboard */}
{step === 5 && (
  <StepPanel title="Step 05 · 可执行分镜脚本" icon="🎞️">
    <GenerateBtn onClick={genStep5} loading={loading["s5"]} label="🎞️ 生成双层分镜表" />
    <OutputBox content={outputs["s5"]} loading={loading["s5"]} />

    {/* 分镜预览表格 */}
    {outputs["s5"] && !loading["s5"] && (
      <div style={{ marginTop: 24 }}>
        <h3 style={{ color: "#818cf8", fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
          📋 分镜预览（共 X 镜，比例 {cfg.ratio}）
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* TODO: YAML解析输出分镜表格，格式见 Task 8 */}
        </div>
      </div>
    )}

    {outputs["s5"] && !loading["s5"] && (
      <button onClick={() => setStep(6)} ...> 🎉 导出最终项目操作手册 </button>
    )}
  </StepPanel>
)}
```

**Step 4: 验证 — 确认 AI 输出包含 shot_prompt 和 video_prompt 两层字段**

---

### Task 7: 重构全局 Prompt 模板 — 注入 DNA 锚点

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` — genStep1 ~ genStep5

**Step 1: 重构 genStep1 — 注入风格锚点**

```javascript
function genStep1() {
  const animeStyle = ANIME_STYLES.find(s => s.id === cfg.animeStyle);
  const movieStyle = MOVIE_STYLES.find(s => s.id === cfg.movieStyle);
  gen("s1",
    `你是顶级影视/短剧改编编剧。请严格按以下格式输出，保持简洁有力。`,
    `请将以下小说内容改编为AI视频生成专用的标准化剧本改编稿。
【项目信息】
- 项目名：${cfg.title || "未命名"}
- 类型：${cfg.type} / 动漫风格：${animeStyle?.label || "默认"}
- 电影参考：${movieStyle?.label || "默认"}
- 单集时长：${cfg.duration}秒
- 目标平台：${cfg.platform}
- 视频比例：${cfg.ratio}

【改编要求】
1. 删除所有内心独白，全部转化为可见动作/对话/视觉意象
2. 每30秒一个小冲突，每60秒一个情绪转折
3. 每句台词不超过15个中文字符
4. 开场5秒立刻抓取眼球（视觉冲击或情绪冲突）
5. 保持角色外貌描写简洁（≤30字），便于后续一致性生成

---原始素材---
${novel || "（未提供内容）"}
---`
  );
}
```

**Step 2: 重构 genStep3 — 注入双风格锚点**

```javascript
function genStep3() {
  const script = outputs["s1"] || novel;
  const ip = outputs["s2"] || "（IP档案待生成）";
  const animeStyle = ANIME_STYLES.find(s => s.id === cfg.animeStyle);
  const movieStyle = MOVIE_STYLES.find(s => s.id === cfg.movieStyle);

  gen("s3",
    `你是AI漫剧导演。生成包含：剧本内容+导演意图+音频标注的三合一剧本。`,
    `根据改编稿和IP档案，生成第1集的标准化剧本。
【风格锚点】
- 动漫风格：${animeStyle?.label} | ${animeStyle?.keywords || ""}
- 电影参考：${movieStyle?.label} | ${movieStyle?.keywords || ""}
- 视频比例：${cfg.ratio}
- 目标时长：${cfg.duration}秒

【输出要求】
包含详细的景别、情绪值（1-10分）、BGM风格提示、光影风格描述。
${scriptNotes ? `额外要求：${scriptNotes}` : ""}

---改编稿---
${script}
---IP档案---
${ip}
---`
  );
}
```

**Step 3: 重构 genStep4 — 角色/场景Prompt注入**

```javascript
function genStep4() {
  const ip = outputs["s2"] || "（IP档案待生成）";
  const animeStyle = ANIME_STYLES.find(s => s.id === cfg.animeStyle);
  const movieStyle = MOVIE_STYLES.find(s => s.id === cfg.movieStyle);

  gen("s4",
    `你是AI视觉总监。请为AI绘画/视频工具生成精准的 Prompt 参数。`,
    `根据IP档案和风格锚点，生成角色DNA和场景资产的完整Prompt库。
【风格锚点】
- 动漫风格：${animeStyle?.label} | ${animeStyle?.keywords || ""}
- 电影参考：${movieStyle?.label} | ${movieStyle?.keywords || ""}
- 视频比例：${cfg.ratio}

【输出格式】
## 角色资产
### 角色1：{角色名}
- 外貌关键词：{核心外貌，≤20字}
- 服装风格：{服装关键词}
- 一致性生图Prompt（EN）：{英文，中含 ${animeStyle?.keywords || ""} + ${movieStyle?.keywords || ""}}
- 一致性生图Prompt（ZH）：{中文}

## 场景资产
### 场景1：{场景名}
- 时代/地域：{标签}
- 氛围关键词：{氛围描述}
- 场景生图Prompt（EN）：{英文，中含场景名+${animeStyle?.keywords || ""}}
- 场景生图Prompt（ZH）：{中文}

${charNotes ? `特殊要求：${charNotes}` : ""}
---IP档案---
${ip}
---`
  );
}
```

---

### Task 8: 分镜YAML解析 + 表格可视化

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` — Step 05

**Step 1: 添加YAML解析函数**

```javascript
function parseStoryboardYAML(text) {
  // 简单解析YAML格式分镜输出
  const shots = [];
  const lines = text.split("\n");
  let current = null;
  let inShots = false;

  for (const line of lines) {
    if (line.match(/^shots?\s*:$/)) { inShots = true; continue; }
    if (inShots) {
      if (line.match(/^- shot_number:\s*(\d+)/)) {
        if (current) shots.push(current);
        current = { shot_number: RegExp.$1 };
      }
      if (current) {
        const descMatch = line.match(/^\s+description:\s*(.+)/);
        if (descMatch) current.description = descMatch[1];
        const camMatch = line.match(/^\s+camera:\s*(.+)/);
        if (camMatch) current.camera = camMatch[1];
        const durMatch = line.match(/^\s+duration:\s*(\d+)/);
        if (durMatch) current.duration = parseInt(durMatch[1]);
        const shotPMatch = line.match(/^\s+shot_prompt:\s*(.+)/);
        if (shotPMatch) current.shot_prompt = shotPMatch[1];
        const vidPMatch = line.match(/^\s+video_prompt:\s*(.+)/);
        if (vidPMatch) current.video_prompt = vidPMatch[1];
      }
    }
  }
  if (current) shots.push(current);
  return shots;
}
```

**Step 2: 替换 Step 05 的分镜预览区**

将 `分镜预览` 的 TODO 替换为：

```javascript
{outputs["s5"] && !loading["s5"] && (() => {
  const shots = parseStoryboardYAML(outputs["s5"]);
  if (shots.length === 0) return null;
  return (
    <div style={{ marginTop: 24 }}>
      <h3 style={{ color: "#818cf8", fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
        📋 分镜预览（共 {shots.length} 镜 · {cfg.ratio} · {shots.reduce((s, sh) => s + (sh.duration || 0), 0)}秒）
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {shots.map((shot, i) => (
          <div key={i} style={{ background: "#0f1117", border: "1px solid #2a2d3a", borderRadius: 12, padding: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
              <div style={{ background: "#6366f1", color: "#fff", borderRadius: 6, padding: "2px 10px", fontSize: 12, fontWeight: 700 }}>
                镜 {shot.shot_number || i + 1}
              </div>
              <div style={{ color: "#94a3b8", fontSize: 13 }}>
                <span style={{ color: "#60a5fa" }}>{shot.camera || "—"}</span>
                <span style={{ margin: "0 8px", color: "#2a2d3a" }}>|</span>
                {shot.duration || "?"}秒
              </div>
            </div>
            <div style={{ color: "#e2e8f0", fontSize: 13, marginBottom: 12 }}>
              {shot.description || "（见AI输出）"}
            </div>
            <div style={{ background: "#0a0c14", borderRadius: 8, padding: 12, marginBottom: 8 }}>
              <div style={{ color: "#f59e0b", fontSize: 11, fontWeight: 600, marginBottom: 6 }}>🎬 分镜图 Prompt</div>
              <div style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.6, wordBreak: "break-word" }}>
                {shot.shot_prompt || "（见上方AI输出）"}
              </div>
            </div>
            <div style={{ background: "#0a0c14", borderRadius: 8, padding: 12 }}>
              <div style={{ color: "#10b981", fontSize: 11, fontWeight: 600, marginBottom: 6 }}>🎬 视频生成 Prompt</div>
              <div style={{ color: "#94a3b8", fontSize: 12, lineHeight: 1.6, wordBreak: "break-word" }}>
                {shot.video_prompt || "（见上方AI输出）"}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
})()}
```

**Step 3: 验证 — 生成完整分镜后，确认表格正确渲染两层Prompt**

---

### Task 9: 数据持久化 + localStorage 字段升级

**Files:**
- Modify: `AI漫剧项目/manzhou-studio/index.html` — cfg useState + saveCfg

**Step 1: 更新 saveCfg 以支持新字段**

确保 `saveCfg` 完整保存所有 cfg 字段，包括 `animeStyle`、`movieStyle`、`ratio`、`charList`、`sceneList`。

```javascript
function saveCfg(n) {
  try { localStorage.setItem("manzhou_cfg", JSON.stringify(n)); } catch {}
  setCfg(n);
}
```

**Step 2: App 初始化时恢复 charList / sceneList**

在 `cfg` useState 之后添加：

```javascript
const [charList, setCharList] = useState(() => {
  try { return JSON.parse(localStorage.getItem("manzhou_chars")) || []; } catch { return []; }
});
const [sceneList, setSceneList] = useState(() => {
  try { return JSON.parse(localStorage.getItem("manzhou_scenes")) || []; } catch { return []; }
});
```

**Step 3: 添加同步函数**

```javascript
useEffect(() => {
  try { localStorage.setItem("manzhou_chars", JSON.stringify(charList)); } catch {}
}, [charList]);

useEffect(() => {
  try { localStorage.setItem("manzhou_scenes", JSON.stringify(sceneList)); } catch {}
}, [sceneList]);
```

---

### Task 10: 最终验证 + Bug修复

**验证清单：**

1. 打开浏览器，访问 `index.html`
2. Step 00：动漫风格库（12选1）、电影风格库（11选1）、视频比例（4选1）是否正确渲染
3. Step 01：上传 .txt 文件是否显示字数统计，超10万字是否截断
4. Step 02：生成IP档案后是否出现可编辑角色/场景卡片
5. Step 03：生成的剧本是否包含风格锚点信息
6. Step 04：生成后是否显示风格锚点条 + 角色/场景资产卡片（含双语文 Prompt）
7. Step 05：分镜是否显示 shot_prompt 和 video_prompt 两层
8. Step 06：导出手册是否包含所有资产
9. 刷新页面后数据是否持久恢复

---

## 执行顺序

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9 → Task 10
```

**预计代码量**：约 800-1000 行新增/修改
**测试方式**：浏览器手动验证每一 Step
