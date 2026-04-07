# skills/libtv-huage-integration.md — huage888 → LibTV 交接规范（手动执行版）

> huage888 系统 | 用户手动执行
> 目的：明确 huage888 产出物如何交给用户在 LibTV 手动执行
> LibTV Skill 位置：`.claude/skills/libtv-skill/SKILL.md`

---

## 一、交接原则

> **本版本不调用 API。** 所有生成操作由用户在 LibTV 手动完成。

1. **huage888 产出操作指南，用户照做**
2. **huage888 生成完整 Prompt，用户复制到 LibTV**
3. **用户负责在 LibTV 执行、下载、填入 element_id**
4. **huage888 只做创意管理和质量守门，不直接调用任何 API**

---

## 二、执行流程

```
huage888                           用户（在 LibTV 手动操作）
─────────────────────────────────  ───────────────────────────────────────
生成 assets/*.json spec            打开 liblib.tv
生成操作指南                        新建 Project
                                   按指南复制 Prompt 到 Session
                                   操作 → 生成图片/视频
                                   下载结果 → 填入 element_id
                                   回到 huage888 → 继续下一步
```

---

## 三、LibTV 手动操作节点

### 节点 1：Phase 1 锚点图（阶段二末尾）

**huage888 产出：**
- `assets/character-front-view.json` — 角色正面图 spec
- `assets/scene-establishing.json` — 场景全景图 spec

**huage888 执行：**
加载 `libtv-skill/SKILL.md`，读取 JSON spec，生成「角色正面图操作指南」和「场景全景图操作指南」。

**用户操作：**
1. 打开 [LibTV](https://www.liblib.tv/)，新建 Project
2. 按操作指南，在 LibTV 中选择 nanobanana 模型
3. 复制 Prompt，粘贴到 Session，发送
4. 等待生成完成，下载图片
5. 在 LibTV 画布中选中图片 → 复制 element_id
6. 将 element_id 填入 `assets/character-sheet.json` / `assets/scene-sheet.json`

---

### 节点 2：Phase 2 多角度图（阶段二末尾）

**huage888 产出：**
- `assets/character-sheet.json` — 角色多角度 spec（已含 element_id）
- `assets/scene-sheet.json` — 场景多角度 spec（已含 element_id）

**huage888 执行：**
加载 `libtv-skill/SKILL.md`，读取 JSON spec，生成「角色多角度操作指南」和「场景多角度操作指南」。

**用户操作：**
1. 在 LibTV 新建 Session
2. 按操作指南，选择 nanobanana 模型，复制 Prompt 发送
3. 等待生成完成，下载多角度图
4. 将图片 URL 填入 `assets/03-asset-registry.md`

---

### 节点 3：分镜视频生成（阶段三末尾）

**huage888 产出：**
- `outputs/02-storyboard-script.md` — 完整分镜脚本
- `assets/03-asset-registry.md` — 资产注册表（含所有 element_id）

**huage888 执行：**
加载 `libtv-skill/SKILL.md`，读取分镜脚本和资产注册表，生成「分镜批量视频操作指南」。

**用户操作：**
1. 在 LibTV 新建 Project
2. 选择视频模型 Kling O1（或 Wan 2.6）
3. 按操作指南，逐镜头发送 Prompt
4. 每个镜头生成完成 → 下载到本地
5. 手动剪辑合成 → 最终成片

---

## 四、操作检查清单（交接前必查）

- [ ] `assets/character-sheet.json` 中所有角色 element_id 已填写（Phase 1 完成后）
- [ ] `assets/scene-sheet.json` 中所有场景 element_id 已填写（Phase 1 完成后）
- [ ] `assets/03-asset-registry.md` 中所有图片 URL 已填写（Phase 2 完成后）
- [ ] 02-storyboard-script.md 中主体引用与 asset-registry 对应无误
- [ ] 分镜脚本总时长与目标时长匹配
- [ ] 合规审核全部通过
- [ ] 用户已理解操作指南，无疑问

---

## 五、脚本文件说明（仅供参考，不执行）

以下脚本保留在 `.claude/skills/libtv-skill/scripts/` 目录下，仅作参考：

| 脚本 | 用途 | 本版本 |
|------|------|--------|
| `_common.py` | 结构化消息模板 | 参考 |
| `create_structured_session.py` | 创建会话 | **不执行** |
| `create_session.py` | 旧版创建会话 | **不执行** |
| `query_session.py` | 轮询进展 | **不执行** |
| `upload_file.py` | 上传文件 | **不执行** |
| `download_results.py` | 下载结果 | **不执行** |
| `change_project.py` | 切换项目 | **不执行** |
| `convert_to_libtv_spec.py` | Markdown → JSON | 参考 |
