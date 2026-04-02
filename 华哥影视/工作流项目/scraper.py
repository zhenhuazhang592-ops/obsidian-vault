"""
ComfyUI Workflow Scraper (v2)
健壮版：固定超时 + 跳过已处理 + 实时输出
"""

import json
import re
import os
import sys
import time
import traceback
from playwright.sync_api import sync_playwright


BASE_DIR = "/Users/huage/Obsidian Vault/工作流项目"
EXPLORE_URL = "https://comfy.icu/explore"
GLOBAL_TIMEOUT = 25000  # 25s per page


def log(msg: str):
    print(msg, flush=True)


def sanitize(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return (name or "unnamed")[:80]


def get_wf_id(href: str) -> str | None:
    m = re.match(r'/workflows/([^/]+)', href)
    return m.group(1) if m else None


def parse_prompt_json(text: str) -> dict | None:
    """括号追踪器提取 const prompt = {...}"""
    idx = text.find("const prompt = ")
    if idx < 0:
        return None
    start = idx + len("const prompt = ")
    depth, in_str, str_char, end = 0, False, None, None
    for i, c in enumerate(text[start:], start):
        if not in_str:
            if c in '"\'':
                in_str, str_char = True, c
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        else:
            if c == str_char and (i == 0 or text[i - 1] != '\\'):
                in_str = False
    if end:
        try:
            return json.loads(text[start:end])
        except Exception:
            return None
    return None


def extract_meta(page) -> dict:
    for s in page.query_selector_all("script[type='application/json']"):
        try:
            data = json.loads(s.inner_text())
            pp = data.get('props', {}).get('pageProps', {})
            if 'workflow' in pp:
                wf = pp['workflow']
                return {
                    "id": wf.get("id"),
                    "name": wf.get("name"),
                    "description": wf.get("description"),
                    "created_at": wf.get("created_at"),
                    "updated_at": wf.get("updated_at"),
                    "tags": wf.get("tags", []),
                    "visibility": wf.get("visibility"),
                    "user": wf.get("user", {}).get("name"),
                    "accelerator": wf.get("accelerator"),
                    "models": wf.get("models"),
                }
        except Exception:
            continue
    return {}


def scrape_one(browser, wf_id: str, fallback_name: str) -> dict | None:
    """抓取单个 workflow"""
    page = browser.new_page(viewport={"width": 1400, "height": 900})

    try:
        page.goto(f"https://comfy.icu/workflows/{wf_id}",
                  wait_until="commit", timeout=GLOBAL_TIMEOUT)
        page.wait_for_timeout(3000)  # 等 JS 渲染
    except Exception as e:
        log(f"    → 导航失败: {e}")
        page.close()
        return None

    meta = extract_meta(page)
    name = sanitize(meta.get("name") or fallback_name or f"wf_{wf_id[:8]}")
    folder = os.path.join(BASE_DIR, name)
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, "workflow.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # API Workflow tab
    try:
        page.get_by_text("API Workflow").click(timeout=5000)
        page.wait_for_timeout(1500)
    except Exception:
        pass

    # View API code
    try:
        page.get_by_text("View API code").click(timeout=5000)
        page.wait_for_timeout(2000)
    except Exception:
        pass

    # 提取 pre 标签
    api_wf_text, api_code_text, prompt_json = None, None, None
    parts = []

    for pre in page.query_selector_all("pre"):
        text = pre.inner_text().strip()
        if not text:
            continue
        if text.startswith("const workflow_id") or text.startswith("// Workflow JSON"):
            if api_wf_text is None:
                api_wf_text = text
                prompt_json = parse_prompt_json(text)
        elif text.startswith("npm install") or text.startswith("export COMFY"):
            if text not in parts:
                parts.append(text)

    if parts:
        api_code_text = "\n\n".join(parts)

    if api_wf_text:
        with open(os.path.join(folder, "api-workflow.json"), "w", encoding="utf-8") as f:
            f.write(api_wf_text)

    if api_code_text:
        with open(os.path.join(folder, "api-code.js"), "w", encoding="utf-8") as f:
            f.write(api_code_text)

    # 下载输入文件
    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}
    input_files = []
    if prompt_json:
        for node_id, node in prompt_json.items():
            for key, val in node.get("inputs", {}).items():
                if isinstance(val, str):
                    ext = os.path.splitext(val)[1].lower()
                    if ext in IMAGE_EXTS:
                        input_files.append((val, node_id, key))

    if input_files:
        input_dir = os.path.join(folder, "input")
        os.makedirs(input_dir, exist_ok=True)
        for filename, node_id, field in input_files:
            local = os.path.join(input_dir, filename)
            if os.path.exists(local):
                continue
            file_url = f"https://comfy.icu/api/v1/view/workflows/{wf_id}/input/{filename}"
            try:
                p2 = browser.new_page()
                resp = p2.goto(file_url, timeout=15000)
                if resp and resp.status in (200, 307, 308):
                    with open(local, "wb") as out:
                        out.write(resp.body())
                    log(f"    [下载] {filename}")
                p2.close()
            except Exception:
                pass

    page.close()

    return {
        "id": wf_id,
        "name": name,
        "folder": folder,
        "has_meta": bool(meta),
        "has_api_wf": api_wf_text is not None,
        "has_code": api_code_text is not None,
        "files": len(input_files),
    }


def main():
    log("=" * 60)
    log("ComfyUI Workflow Scraper v2")
    log(f"输出: {BASE_DIR}")
    log("=" * 60)

    os.makedirs(BASE_DIR, exist_ok=True)
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ── 1. 扫描 explore ─────────────────────────────────────
        log("\n[1/2] 扫描 Explore...")
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(EXPLORE_URL, wait_until="commit", timeout=GLOBAL_TIMEOUT)
        page.wait_for_timeout(3000)

        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)

        seen, workflows = set(), []
        for card in page.query_selector_all("a[href*='/workflows/']"):
            href = card.get_attribute("href") or ""
            wf_id = get_wf_id(href)
            if wf_id and wf_id not in seen:
                seen.add(wf_id)
                workflows.append(wf_id)
        page.close()
        log(f"  发现 {len(workflows)} 个 workflows\n")

        # ── 2. 逐个抓取 ───────────────────────────────────────
        log(f"[2/2] 开始抓取...")
        for i, wf_id in enumerate(workflows):
            log(f"[{i+1:3d}/{len(workflows)}] {wf_id[:20]}...")
            try:
                result = scrape_one(browser, wf_id, None)
                if result:
                    results.append(result)
                    flags = []
                    if result["has_meta"]:   flags.append("meta")
                    if result["has_api_wf"]: flags.append("api-wf")
                    if result["has_code"]:   flags.append("code")
                    if result["files"]:      flags.append(f"+{result['files']}files")
                    log(f"    → {result['name'][:40]} [{' '.join(flags)}]")
                else:
                    log(f"    → ✗ 失败")
            except Exception as e:
                log(f"    → ✗ {e}")
            if (i + 1) % 10 == 0:
                log(f"  进度: {i+1}/{len(workflows)}")

        browser.close()

    # ── 汇总 ──────────────────────────────────────────────────
    ok = [r for r in results if r["has_api_wf"]]
    report = {
        "total": len(workflows),
        "scraped": len(results),
        "with_api_workflow": len(ok),
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "workflows": [{"id": r["id"], "name": r["name"]} for r in results],
    }
    path = os.path.join(BASE_DIR, "index.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    log(f"\n{'=' * 60}")
    log(f"完成！{len(results)}/{len(workflows)} 个（含 {len(ok)} 个完整 API Workflow）")
    log(f"汇总: {path}")
    log("=" * 60)


if __name__ == "__main__":
    main()
