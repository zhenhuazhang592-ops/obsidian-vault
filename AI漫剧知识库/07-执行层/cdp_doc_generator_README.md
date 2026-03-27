# 漫舟CDP文档生成器 · 使用说明

## 功能

自动读取CDP JSON → 生成完整项目文档包

## 安装依赖

```bash
pip install markdown jinja2
```

## 使用方式

### 方式1：从文件读取

```bash
python cdp_doc_generator.py --input ./CDP-JSON.md --output ./output/
```

### 方式2：直接传入JSON

```bash
python cdp_doc_generator.py --content '{"version":"1.0",...}' --output ./output/
```

### 方式3：在Python中调用

```python
from cdp_doc_generator import generate_all_documents, save_documents

# 读取CDP JSON文件
with open("CDP-JSON.md", "r") as f:
    cdp_content = f.read()

# 生成所有文档
files = generate_all_documents(cdp_content, "./output")

# 保存文档
save_documents(files, "./output")
```

## 输出文件结构

```
output/
├── 00-项目信息/
│   ├── 全局设置.md           # 步骤1产出
│   └── 导出配置单.md         # 步骤6产出
├── 01-CDP资产包/
│   └── CDP-JSON.md         # 步骤2产出（原始JSON）
├── 02-资产库/
│   ├── 资产库.md            # 步骤3产出
│   ├── 角色资产.md
│   ├── 场景资产.md
│   ├── 道具资产.md
│   └── 生成任务表.md
├── 03-分镜脚本/
│   ├── 分镜脚本总览.md
│   ├── 第01集-分镜脚本.md
│   ├── 第02集-分镜脚本.md
│   └── ...
├── 04-视频文件/
│   └── 视频生成任务清单.md   # 步骤5产出
└── README.md               # 项目总览
```

## 生成的文档说明

### 1. 全局设置.md
- 项目基本信息
- 视觉规格
- 统计数据
- 生成工具配置

### 2. 资产库.md / 角色资产.md / 场景资产.md / 道具资产.md
- 完整的角色/场景/道具描述
- AI生图Prompt建议
- 生成任务清单

### 3. 分镜脚本.md
- 每个镜头的完整信息
- imagePrompt + videoPrompt
- 九宫格分镜Prompt
- action三段式

### 4. 视频生成任务清单.md
- 所有videoPrompt汇总
- 生成参数配置
- 质量检查清单
- 失败重试策略

### 5. 导出配置单.md
- 项目信息汇总
- 导出检查清单
- 剪映剪辑指引
- 发布建议

## 提示

- 不需要安装可选依赖（markdown/jinja2），核心功能不需要它们
- 支持从Markdown代码块中提取JSON
- 支持带YAML front matter的文件

## 示例

```bash
# 使用示例CDP JSON测试
python cdp_doc_generator.py --input ./示例CDP-JSON.md --output ./test_output/
```
