#!/usr/bin/env python3
"""
art_styles.py — 艺术风格库（Python 版本）

来源：Toonflow artStyle.ts（200+ 风格）+ 漠玫赛博墨韵专属风格

分类：
  常用风格 / IP风格 / 插画风格 / 可爱Q版 / 立体风格 / 日系风格 / 赛博墨韵（漠玫专属）

用途：
  - storyboard-artist 生成分镜脚本时引用风格
  - art-designer 生成角色/场景提示词时锚定风格
  - huage888 工具链中快速查询风格

用法：

  from art_styles import ART_STYLES, get_style, search_styles

  # 按分类查找
  anime = ART_STYLES["常用风格"]
  for s in anime:
      print(f"{s['name']}: {s['prompt']}")

  # 精确查找
  style = get_style("吉卜力")
  print(style["prompt"])

  # 模糊搜索
  results = search_styles("动漫")
  for s in results:
      print(f"  {s['category']}: {s['name']}")
"""

# ─────────────────────────────────────────────────────────────────────────────
# 风格数据（来源：Toonflow artStyle.ts）
# 格式：category → list[StyleItem]
# StyleItem: {name, prompt, prompt_en, file_url}
# ─────────────────────────────────────────────────────────────────────────────

ART_STYLES: dict[str, list[dict]] = {
    # ══════════════════════════════════════════════════════
    "常用风格": [
        {
            "name": "2D动漫风格",
            "prompt": "(画风：2D动漫风格,2d animation style)",
            "prompt_en": "2d animation style",
            "file_url": "https://files.manjuwu.cn/anime/aigc/g/i/68985098-60f1-4b64-b973-64071d95edb3.png",
        },
        {
            "name": "真人写实",
            "prompt": "(画风：照片级真人超写实,photorealistic, lifelike, ultra detailed)",
            "prompt_en": "photorealistic, lifelike, ultra detailed",
            "file_url": "https://files.manjuwu.cn/anime/uploads/other/20260127/025c131413394fb5a9214e00d67ea354.jpg",
        },
        {
            "name": "3D国创",
            "prompt": "(画风：3D国创,Chinese 3D animation style)",
            "prompt_en": "Chinese 3D animation style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/立体风格/3D国创.webp",
        },
        {
            "name": "三渲二",
            "prompt": "(画风：三渲二,cel-shaded)",
            "prompt_en": "cel-shaded",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/三渲二.webp",
        },
        {
            "name": "日式少女漫",
            "prompt": "(画风：日式少女漫,shoujo manga style)",
            "prompt_en": "shoujo manga style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/日式少女漫.webp",
        },
        {
            "name": "龙族传说",
            "prompt": "(画风：龙族传说,dragon clan legend art)",
            "prompt_en": "dragon clan legend art",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/龙族传说.webp",
        },
        {
            "name": "吉卜力",
            "prompt": "(画风：吉卜力,Ghibli style, Studio Ghibli aesthetic)",
            "prompt_en": "Ghibli style, Studio Ghibli aesthetic",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/吉卜力.webp",
        },
        {
            "name": "80s年代",
            "prompt": "(画风：80s年代,1980s retro)",
            "prompt_en": "1980s retro",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/80s年代.webp",
        },
        {
            "name": "木叶村",
            "prompt": "(画风：木叶村,Naruto style, Konohagakure)",
            "prompt_en": "Naruto style, Konohagakure",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/木叶村.webp",
        },
        {
            "name": "名侦探阿楠",
            "prompt": "(画风：名侦探阿楠,Detective Conan style, Case Closed style)",
            "prompt_en": "Detective Conan style, Case Closed style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/名侦探阿楠.webp",
        },
        {
            "name": "草帽团",
            "prompt": "(画风：草帽团,One Piece style, Straw Hat Pirates)",
            "prompt_en": "One Piece style, Straw Hat Pirates",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/草帽团.webp",
        },
        {
            "name": "比奇堡",
            "prompt": "(画风：比奇堡,SpongeBob style, Bikini Bottom)",
            "prompt_en": "SpongeBob style, Bikini Bottom",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/比奇堡.webp",
        },
        {
            "name": "蜡笔小新",
            "prompt": "(画风：蜡笔小新,Crayon Shin-chan style)",
            "prompt_en": "Crayon Shin-chan style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/蜡笔小新.webp",
        },
        {
            "name": "动森",
            "prompt": "(画风：动森,Animal Crossing style)",
            "prompt_en": "Animal Crossing style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/动森.webp",
        },
        {
            "name": "写实都市",
            "prompt": "(画风：写实都市,photorealistic urban, modern city)",
            "prompt_en": "photorealistic urban, modern city",
            "file_url": "",
        },
        {
            "name": "水彩插画",
            "prompt": "(画风：水彩插画,watercolor illustration)",
            "prompt_en": "watercolor illustration",
            "file_url": "",
        },
    ],

    # ══════════════════════════════════════════════════════
    "IP风格": [
        {
            "name": "龙族传说",
            "prompt": "(画风：龙族传说,dragon clan legend art)",
            "prompt_en": "dragon clan legend art",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/龙族传说.webp",
        },
        {
            "name": "比奇堡",
            "prompt": "(画风：比奇堡,SpongeBob style, Bikini Bottom)",
            "prompt_en": "SpongeBob style, Bikini Bottom",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/比奇堡.webp",
        },
        {
            "name": "蜡笔小新",
            "prompt": "(画风：蜡笔小新,Crayon Shin-chan style)",
            "prompt_en": "Crayon Shin-chan style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/蜡笔小新.webp",
        },
        {
            "name": "动森",
            "prompt": "(画风：动森,Animal Crossing style)",
            "prompt_en": "Animal Crossing style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/动森.webp",
        },
        {
            "name": "木叶村",
            "prompt": "(画风：木叶村,Naruto style, Konohagakure)",
            "prompt_en": "Naruto style, Konohagakure",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/ip风格/木叶村.webp",
        },
        {
            "name": "草帽团",
            "prompt": "(画风：草帽团,One Piece style, Straw Hat Pirates)",
            "prompt_en": "One Piece style, Straw Hat Pirates",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/草帽团.webp",
        },
    ],

    # ══════════════════════════════════════════════════════
    "插画风格": [
        {
            "name": "浮世绘",
            "prompt": "(画风：浮世绘,Ukiyo-e, traditional Japanese woodblock print)",
            "prompt_en": "Ukiyo-e, traditional Japanese woodblock print",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/浮世绘.webp",
        },
        {
            "name": "波普印刷",
            "prompt": "(画风：波普印刷,pop art, Andy Warhol style)",
            "prompt_en": "pop art, Andy Warhol style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/波普印刷.webp",
        },
        {
            "name": "哥特霓虹",
            "prompt": "(画风：哥特霓虹,gothic neon, dark cyberpunk illustration)",
            "prompt_en": "gothic neon, dark cyberpunk illustration",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/哥特霓虹.webp",
        },
        {
            "name": "水彩",
            "prompt": "(画风：水彩,watercolor)",
            "prompt_en": "watercolor",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/水彩.webp",
        },
        {
            "name": "油画釉光",
            "prompt": "(画风：油画釉光,oily paint, enamel glaze effect)",
            "prompt_en": "oily paint, enamel glaze effect",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/油画釉光.webp",
        },
        {
            "name": "藤本树风格",
            "prompt": "(画风：藤本树风格,Tatsumoto Fujimoto style, chainsaw man art)",
            "prompt_en": "Tatsumoto Fujimoto style, chainsaw man art",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/藤本树风格.webp",
        },
        {
            "name": "日式少女漫",
            "prompt": "(画风：日式少女漫,shoujo manga style)",
            "prompt_en": "shoujo manga style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/插画风格/日式少女漫.webp",
        },
    ],

    # ══════════════════════════════════════════════════════
    "可爱Q版": [
        {
            "name": "Q版3D",
            "prompt": "(画风：Q版3D,chibi 3D, super deformed 3D)",
            "prompt_en": "chibi 3D, super deformed 3D",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/可爱Q版/Q版3D.webp",
        },
        {
            "name": "火柴人",
            "prompt": "(画风：火柴人,stick figure animation)",
            "prompt_en": "stick figure animation",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/可爱Q版/火柴人.webp",
        },
        {
            "name": "像素",
            "prompt": "(画风：像素,pixel art, 8-bit)",
            "prompt_en": "pixel art, 8-bit",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/可爱Q版/像素.webp",
        },
        {
            "name": "日本小人",
            "prompt": "(画风：日本小人,Japanese chibi illustration)",
            "prompt_en": "Japanese chibi illustration",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/可爱Q版/日本小人.webp",
        },
        {
            "name": "微缩景观",
            "prompt": "(画风：微缩景观,miniature world, tilt-shift)",
            "prompt_en": "miniature world, tilt-shift",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/可爱Q版/微缩景观.webp",
        },
    ],

    # ══════════════════════════════════════════════════════
    "立体风格": [
        {
            "name": "方块世界",
            "prompt": "(画风：方块世界,Minecraft style, voxel art)",
            "prompt_en": "Minecraft style, voxel art",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/立体风格/方块世界.webp",
        },
        {
            "name": "折纸艺术",
            "prompt": "(画风：折纸艺术,origami art, paper craft)",
            "prompt_en": "origami art, paper craft",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/立体风格/折纸艺术.webp",
        },
        {
            "name": "莱卡定格",
            "prompt": "(画风：莱卡定格,stop-motion Laika style)",
            "prompt_en": "stop-motion Laika style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/立体风格/莱卡定格.webp",
        },
        {
            "name": "3D国创",
            "prompt": "(画风：3D国创,Chinese 3D animation style)",
            "prompt_en": "Chinese 3D animation style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/立体风格/3D国创.webp",
        },
    ],

    # ══════════════════════════════════════════════════════
    "日系风格": [
        {
            "name": "三渲二",
            "prompt": "(画风：三渲二,cel-shaded)",
            "prompt_en": "cel-shaded",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/三渲二.webp",
        },
        {
            "name": "吉卜力",
            "prompt": "(画风：吉卜力,Ghibli style, Studio Ghibli aesthetic)",
            "prompt_en": "Ghibli style, Studio Ghibli aesthetic",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/吉卜力.webp",
        },
        {
            "name": "龙族传说",
            "prompt": "(画风：龙族传说,dragon clan legend art)",
            "prompt_en": "dragon clan legend art",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/龙族传说.webp",
        },
        {
            "name": "藤本树风格",
            "prompt": "(画风：藤本树风格,Tatsumoto Fujimoto style, chiansaw man art)",
            "prompt_en": "Tatsumoto Fujimoto style, chiansaw man art",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/藤本树风格.webp",
        },
        {
            "name": "日式少女漫",
            "prompt": "(画风：日式少女漫,shoujo manga style)",
            "prompt_en": "shoujo manga style",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/日式少女漫.webp",
        },
        {
            "name": "草帽团",
            "prompt": "(画风：草帽团,One Piece style, Straw Hat Pirates)",
            "prompt_en": "One Piece style, Straw Hat Pirates",
            "file_url": "https://files.manjuwu.cn//app/FilmStyle/V1/日系风格/草帽团.webp",
        },
    ],

    # ══════════════════════════════════════════════════════
    "赛博墨韵（漠玫专属）": [
        {
            "name": "流动墨滴",
            "prompt": "(画风：赛博墨韵,流动墨滴数据流,金色瞳孔数据流,青蓝水墨眼线,道姑髻,数字东方)",
            "prompt_en": "cyber ink style, flowing ink drop data stream, golden pupil data flow, cyan-blue ink eye line, Taoist bun hairstyle, digital Oriental",
            "file_url": "",
            "note": "漠玫核心风格锚点",
        },
        {
            "name": "金色瞳孔数据流",
            "prompt": "(画风：赛博墨韵,金色瞳孔内数据流,墨色眼线,道姑髻,数字禅意)",
            "prompt_en": "cyber ink, golden pupil with data stream, ink-lined eyes, Taoist bun, digital Zen",
            "file_url": "",
            "note": "漠玫标志性视觉元素",
        },
        {
            "name": "青蓝水墨眼线",
            "prompt": "(画风：赛博墨韵,青蓝色水墨眼线,墨色瞳孔,道姑髻簪数据簪,古典禅意)",
            "prompt_en": "cyber ink, cyan-blue ink eye line, ink pupil, Taoist bun with data hairpin, classical Zen",
            "file_url": "",
            "note": "漠玫角色特征",
        },
        {
            "name": "赛博竹林",
            "prompt": "(画风：赛博墨韵,数字竹林,水墨竹叶,霓虹光斑,东方赛博,烟雾朦胧)",
            "prompt_en": "cyber bamboo forest, ink bamboo leaves, neon light spots, Oriental cyberpunk, misty",
            "file_url": "",
            "note": "漠玫场景风格",
        },
        {
            "name": "墨色赛博城",
            "prompt": "(画风：赛博墨韵,墨色城市,霓虹光效,水墨云雾,东方赛博朋克)",
            "prompt_en": "ink city, neon light, ink mist clouds, Oriental cyberpunk",
            "file_url": "",
            "note": "漠玫城市场景",
        },
        {
            "name": "断桥墨雨",
            "prompt": "(画风：赛博墨韵,西湖断桥,墨色雨丝,青蓝水墨,数字东方,烟雾朦胧)",
            "prompt_en": "cyber ink, West Lake broken bridge, ink rain threads, cyan-blue ink, digital Oriental, misty",
            "file_url": "",
            "note": "断桥奇遇场景风格",
        },
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 查询函数
# ─────────────────────────────────────────────────────────────────────────────

def get_style(name: str) -> dict | None:
    """
    精确查找风格

    Args:
        name: 风格名称

    Returns:
        风格字典，未找到返回 None
    """
    for category, styles in ART_STYLES.items():
        for style in styles:
            if style["name"] == name:
                return style
    return None


def search_styles(keyword: str, case_sensitive: bool = False) -> list[dict]:
    """
    模糊搜索风格（搜索名称和 prompt）

    Args:
        keyword: 搜索关键词
        case_sensitive: 是否区分大小写

    Returns:
        匹配的风格列表（按类别和名称排序）
    """
    results = []
    kw = keyword if case_sensitive else keyword.lower()

    for category, styles in ART_STYLES.items():
        for style in styles:
            searchable = " ".join([
                style["name"],
                style["prompt"],
                style.get("prompt_en", ""),
                style.get("note", ""),
            ])
            search_text = searchable if case_sensitive else searchable.lower()

            if kw in search_text:
                results.append({**style, "category": category})

    return results


def get_styles_by_category(category: str) -> list[dict]:
    """获取指定类别的所有风格"""
    return ART_STYLES.get(category, [])


def all_styles() -> list[dict]:
    """获取所有风格（展平）"""
    results = []
    for category, styles in ART_STYLES.items():
        for style in styles:
            results.append({**style, "category": category})
    return results


def render_style_prompt(style_name: str, extra: str = "") -> str:
    """
    渲染风格 prompt（用于生成调用）

    Args:
        style_name: 风格名称
        extra: 额外追加的内容

    Returns:
        完整的 prompt 字符串
    """
    style = get_style(style_name)
    if not style:
        return extra

    prompt_parts = [style["prompt"]]
    if extra:
        prompt_parts.append(extra)
    return "，".join(prompt_parts)


def recommend_styles_for_project(project_type: str) -> list[dict]:
    """
    根据项目类型推荐风格

    Args:
        project_type: 项目类型（如 "古风" / "赛博" / "动漫" / "写实"）

    Returns:
        推荐风格列表
    """
    recommendations = {
        "赛博": ["流动墨滴", "赛博竹林", "墨色赛博城", "金色瞳孔数据流", "哥特霓虹"],
        "古风": ["浮世绘", "水墨", "写实都市"],
        "动漫": ["吉卜力", "日式少女漫", "三渲二", "Q版3D"],
        "写实": ["真人写实", "写实都市", "莱卡定格"],
        "可爱": ["Q版3D", "像素", "动森", "日本小人"],
        "IP": ["蜡笔小新", "草帽团", "木叶村", "龙族传说"],
        "短剧": ["真人写实", "3D国创", "赛博竹林", "油画釉光"],
    }

    recommended_names = recommendations.get(project_type, [])
    results = []
    for name in recommended_names:
        style = get_style(name)
        if style:
            results.append(style)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="huage888 艺术风格库")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有风格")
    p_cat = sub.add_parser("category", help="列出指定类别")
    p_cat.add_argument("category", help="类别名称")

    p_get = sub.add_parser("get", help="精确查找风格")
    p_get.add_argument("name", help="风格名称")

    p_search = sub.add_parser("search", help="搜索风格")
    p_search.add_argument("keyword", help="搜索关键词")

    p_rec = sub.add_parser("recommend", help="推荐风格")
    p_rec.add_argument("project_type", help="项目类型（赛博/古风/动漫/写实/可爱/IP/短剧）")

    args = parser.parse_args()

    if args.cmd == "list":
        for cat, styles in ART_STYLES.items():
            print(f"\n【{cat}】({len(styles)} 种)")
            for s in styles:
                note = f" | {s['note']}" if s.get("note") else ""
                print(f"  {s['name']}{note}")

    elif args.cmd == "category":
        styles = get_styles_by_category(args.category)
        if not styles:
            print(f"未知类别：{args.category}，可用：{list(ART_STYLES.keys())}")
            return
        print(f"【{args.category}】")
        for s in styles:
            print(f"  {s['name']}: {s['prompt']}")

    elif args.cmd == "get":
        style = get_style(args.name)
        if not style:
            print(f"未找到风格：{args.name}")
            return
        import json
        print(json.dumps(style, ensure_ascii=False, indent=2))

    elif args.cmd == "search":
        results = search_styles(args.keyword)
        print(f"找到 {len(results)} 个匹配：")
        for s in results:
            print(f"  [{s['category']}] {s['name']}: {s['prompt'][:60]}...")

    elif args.cmd == "recommend":
        results = recommend_styles_for_project(args.project_type)
        print(f"为「{args.project_type}」推荐风格：")
        for s in results:
            print(f"  {s['name']}: {s['prompt']}")


if __name__ == "__main__":
    _cli()
