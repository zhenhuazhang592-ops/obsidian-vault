# Task Plan: gongzhonghao + md2wechat 集成

## Goal
在 gongzhonghao skill 中集成 md2wechat 的核心功能：Markdown→HTML排版、封面图上传、微信草稿箱推送。

## Phases

- [ ] Phase 1: 创建wechat-api模块（封装微信API调用）
- [ ] Phase 2: 创建md2html模块（Markdown→微信HTML转换）
- [ ] Phase 3: 创建publish模块（封面上传+草稿箱推送）
- [ ] Phase 4: 更新EXTEND.md（添加md2wechat API配置）
- [ ] Phase 5: 更新SKILL.md（添加/gongzhonghao publish命令）
- [ ] Phase 6: 测试完整流程

## Key Questions

1. 是否需要安装md2wechat CLI，还是直接调用API？
2. 使用md2wechat.cn的API还是自建API服务？
3. 配图如何处理（上传到微信还是用URL）？

## Decisions Made

- 使用md2wechat.cn的API服务（无需安装CLI）
- 封面图上传到微信素材库获取media_id
- 文章配图使用在线URL（需转存到微信）或本地路径
- Go SDK改用Python requests封装（gongzhonghao是skill而非独立CLI）

## 微信API集成方案

### 流程
```
1. 获取 access_token（带缓存，2小时有效）
2. 上传封面图 → thumb_media_id
3. 转换Markdown → HTML（调用md2wechat.cn API）
4. 上传文章内图片 → 替换src为微信URL
5. 推送到草稿箱
```

### 需要封装的API

| 功能 | API | 参数 |
|------|-----|------|
| 获取token | /cgi-bin/token | appid, secret |
| 上传图片 | /cgi-bin/media/upload | access_token, type=image, file |
| 创建草稿 | /cgi-bin/draft/add | access_token, articles[] |

## Files to Create/Modify

| 文件 | 操作 | 说明 |
|------|------|------|
| `EXTEND.md` | 修改 | 添加md2wechat API Key配置 |
| `wechat-api.md` | 新建 | 微信API封装文档 |
| `publish-command.md` | 新建 | /gongzhonghao publish 命令 |
| `prompts/publish-template.md` | 新建 | 草稿箱推送模板 |

## Status
**Phase 1-5 完成** - 准备 Phase 6 测试完整流程

## 新增模块文件

| 文件 | 作用 | 状态 |
|------|------|------|
| `wechat-api.md` | 微信API封装 | ✅ |
| `md2html.md` | Markdown→HTML转换 | ✅ |
| `publish-command.md` | /gongzhonghao publish 命令 | ✅ |
| `EXTEND.md` 更新 | md2wechat API 配置 | ✅ |
| `SKILL.md` 更新 | 添加 publish 命令 | ✅ |
