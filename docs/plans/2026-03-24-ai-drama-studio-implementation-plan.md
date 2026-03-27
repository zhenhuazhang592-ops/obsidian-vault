# AI漫剧工业化生产系统 · 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个人机协作的AI漫剧工业化生产系统，包含React前端 + Claude多Agent + Obsidian + SQLite

**Architecture:**
- 前端：React + Vite + SQLite (better-sqlite3)
- 创作引擎：Claude Code 多Agent协同
- 存储：Obsidian Vault (Markdown内容) + SQLite (结构化数据)
- 工作流：并行初稿 → 串行精调 → 人工审核节点

**Tech Stack:** React 18, Vite, TypeScript, better-sqlite3, Claude API, Obsidian CLI

---

## 执行阶段概览

| 阶段 | 任务数 | 核心目标 |
|------|--------|---------|
| Phase 1 | 8 | 前端基础设施搭建 |
| Phase 2 | 6 | 前端核心UI功能 |
| Phase 3 | 7 | Claude Agent系统构建 |
| Phase 4 | 5 | 工作流与存储集成 |
| Phase 5 | 3 | 端到端测试 |

**总计：29个任务**

---

## Phase 1: 前端基础设施搭建

### Task 1: 创建 React + Vite 项目

**Files:**
- Create: `ai-drama-studio/package.json`
- Create: `ai-drama-studio/vite.config.ts`
- Create: `ai-drama-studio/tsconfig.json`
- Create: `ai-drama-studio/index.html`
- Create: `ai-drama-studio/src/main.tsx`
- Create: `ai-drama-studio/src/App.tsx`

**Step 1: 初始化项目**

```bash
cd /Users/huage/Obsidian\ Vault
mkdir -p ai-drama-studio
cd ai-drama-studio
npm init -y
npm install react@18 react-dom@18 vite@5 @vitejs/plugin-react@4 typescript@5
npm install -D @types/react@18 @types/react-dom@18
```

**Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})
```

**Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

**Step 4: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <title>AI漫剧工业化生产系统</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 5: 创建 src/main.tsx**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

**Step 6: 创建 src/App.tsx**

```tsx
function App() {
  return <div>AI漫剧工业化生产系统</div>
}

export default App
```

**Step 7: 启动验证**

```bash
cd ai-drama-studio && npm run dev
```
Expected: Dev server starts on port 3000

**Step 8: 提交**

```bash
git add -A && git commit -m "feat: scaffold React + Vite project"
```

---

### Task 2: 安装并配置 SQLite (better-sqlite3)

**Files:**
- Modify: `ai-drama-studio/package.json`
- Create: `ai-drama-studio/src/db/database.ts`
- Create: `ai-drama-studio/src/db/schema.ts`

**Step 1: 安装 better-sqlite3**

```bash
cd ai-drama-studio
npm install better-sqlite3@11
npm install -D @types/better-sqlite3
```

**Step 2: 创建 src/db/schema.ts**

```typescript
export const SCHEMA = `
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  source TEXT,
  type TEXT DEFAULT 'modern',
  episode_count INTEGER DEFAULT 12,
  status TEXT DEFAULT 'draft',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS characters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  identity TEXT,
  visual_tags TEXT,
  reference_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS shots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  episode INTEGER NOT NULL,
  scene TEXT,
  shot_order INTEGER NOT NULL,
  camera_type TEXT,
  movement TEXT,
  action TEXT,
  prompt TEXT,
  bgm TEXT,
  sfx TEXT,
  vo_emotion TEXT,
  status TEXT DEFAULT 'pending',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS scenes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  location_type TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id)
);
`
```

**Step 3: 创建 src/db/database.ts**

```typescript
import Database from 'better-sqlite3'
import { SCHEMA } from './schema'

const DB_PATH = './ai-drama-studio.db'

let db: Database.Database | null = null

export function getDatabase(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH)
    db.exec(SCHEMA)
  }
  return db
}

export function closeDatabase(): void {
  if (db) {
    db.close()
    db = null
  }
}
```

**Step 4: 验证数据库初始化**

```bash
cd ai-drama-studio && npx tsx -e "import { getDatabase } from './src/db/database'; const db = getDatabase(); console.log('Database initialized'); db.close()"
```
Expected: "Database initialized"

**Step 5: 提交**

```bash
git add -A && git commit -m "feat: add SQLite database with schema"
```

---

### Task 3: 创建项目目录结构

**Files:**
- Create: `ai-drama-studio/src/components/`
- Create: `ai-drama-studio/src/hooks/`
- Create: `ai-drama-studio/src/types/`
- Create: `ai-drama-studio/src/styles/`
- Create: `ai-drama-studio/src/db/`

**Step 1: 创建目录结构**

```bash
cd ai-drama-studio/src
mkdir -p components hooks types styles db
ls -la
```
Expected: 目录列表包含 components, hooks, types, styles, db

**Step 2: 创建 .gitkeep 文件**

```bash
touch components/.gitkeep hooks/.gitkeep types/.gitkeep styles/.gitkeep
```

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: create source directory structure"
```

---

### Task 4: 定义 TypeScript 类型

**Files:**
- Create: `ai-drama-studio/src/types/index.ts`

**Step 1: 创建类型定义**

```typescript
export interface Project {
  id: number
  name: string
  source: string
  type: 'modern' | 'ancient' | 'fantasy' | 'scifi'
  episode_count: number
  status: 'draft' | 'outline_review' | 'storyboard_review' | 'producing' | 'completed'
  created_at: string
}

export interface Character {
  id: number
  project_id: number
  name: string
  identity: string
  visual_tags: VisualTag[]
  reference_id: string
  created_at: string
}

export interface VisualTag {
  category: 'hair' | 'face' | 'eyes' | 'clothing' | 'accessory'
  tag: string
  weight: number
}

export interface Shot {
  id: number
  project_id: number
  episode: number
  scene: string
  shot_order: number
  camera_type: string
  movement: string
  action: string
  prompt: string
  bgm: string
  sfx: string
  vo_emotion: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}

export interface Scene {
  id: number
  project_id: number
  name: string
  description: string
  location_type: string
  created_at: string
}

export interface WorkflowStage {
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'waiting_review'
  agent?: string
}
```

**Step 2: 验证类型检查**

```bash
cd ai-drama-studio && npx tsc --noEmit
```
Expected: 无错误输出

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: add TypeScript type definitions"
```

---

### Task 5: 创建全局样式基础

**Files:**
- Create: `ai-drama-studio/src/styles/global.css`

**Step 1: 创建全局样式**

```css
:root {
  --color-primary: #6366f1;
  --color-primary-dark: #4f46e5;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-bg: #0f172a;
  --color-bg-secondary: #1e293b;
  --color-text: #f8fafc;
  --color-text-secondary: #94a3b8;
  --color-border: #334155;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
}

button {
  cursor: pointer;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
}

button.primary {
  background: var(--color-primary);
  color: white;
}

button.primary:hover {
  background: var(--color-primary-dark);
}

input, textarea {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
}

input:focus, textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}
```

**Step 2: 在 main.tsx 中引入**

```typescript
import './styles/global.css'
```

**Step 3: 验证样式加载**

```bash
cd ai-drama-studio && npm run dev &
sleep 3
curl -s http://localhost:3000 | head -20
```
Expected: HTML包含样式变量

**Step 4: 提交**

```bash
git add -A && git commit -m "feat: add global styles"
```

---

### Task 6: 创建 Project CRUD 数据库操作

**Files:**
- Create: `ai-drama-studio/src/db/project.ts`

**Step 1: 创建 project.ts**

```typescript
import { getDatabase } from './database'
import { Project } from '../types'

export function createProject(name: string, source: string, type: string, episodeCount: number): Project {
  const db = getDatabase()
  const stmt = db.prepare(
    'INSERT INTO projects (name, source, type, episode_count) VALUES (?, ?, ?, ?)'
  )
  const result = stmt.run(name, source, type, episodeCount)
  return getProjectById(result.lastInsertRowid as number)!
}

export function getProjectById(id: number): Project | undefined {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM projects WHERE id = ?')
  return stmt.get(id) as Project | undefined
}

export function getAllProjects(): Project[] {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM projects ORDER BY created_at DESC')
  return stmt.all() as Project[]
}

export function updateProjectStatus(id: number, status: string): void {
  const db = getDatabase()
  const stmt = db.prepare('UPDATE projects SET status = ? WHERE id = ?')
  stmt.run(status, id)
}

export function deleteProject(id: number): void {
  const db = getDatabase()
  db.prepare('DELETE FROM shots WHERE project_id = ?').run(id)
  db.prepare('DELETE FROM characters WHERE project_id = ?').run(id)
  db.prepare('DELETE FROM scenes WHERE project_id = ?').run(id)
  db.prepare('DELETE FROM projects WHERE id = ?').run(id)
}
```

**Step 2: 创建单元测试**

```bash
mkdir -p ai-drama-studio/src/db/__tests__
```

**Step 3: 创建测试文件**

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { createProject, getProjectById, getAllProjects, deleteProject } from '../project'
import { getDatabase } from '../database'

describe('Project CRUD', () => {
  beforeEach(() => {
    const db = getDatabase()
    db.exec('DELETE FROM projects')
  })

  it('should create a project', () => {
    const project = createProject('测试剧集', '原创', 'modern', 12)
    expect(project.name).toBe('测试剧集')
    expect(project.episode_count).toBe(12)
  })

  it('should get project by id', () => {
    const created = createProject('测试', '小说改编', 'fantasy', 24)
    const found = getProjectById(created.id)
    expect(found?.name).toBe('测试')
  })

  it('should list all projects', () => {
    createProject('项目1', '原创', 'modern', 12)
    createProject('项目2', '小说', 'ancient', 30)
    const projects = getAllProjects()
    expect(projects.length).toBe(2)
  })

  it('should delete project and related data', () => {
    const project = createProject('删除测试', '原创', 'modern', 12)
    deleteProject(project.id)
    expect(getProjectById(project.id)).toBeUndefined()
  })
})
```

**Step 4: 安装 vitest**

```bash
cd ai-drama-studio && npm install -D vitest @vitest/ui
```

**Step 5: 运行测试**

```bash
cd ai-drama-studio && npx vitest run src/db/__tests__/project.ts
```
Expected: 所有测试通过

**Step 6: 提交**

```bash
git add -A && git commit -m "feat: add project CRUD operations"
```

---

### Task 7: 创建 Character CRUD 数据库操作

**Files:**
- Create: `ai-drama-studio/src/db/character.ts`

**Step 1: 创建 character.ts**

```typescript
import { getDatabase } from './database'
import { Character, VisualTag } from '../types'

export function createCharacter(
  projectId: number,
  name: string,
  identity: string,
  visualTags: VisualTag[],
  referenceId: string
): Character {
  const db = getDatabase()
  const stmt = db.prepare(
    'INSERT INTO characters (project_id, name, identity, visual_tags, reference_id) VALUES (?, ?, ?, ?, ?)'
  )
  const result = stmt.run(projectId, name, identity, JSON.stringify(visualTags), referenceId)
  return getCharacterById(result.lastInsertRowid as number)!
}

export function getCharacterById(id: number): Character | undefined {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM characters WHERE id = ?')
  const row = stmt.get(id) as any
  if (!row) return undefined
  return {
    ...row,
    visual_tags: JSON.parse(row.visual_tags || '[]')
  }
}

export function getCharactersByProject(projectId: number): Character[] {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM characters WHERE project_id = ?')
  const rows = stmt.all(projectId) as any[]
  return rows.map(row => ({
    ...row,
    visual_tags: JSON.parse(row.visual_tags || '[]')
  }))
}

export function updateCharacterVisualTags(id: number, visualTags: VisualTag[]): void {
  const db = getDatabase()
  const stmt = db.prepare('UPDATE characters SET visual_tags = ? WHERE id = ?')
  stmt.run(JSON.stringify(visualTags), id)
}

export function deleteCharacter(id: number): void {
  const db = getDatabase()
  db.prepare('DELETE FROM characters WHERE id = ?').run(id)
}
```

**Step 2: 创建测试**

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { createCharacter, getCharacterById, getCharactersByProject, deleteCharacter } from '../character'
import { createProject } from '../project'
import { getDatabase } from '../database'

describe('Character CRUD', () => {
  beforeEach(() => {
    const db = getDatabase()
    db.exec('DELETE FROM characters; DELETE FROM projects')
  })

  it('should create a character', () => {
    const project = createProject('测试', '原创', 'modern', 12)
    const tags = [{ category: 'hair', tag: '(black hair:1.2)', weight: 1.2 }]
    const character = createCharacter(project.id, '男主', '落魄青年', tags, 'ref-001')
    expect(character.name).toBe('男主')
    expect(character.visual_tags).toHaveLength(1)
  })

  it('should get characters by project', () => {
    const project = createProject('测试', '原创', 'modern', 12)
    createCharacter(project.id, '男主', '青年', [], 'ref-1')
    createCharacter(project.id, '女主', '少女', [], 'ref-2')
    const characters = getCharactersByProject(project.id)
    expect(characters).toHaveLength(2)
  })
})
```

**Step 3: 运行测试**

```bash
cd ai-drama-studio && npx vitest run src/db/__tests__/character.ts
```
Expected: 所有测试通过

**Step 4: 提交**

```bash
git add -A && git commit -m "feat: add character CRUD operations"
```

---

### Task 8: 创建 Shot CRUD 数据库操作

**Files:**
- Create: `ai-drama-studio/src/db/shot.ts`

**Step 1: 创建 shot.ts**

```typescript
import { getDatabase } from './database'
import { Shot } from '../types'

export function createShot(
  projectId: number,
  episode: number,
  scene: string,
  shotOrder: number,
  cameraType: string,
  movement: string,
  action: string,
  prompt: string,
  bgm: string,
  sfx: string,
  voEmotion: string
): Shot {
  const db = getDatabase()
  const stmt = db.prepare(`
    INSERT INTO shots (project_id, episode, scene, shot_order, camera_type, movement, action, prompt, bgm, sfx, vo_emotion)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `)
  const result = stmt.run(projectId, episode, scene, shotOrder, cameraType, movement, action, prompt, bgm, sfx, voEmotion)
  return getShotById(result.lastInsertRowid as number)!
}

export function getShotById(id: number): Shot | undefined {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM shots WHERE id = ?')
  return stmt.get(id) as Shot | undefined
}

export function getShotsByEpisode(projectId: number, episode: number): Shot[] {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM shots WHERE project_id = ? AND episode = ? ORDER BY shot_order')
  return stmt.all(projectId, episode) as Shot[]
}

export function getShotsByProject(projectId: number): Shot[] {
  const db = getDatabase()
  const stmt = db.prepare('SELECT * FROM shots WHERE project_id = ? ORDER BY episode, shot_order')
  return stmt.all(projectId) as Shot[]
}

export function updateShotPrompt(id: number, prompt: string): void {
  const db = getDatabase()
  db.prepare('UPDATE shots SET prompt = ? WHERE id = ?').run(prompt, id)
}

export function updateShotStatus(id: number, status: string): void {
  const db = getDatabase()
  db.prepare('UPDATE shots SET status = ? WHERE id = ?').run(status, id)
}

export function deleteShotsByEpisode(projectId: number, episode: number): void {
  const db = getDatabase()
  db.prepare('DELETE FROM shots WHERE project_id = ? AND episode = ?').run(projectId, episode)
}
```

**Step 2: 创建测试**

```bash
mkdir -p ai-drama-studio/src/db/__tests__
```

**Step 3: 创建 shot 测试**

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { createShot, getShotsByEpisode, updateShotPrompt, deleteShotsByEpisode } from '../shot'
import { createProject } from '../project'
import { getDatabase } from '../database'

describe('Shot CRUD', () => {
  beforeEach(() => {
    const db = getDatabase()
    db.exec('DELETE FROM shots; DELETE FROM projects')
  })

  it('should create a shot', () => {
    const project = createProject('测试', '原创', 'modern', 12)
    const shot = createShot(project.id, 1, '场景1', 1, 'Close-Up', 'push in', '男主转身', 'prompt text', 'BGM', 'SFX', 'VO_Emotion')
    expect(shot.episode).toBe(1)
    expect(shot.prompt).toBe('prompt text')
  })

  it('should get shots by episode', () => {
    const project = createProject('测试', '原创', 'modern', 12)
    createShot(project.id, 1, '场景1', 1, 'CU', 'static', 'action', 'p', 'B', 'S', 'V')
    createShot(project.id, 1, '场景1', 2, 'MS', 'pan', 'action2', 'p2', 'B2', 'S2', 'V2')
    createShot(project.id, 2, '场景2', 1, 'WS', 'dolly', 'action3', 'p3', 'B3', 'S3', 'V3')
    const episode1Shots = getShotsByEpisode(project.id, 1)
    expect(episode1Shots).toHaveLength(2)
  })
})
```

**Step 4: 运行测试**

```bash
cd ai-drama-studio && npx vitest run src/db/__tests__/shot.ts
```
Expected: 所有测试通过

**Step 5: 提交**

```bash
git add -A && git commit -m "feat: add shot CRUD operations"
```

---

## Phase 1 完成：前端基础设施搭建 ✅

**已完成：**
- React + Vite 项目脚手架
- SQLite 数据库配置
- TypeScript 类型定义
- 全局样式
- Project/Character/Shot CRUD

---

## Phase 2: 前端核心UI功能

### Task 9: 创建项目列表页面

**Files:**
- Create: `ai-drama-studio/src/components/ProjectList.tsx`
- Modify: `ai-drama-studio/src/App.tsx`

**Step 1: 创建 ProjectList 组件**

```tsx
import { useState, useEffect } from 'react'
import { Project } from '../types'
import { getAllProjects, createProject, deleteProject } from '../db/project'

export function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([])
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newSource, setNewSource] = useState('')
  const [newType, setNewType] = useState('modern')
  const [newEpisodes, setNewEpisodes] = useState('12')

  useEffect(() => {
    setProjects(getAllProjects())
  }, [])

  const handleCreate = () => {
    if (!newName.trim()) return
    const project = createProject(newName, newSource, newType, parseInt(newEpisodes))
    setProjects([project, ...projects])
    setNewName('')
    setNewSource('')
    setShowForm(false)
  }

  const handleDelete = (id: number) => {
    if (!confirm('确认删除？')) return
    deleteProject(id)
    setProjects(projects.filter(p => p.id !== id))
  }

  return (
    <div className="project-list">
      <div className="header">
        <h1>AI漫剧工业化生产系统</h1>
        <button className="primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '+ 新建项目'}
        </button>
      </div>

      {showForm && (
        <div className="form-card">
          <input
            placeholder="项目名称"
            value={newName}
            onChange={e => setNewName(e.target.value)}
          />
          <input
            placeholder="IP来源（小说名/原创）"
            value={newSource}
            onChange={e => setNewSource(e.target.value)}
          />
          <select value={newType} onChange={e => setNewType(e.target.value)}>
            <option value="modern">现代都市</option>
            <option value="ancient">古风</option>
            <option value="fantasy">玄幻</option>
            <option value="scifi">科幻</option>
          </select>
          <input
            type="number"
            placeholder="集数"
            value={newEpisodes}
            onChange={e => setNewEpisodes(e.target.value)}
          />
          <button className="primary" onClick={handleCreate}>创建</button>
        </div>
      )}

      <div className="project-grid">
        {projects.map(project => (
          <div key={project.id} className="project-card">
            <h3>{project.name}</h3>
            <p>来源：{project.source || '未设置'}</p>
            <p>类型：{project.type}</p>
            <p>集数：{project.episode_count}</p>
            <p>状态：{project.status}</p>
            <div className="actions">
              <button>打开</button>
              <button onClick={() => handleDelete(project.id)}>删除</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Step 2: 更新 App.tsx**

```tsx
import { ProjectList } from './components/ProjectList'
import './styles/global.css'

function App() {
  return <ProjectList />
}

export default App
```

**Step 3: 添加组件样式**

```css
.project-list {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--color-bg-secondary);
  border-radius: 8px;
  margin-bottom: 24px;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.project-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
}

.project-card h3 {
  margin-bottom: 8px;
  color: var(--color-text);
}

.project-card p {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-bottom: 4px;
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.actions button {
  flex: 1;
  background: var(--color-bg);
}
```

**Step 4: 验证页面**

```bash
cd ai-drama-studio && npm run dev &
sleep 3
curl -s http://localhost:3000 | grep -o '<h1>.*</h1>'
```
Expected: 显示项目列表页面

**Step 5: 提交**

```bash
git add -A && git commit -m "feat: add project list page"
```

---

### Task 10: 创建项目详情页面（进度看板）

**Files:**
- Create: `ai-drama-studio/src/components/ProjectDetail.tsx`
- Create: `ai-drama-studio/src/hooks/useProject.ts`

**Step 1: 创建 useProject hook**

```typescript
import { useState, useEffect } from 'react'
import { Project, Character, Shot, Scene } from '../types'
import { getProjectById, updateProjectStatus } from '../db/project'
import { getCharactersByProject } from '../db/character'
import { getShotsByProject } from '../db/shot'

export function useProject(projectId: number) {
  const [project, setProject] = useState<Project | null>(null)
  const [characters, setCharacters] = useState<Character[]>([])
  const [shots, setShots] = useState<Shot[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const p = getProjectById(projectId)
    if (p) {
      setProject(p)
      setCharacters(getCharactersByProject(projectId))
      setShots(getShotsByProject(projectId))
    }
    setLoading(false)
  }, [projectId])

  const updateStatus = (status: string) => {
    updateProjectStatus(projectId, status)
    setProject({ ...project!, status })
  }

  return { project, characters, shots, loading, updateStatus }
}
```

**Step 2: 创建 ProjectDetail 组件**

```tsx
import { useParams, Link } from 'react-router-dom'
import { useProject } from '../hooks/useProject'

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id || '0')
  const { project, characters, shots, loading, updateStatus } = useProject(projectId)

  if (loading) return <div>加载中...</div>
  if (!project) return <div>项目不存在</div>

  const workflowStages = [
    { name: 'IP解析', key: 'outline_review', check: () => true },
    { name: '剧本大纲', key: 'outline_review', check: () => project.status !== 'draft' },
    { name: '分镜脚本', key: 'storyboard_review', check: () => project.status === 'storyboard_review' || project.status === 'producing' || project.status === 'completed' },
    { name: '视觉Prompt', key: 'producing', check: () => project.status === 'producing' || project.status === 'completed' },
    { name: '完成', key: 'completed', check: () => project.status === 'completed' }
  ]

  return (
    <div className="project-detail">
      <div className="header">
        <Link to="/">← 返回</Link>
        <h1>{project.name}</h1>
        <span className="status">{project.status}</span>
      </div>

      <div className="workflow">
        <h2>工作流程</h2>
        <div className="stages">
          {workflowStages.map((stage, index) => {
            const isComplete = stage.check()
            const isCurrent = !isComplete && workflowStages[index - 1]?.check()
            return (
              <div
                key={stage.name}
                className={`stage ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''}`}
              >
                <div className="stage-icon">{isComplete ? '✓' : index + 1}</div>
                <div className="stage-name">{stage.name}</div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="info-grid">
        <div className="info-card">
          <h3>基本信息</h3>
          <p>IP来源：{project.source}</p>
          <p>类型：{project.type}</p>
          <p>集数：{project.episode_count}</p>
        </div>
        <div className="info-card">
          <h3>角色库</h3>
          <p>{characters.length} 个角色</p>
          <Link to={`/project/${projectId}/characters`}>管理角色</Link>
        </div>
        <div className="info-card">
          <h3>镜头库</h3>
          <p>{shots.length} 个镜头</p>
          <Link to={`/project/${projectId}/shots`}>查看镜头</Link>
        </div>
      </div>
    </div>
  )
}
```

**Step 3: 添加路由**

```bash
cd ai-drama-studio && npm install react-router-dom@6
```

**Step 4: 更新 App.tsx 使用路由**

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ProjectList } from './components/ProjectList'
import { ProjectDetail } from './components/ProjectDetail'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProjectList />} />
        <Route path="/project/:id" element={<ProjectDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

**Step 5: 添加详情页样式**

```css
.project-detail {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.workflow {
  background: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
}

.stages {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
}

.stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.stage-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-border);
}

.stage.complete .stage-icon {
  background: var(--color-success);
  border-color: var(--color-success);
}

.stage.current .stage-icon {
  border-color: var(--color-primary);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-card {
  background: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 16px;
}
```

**Step 6: 验证**

```bash
cd ai-drama-studio && npm run dev &
sleep 3
curl -s http://localhost:3000 | grep 'AI漫剧'
```
Expected: 页面正常渲染

**Step 7: 提交**

```bash
git add -A && git commit -m "feat: add project detail page with workflow tracking"
```

---

### Task 11: 创建角色管理页面

**Files:**
- Create: `ai-drama-studio/src/components/CharacterManager.tsx`

**Step 1: 创建 CharacterManager 组件**

```tsx
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Character, VisualTag } from '../types'
import { getCharactersByProject, createCharacter, deleteCharacter, updateCharacterVisualTags } from '../db/character'

export function CharacterManager() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id || '0')
  const [characters, setCharacters] = useState<Character[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  const [newName, setNewName] = useState('')
  const [newIdentity, setNewIdentity] = useState('')
  const [newRefId, setNewRefId] = useState('')

  useEffect(() => {
    setCharacters(getCharactersByProject(projectId))
  }, [projectId])

  const handleCreate = () => {
    if (!newName.trim()) return
    const character = createCharacter(projectId, newName, newIdentity, [], newRefId)
    setCharacters([...characters, character])
    setNewName('')
    setNewIdentity('')
    setNewRefId('')
    setShowForm(false)
  }

  const handleDelete = (charId: number) => {
    if (!confirm('确认删除？')) return
    deleteCharacter(charId)
    setCharacters(characters.filter(c => c.id !== charId))
  }

  const visualCategories = ['hair', 'face', 'eyes', 'clothing', 'accessory'] as const

  return (
    <div className="character-manager">
      <div className="header">
        <Link to={`/project/${projectId}`}>← 返回</Link>
        <h1>角色管理</h1>
        <button className="primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '取消' : '+ 添加角色'}
        </button>
      </div>

      {showForm && (
        <div className="form-card">
          <input placeholder="角色名称" value={newName} onChange={e => setNewName(e.target.value)} />
          <input placeholder="身份（如：落魄青年）" value={newIdentity} onChange={e => setNewIdentity(e.target.value)} />
          <input placeholder="参考图ID" value={newRefId} onChange={e => setNewRefId(e.target.value)} />
          <button className="primary" onClick={handleCreate}>创建</button>
        </div>
      )}

      <div className="character-list">
        {characters.map(char => (
          <div key={char.id} className="character-card">
            <h3>{char.name}</h3>
            <p>身份：{char.identity || '未设置'}</p>
            <p>参考图ID：{char.reference_id || '未设置'}</p>
            <div className="visual-tags">
              <h4>视觉特征</h4>
              {char.visual_tags.length === 0 ? (
                <p className="empty">暂无视觉标签</p>
              ) : (
                char.visual_tags.map((tag, i) => (
                  <span key={i} className="tag">{tag.tag} ({tag.weight})</span>
                ))
              )}
            </div>
            <div className="actions">
              <button onClick={() => setEditingId(char.id)}>编辑</button>
              <button onClick={() => handleDelete(char.id)}>删除</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Step 2: 添加路由**

```tsx
import { CharacterManager } from './components/CharacterManager'

<Route path="/project/:id/characters" element={<CharacterManager />} />
```

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: add character management page"
```

---

### Task 12: 创建镜头审核面板

**Files:**
- Create: `ai-drama-studio/src/components/ShotReview.tsx`

**Step 1: 创建 ShotReview 组件**

```tsx
import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Shot } from '../types'
import { getShotsByEpisode, updateShotStatus } from '../db/shot'

export function ShotReview() {
  const { id, episode } = useParams<{ id: string; episode: string }>()
  const projectId = parseInt(id || '0')
  const episodeNum = parseInt(episode || '1')
  const [shots, setShots] = useState<Shot[]>([])
  const [selectedShot, setSelectedShot] = useState<Shot | null>(null)

  useEffect(() => {
    setShots(getShotsByEpisode(projectId, episodeNum))
  }, [projectId, episodeNum])

  const handleApprove = (shotId: number) => {
    updateShotStatus(shotId, 'approved')
    setShots(shots.map(s => s.id === shotId ? { ...s, status: 'approved' } : s))
  }

  const handleReject = (shotId: number) => {
    updateShotStatus(shotId, 'rejected')
    setShots(shots.map(s => s.id === shotId ? { ...s, status: 'rejected' } : s))
  }

  return (
    <div className="shot-review">
      <h1>第{episodeNum}集镜头审核</h1>
      <div className="shot-list">
        {shots.map(shot => (
          <div key={shot.id} className={`shot-card ${shot.status}`}>
            <div className="shot-header">
              <span>镜头 {shot.shot_order}</span>
              <span className="status-badge">{shot.status}</span>
            </div>
            <p className="camera">{shot.camera_type} | {shot.movement}</p>
            <p className="action">{shot.action}</p>
            <div className="emotion">
              <span>BGM: {shot.bgm}</span>
              <span>SFX: {shot.sfx}</span>
              <span>VO: {shot.vo_emotion}</span>
            </div>
            {shot.prompt && (
              <div className="prompt-preview">
                <code>{shot.prompt.substring(0, 100)}...</code>
              </div>
            )}
            <div className="actions">
              {shot.status === 'pending' && (
                <>
                  <button className="approve" onClick={() => handleApprove(shot.id)}>通过</button>
                  <button className="reject" onClick={() => handleReject(shot.id)}>驳回</button>
                </>
              )}
              <button onClick={() => setSelectedShot(shot)}>详情</button>
            </div>
          </div>
        ))}
      </div>
      {selectedShot && (
        <div className="modal" onClick={() => setSelectedShot(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>镜头 {selectedShot.shot_order} 详情</h2>
            <p><strong>类型：</strong>{selectedShot.camera_type}</p>
            <p><strong>运镜：</strong>{selectedShot.movement}</p>
            <p><strong>动作：</strong>{selectedShot.action}</p>
            <p><strong>BGM：</strong>{selectedShot.bgm}</p>
            <p><strong>SFX：</strong>{selectedShot.sfx}</p>
            <p><strong>配音：</strong>{selectedShot.vo_emotion}</p>
            <div className="prompt-full">
              <h3>完整Prompt</h3>
              <textarea readOnly value={selectedShot.prompt} />
            </div>
            <button onClick={() => setSelectedShot(null)}>关闭</button>
          </div>
        </div>
      )}
    </div>
  )
}
```

**Step 2: 添加路由**

```tsx
import { ShotReview } from './components/ShotReview'

<Route path="/project/:id/episode/:episode/shots" element={<ShotReview />} />
```

**Step 3: 添加样式**

```css
.shot-review {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.shot-card {
  background: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 4px solid var(--color-border);
}

.shot-card.approved {
  border-left-color: var(--color-success);
}

.shot-card.rejected {
  border-left-color: var(--color-danger);
}

.shot-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.shot-card.pending .status-badge {
  background: var(--color-warning);
}

.shot-card.approved .status-badge {
  background: var(--color-success);
}

.shot-card.rejected .status-badge {
  background: var(--color-danger);
}

.prompt-preview {
  background: var(--color-bg);
  padding: 8px;
  border-radius: 4px;
  margin: 8px 0;
  overflow: hidden;
}

.prompt-preview code {
  font-size: 12px;
  white-space: nowrap;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--color-bg-secondary);
  padding: 24px;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.prompt-full textarea {
  width: 100%;
  height: 150px;
  margin: 8px 0;
  font-family: monospace;
  resize: none;
}
```

**Step 4: 提交**

```bash
git add -A && git commit -m "feat: add shot review panel"
```

---

### Task 13: 创建 Obsidian 同步服务

**Files:**
- Create: `ai-drama-studio/src/services/obsidianSync.ts`

**Step 1: 创建 ObsidianSync 服务**

```typescript
import * as fs from 'fs'
import * as path from 'path'
import { Project, Character, Shot } from '../types'

const OBSIDIAN_BASE = '/Users/huage/Obsidian Vault/AI漫剧项目'

export interface ObsidianProject {
  project: Project
  characters: Character[]
  shots: Shot[]
}

export function getProjectPath(projectName: string): string {
  return path.join(OBSIDIAN_BASE, projectName)
}

export function ensureProjectStructure(projectName: string): void {
  const base = getProjectPath(projectName)
  const dirs = [
    '00-项目信息',
    '01-世界观',
    '02-角色',
    '03-场景',
    '04-剧本',
    '05-审核'
  ]
  for (const dir of dirs) {
    fs.mkdirSync(path.join(base, dir), { recursive: true })
  }
}

export function saveProjectOverview(project: Project): void {
  const content = `# ${project.name}

## 基本信息
- **IP来源**：${project.source}
- **类型**：${project.type}
- **集数**：${project.episode_count}
- **状态**：${project.status}
- **创建时间**：${project.created_at}
`
  const filePath = path.join(getProjectPath(project.name), '00-项目信息', '项目概览.md')
  fs.writeFileSync(filePath, content)
}

export function saveCharacterAnchors(projectName: string, characters: Character[]): void {
  let content = '# 角色锚点\n\n'
  for (const char of characters) {
    content += `## ${char.name}\n\n`
    content += `**身份**：${char.identity}\n\n`
    content += `**参考图ID**：${char.reference_id}\n\n`
    content += `### 视觉特征\n\n`
    for (const tag of char.visual_tags) {
      content += `- ${tag.category}: ${tag.tag} (权重: ${tag.weight})\n`
    }
    content += '\n---\n\n'
  }
  const filePath = path.join(getProjectPath(projectName), '02-角色', '角色锚点.md')
  fs.writeFileSync(filePath, content)
}

export function saveEpisodeScript(projectName: string, episode: number, shots: Shot[]): void {
  let content = `# 第${episode}集 分镜脚本\n\n`
  let currentScene = ''
  for (const shot of shots) {
    if (shot.scene !== currentScene) {
      currentScene = shot.scene
      content += `## 场景：${currentScene}\n\n`
    }
    content += `### 镜头 ${shot.shot_order}\n\n`
    content += `**类型**：${shot.camera_type} | **运镜**：${shot.movement}\n\n`
    content += `**动作**：${shot.action}\n\n`
    content += `**BGM/SFX**：${shot.bgm} / ${shot.sfx}\n\n`
    content += `**配音情绪**：${shot.vo_emotion}\n\n`
    content += `**Prompt**：\n\`\`\`\n${shot.prompt} --ar 16:9\n\`\`\`\n\n`
    content += `---\n\n`
  }
  const episodeDir = path.join(getProjectPath(projectName), '04-剧本', `第${episode}集`)
  fs.mkdirSync(episodeDir, { recursive: true })
  fs.writeFileSync(path.join(episodeDir, '分镜脚本.md'), content)
}

export function exportToObsidian(data: ObsidianProject): void {
  ensureProjectStructure(data.project.name)
  saveProjectOverview(data.project)
  saveCharacterAnchors(data.project.name, data.characters)
  const shotsByEpisode = new Map<number, Shot[]>()
  for (const shot of data.shots) {
    if (!shotsByEpisode.has(shot.episode)) {
      shotsByEpisode.set(shot.episode, [])
    }
    shotsByEpisode.get(shot.episode)!.push(shot)
  }
  for (const [episode, shots] of shotsByEpisode) {
    saveEpisodeScript(data.project.name, episode, shots)
  }
}
```

**Step 2: 创建索引导出**

```typescript
export function exportAllProjects(projects: ObsidianProject[]): void {
  for (const project of projects) {
    exportToObsidian(project)
  }
}
```

**Step 3: 验证目录创建**

```bash
cd ai-drama-studio && npx tsx -e "
import { ensureProjectStructure, getProjectPath } from './src/services/obsidianSync';
ensureProjectStructure('测试项目');
const fs = require('fs');
console.log(fs.readdirSync(getProjectPath('测试项目')));
"
```
Expected: 目录结构创建成功

**Step 4: 提交**

```bash
git add -A && git commit -m "feat: add obsidian sync service"
```

---

## Phase 2 完成：前端核心UI功能 ✅

**已完成：**
- 项目列表页面
- 项目详情/进度看板
- 角色管理页面
- 镜头审核面板
- Obsidian同步服务

---

## Phase 3: Claude Agent系统构建

### Task 14: 创建 Agent 系统提示词模板库

**Files:**
- Create: `ai-drama-studio/src/agents/systemPrompts.ts`

**Step 1: 创建系统提示词模板**

```typescript
export const AGENT_SYSTEM_PROMPTS = {
  ipAnalyzer: `你是一位顶尖的IP分析师，专门解析小说和创意IP。

你的职责：
1. 提取世界观（时间背景、空间背景、社会结构、力量体系、规则体系）
2. 提取核心矛盾（主线冲突、人物冲突、社会冲突、情感冲突）
3. 识别情绪主线和爽点结构

输出格式（必须严格遵守）：
## 世界观类型
[现代都市/古风/玄幻/科幻]

## 核心规则
[金钱权力/武力等级/科技阶级等]

## 社会结构
[简要描述]

## 力量体系（如有）
[描述]

## 核心矛盾
- 主线冲突：[描述]
- 人物冲突：[描述]
- 情感冲突：[描述]

## 情绪主线
[爽-怒-紧张-期待-反转-释放]

## 爽点结构
[列出主要爽点]

禁止使用占位符。`,
  characterSystem: `你是一位角色系统专家，专门从小说中提取角色信息并生成视觉特征Tag。

每个角色必须输出：
## 角色：[姓名]

### 基本信息
- **身份**：[描述]
- **核心欲望**：[描述]
- **隐藏恐惧**：[描述]
- **人物弧线**：[起点→转折→终点]

### 视觉特征（必须精确）
- **Reference Image ID**：ref-[角色名拼音]-[序号]
- **发型Tag**：(如 (short black hair:1.2))
- **面部特征**：(如 (sharp jawline:1.1))
- **眼睛**：(如 (cold dark eyes:1.2))
- **基础服装**：(如 (black formal suit:1.3))
- **变装服装**：(如 (worn-out grey hoodie:1.2))

### 情绪表达
- **愤怒**：[描述表情和身体语言]
- **悲伤**：[描述]
- **冷漠**：[描述]

### 关系网络
- [与角色B的关系]：[描述]

权重规则：容貌1.0-1.3，服装1.2-1.5，配饰1.0-1.2

禁止使用占位符。`,
  sceneDesign: `你是一位场景设计师，分析小说中的场景类型。

输出：
## 场景库

### 场景1：[名称]
- **类型**：[室内/室外/特定场所]
- **位置**：[具体描述]
- **时间**：[白天/夜晚/特定时间]
- **氛围**：[描述]
- **视觉元素**：[列出关键视觉元素]

每个场景必须包含：光影特点、色彩基调、空间感描述。

禁止使用占位符。`,
  storyEngine: `你是一位的AI编剧，擅长将小说重构为爆款短剧结构。

爆款算法规则：
1. 前3秒防滑走：每集第一个镜头必须是极具视觉冲击力的画面
2. 情绪节奏：每集必须有爽、怒、紧张、期待、反转、释放
3. 2-3分钟一集：3分钟一个高潮，5分钟一个反转
4. 每集结尾必须悬念

分集大纲格式：
### 第X集
**【本集情绪主线】**：[如：紧张→反转→释放]
**【核心爆点】**：[描述]
**【前3秒钩子】**：[极度视觉冲击或悬疑画面描述]

**场景流程**：
1. [场景1]：动作描述
2. [场景2]：动作描述
...

**【本集悬念】**：[结尾钩子]

禁止使用占位符。必须完整输出所有集数。`,
  directorAgent: `你是一位AI导演，擅长分镜设计和镜头语言。

每个场景必须输出：
### 场景 [编号]：[名称]

**【场景描述】**：[中文描述]

**【剧情动作】**：[详细描述发生了什么]

**【AI导演分镜设计】**
- 镜头 01：[运镜方式]。[具体画面描述，包含光影]
- 镜头 02：[运镜方式]。[具体画面描述]
- 镜头 03：[运镜方式]。[具体画面描述]

**【BGM/SFX】**：[如：沉重的低音大提琴 + 雷暴音效]

**【配音情绪标签】**：[VO_Emotion: 咬牙切齿/哽咽/冷笑/颤抖/平静]

运镜术语库：
- 推进：push in, dolly in
- 后拉：pull out, dolly out
- 横移：pan, tracking shot
- 环绕：crane shot,环绕
- 固定：static, locked

禁止使用占位符。`,
  visualAgent: `你是一位AI视觉设计师，负责生成可直接用于Seedance等视频生成工具的英文Prompt。

Prompt结构（强制顺序）：
[镜头类型] [运镜方式]. [角色特征Tag]. [动作描述]. [环境光影]. [情绪表达]. [背景虚化]. [画质参数]. --ar 16:9

规则：
1. 角色特征必须使用角色锚点中的精确Tag，带权重
2. 禁止使用省略号或占位符
3. 每个镜头必须输出一行完整Prompt
4. 画质参数必须包含：8k resolution, photorealistic, cinematic color grading
5. 画幅固定为 16:9

示例Prompt：
Extreme Close-Up shot, push in camera movement. A handsome 25-year-old Asian man, (messy soaked black hair:1.2), (black formal suit drenched in rain:1.3), water dripping from his chin. His expression transitions from deep despair to extreme coldness and anger, staring intensely into the camera. Cinematic lighting, high contrast dramatic lighting, a sudden flash of blue lightning illuminates half of his face. Heavy rain night, cyberpunk city street background blurred in bokeh. 8k resolution, photorealistic, IMAX 70mm, Dennis Villeneuve style, cinematic color grading, high emotional intensity. --ar 16:9`,
  soundAgent: `你是一位AI声音设计师，负责BGM、SFX和配音情绪设计。

每个场景必须输出：
**【BGM】**：[类型描述，如：沉重的低音大提琴]
**【SFX】**：[音效描述，如：雷暴音效、心跳声]
**【配音情绪】**：[VO_Emotion: 标签]

情绪曲线绑定规则：
- 高潮戏 → 激昂BGM + 关键SFX
- 情感戏 → 温柔BGM + 环境音效
- 悬疑戏 → 低沉BGM + 尖锐SFX
- 冲突戏 → 紧张弦乐 + 对白

配音情绪标签库：
- [VO_Emotion: 咬牙切齿]
- [VO_Emotion: 哽咽]
- [VO_Emotion: 冷笑]
- [VO_Emotion: 颤抖]
- [VO_Emotion: 平静]
- [VO_Emotion: 愤怒]
- [VO_Emotion: 惊讶]

禁止使用占位符。`
}
```

**Step 2: 验证编译**

```bash
cd ai-drama-studio && npx tsc --noEmit
```
Expected: 无错误

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: add agent system prompt templates"
```

---

### Task 15: 创建视觉风格库

**Files:**
- Create: `ai-drama-studio/src/agents/visualStyles.ts`

**Step 1: 创建视觉风格库**

```typescript
export interface VisualStyle {
  name: string
  nameCN: string
 适用场景: string[]
  visualFeatures: string[]
  promptSuffix: string[]
}

export const VISUAL_STYLE_LIBRARY: VisualStyle[] = [
  {
    name: 'Hollywood Epic',
    nameCN: '好莱坞史诗风',
    适用场景: ['大场面', '高潮戏', '史诗'],
    visualFeatures: [
      'Large scale set pieces',
      'Epic orchestral score atmosphere',
      'IMAX framing',
      'Sweeping crane shots'
    ],
    promptSuffix: [
      'IMAX 70mm',
      'Dennis Villeneuve style',
      'epic scale',
      'cinematic color grading'
    ]
  },
  {
    name: 'Wong Kar-wai Emotional',
    nameCN: '王家卫情绪风',
    适用场景: ['情感戏', '独白', '孤独感'],
    visualFeatures: [
      'High ISO grain',
      'Neon lights',
      'Slow motion',
      'Intimate close-ups'
    ],
    promptSuffix: [
      'Wong Kar-wai style',
      '90s Hong Kong art film',
      'neon lighting',
      'high ISO grain',
      'slow motion'
    ]
  },
  {
    name: 'Denis Villeneuve Sci-Fi',
    nameCN: '丹尼斯维伦纽瓦科幻',
    适用场景: ['科幻', '史诗', '压迫感'],
    visualFeatures: [
      'IMAX 70mm',
      'Massive scale',
      'Blue/orange color grading',
      'Intense atmosphere'
    ],
    promptSuffix: [
      'IMAX 70mm',
      'Denis Villeneuve style',
      'sci-fi epic',
      'massive scale',
      'blue orange color grading'
    ]
  },
  {
    name: 'Chinese Short Drama',
    nameCN: '中国短剧爽剧风',
    适用场景: ['逆袭', '打脸', '爽点'],
    visualFeatures: [
      'High emotional intensity',
      'Fast editing rhythm',
      'High contrast',
      'Dramatic lighting'
    ],
    promptSuffix: [
      'high emotional intensity',
      'fast editing rhythm',
      'high contrast lighting',
      'Chinese short drama style'
    ]
  },
  {
    name: 'UGC Documentary',
    nameCN: 'UGC真实纪录风',
    适用场景: ['日常', 'vlog', '真实感'],
    visualFeatures: [
      'Mobile phone camera feel',
      'Natural lighting',
      'Authentic atmosphere',
      'Shallow depth of field'
    ],
    promptSuffix: [
      'vlog documentary style',
      'realistic镜头',
      'authentic atmosphere',
      'mobile phone camera'
    ]
  },
  {
    name: 'Pixar 3D Animation',
    nameCN: '皮克斯3D动画风',
    适用场景: ['动画', '可爱', '家庭'],
    visualFeatures: [
      'Pixar 3D animation style',
      'Expressive characters',
      'Vibrant colors',
      'Cinema-quality rendering'
    ],
    promptSuffix: [
      'Pixar 3D animation style:1.3',
      'CGI animation',
      'highly detailed',
      '8k resolution',
      'Unreal Engine 5 render'
    ]
  },
  {
    name: 'Cyberpunk Neon',
    nameCN: '赛博朋克霓虹风',
    适用场景: ['科幻', '未来', '都市'],
    visualFeatures: [
      'Neon lights',
      'Rain-soaked streets',
      'Futuristic architecture',
      'High contrast lighting'
    ],
    promptSuffix: [
      'cyberpunk city',
      'neon lighting',
      'rain-soaked streets',
      'futuristic atmosphere'
    ]
  }
]

export function matchStyle(sceneType: string): VisualStyle {
  const typeMap: Record<string, string> = {
    '高潮': 'Hollywood Epic',
    '大场面': 'Hollywood Epic',
    '情感': 'Wong Kar-wai Emotional',
    '独白': 'Wong Kar-wai Emotional',
    '科幻': 'Denis Villeneuve Sci-Fi',
    '史诗': 'Denis Villeneuve Sci-Fi',
    '逆袭': 'Chinese Short Drama',
    '打脸': 'Chinese Short Drama',
    '日常': 'UGC Documentary',
    'vlog': 'UGC Documentary',
    '动画': 'Pixar 3D Animation',
    '未来': 'Cyberpunk Neon',
    '都市': 'Cyberpunk Neon'
  }
  const matchName = typeMap[sceneType] || 'Chinese Short Drama'
  return VISUAL_STYLE_LIBRARY.find(s => s.name === matchName) || VISUAL_STYLE_LIBRARY[3]
}
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: add visual style library"
```

---

### Task 16: 创建爆款元素库

**Files:**
- Create: `ai-drama-studio/src/agents/hitElements.ts`

**Step 1: 创建爆款元素库**

```typescript
export interface HitElement {
  type: string
  description: string
  visualExamples: string[]
}

export const HIT_ELEMENT_LIBRARY: HitElement[] = [
  {
    type: '身份打脸',
    description: '身份反转带来的打脸爽感',
    visualExamples: [
      '穷小子展示身份的瞬间',
      '被嘲笑的对象突然逆转',
      '隐藏身份揭晓'
    ]
  },
  {
    type: '豪门对抗',
    description: '豪门家族之间的冲突',
    visualExamples: [
      '家族对峙场面',
      '豪门宴会暗流涌动',
      '权力交接争夺'
    ]
  },
  {
    type: '逆袭',
    description: '从低谷到巅峰的逆袭',
    visualExamples: [
      '废柴觉醒瞬间',
      '被打压后反击',
      '能力爆发时刻'
    ]
  },
  {
    type: '复仇',
    description: '复仇的快感',
    visualExamples: [
      '复仇者出现',
      '仇人崩溃表情',
      '正义伸张时刻'
    ]
  },
  {
    type: '爱情修罗场',
    description: '多角恋的情感冲突',
    visualExamples: [
      '两人对峙',
      '三角关系爆发',
      '情感抉择时刻'
    ]
  },
  {
    type: '权力斗争',
    description: '权力争夺的紧张感',
    visualExamples: [
      '高层会议博弈',
      '夺权行动',
      '背叛与忠诚'
    ]
  }
]

export const HOOK_LIBRARY = {
  visualImpact: [
    '巴掌扇在脸上的瞬间',
    '水杯突然泼在脸上',
    '急刹车产生的冲击',
    '爆炸带来的冲击波',
    '角色突然抬头（特写）',
    '眼睛突然睁大'
  ],
  suspenseVisual: [
    '黑暗中闪烁的眼睛',
    '门缝透出的光',
    '倒计时器特写',
    '影子逼近的脚步',
    '神秘人出现',
    '关键证据的特写'
  ]
}

export const EMOTION_CURVE = {
  episode: ['爽', '怒', '紧张', '期待', '反转', '释放'],
  timing: {
    '2min': { 高潮: '90s', 反转: '120s' },
    '3min': { 高潮: '120s', 反转: '180s' }
  }
}
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: add hit element library"
```

---

### Task 17: 创建 Claude API 调用服务

**Files:**
- Create: `ai-drama-studio/src/services/claudeApi.ts`

**Step 1: 创建 Claude API 服务**

```typescript
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic()

export interface ClaudeRequest {
  system: string
  prompt: string
  maxTokens?: number
}

export async function callClaude(request: ClaudeRequest): Promise<string> {
  const response = await anthropic.messages.create({
    model: 'claude-opus-4-6',
    max_tokens: request.maxTokens || 4096,
    system: request.system,
    messages: [
      {
        role: 'user',
        content: request.prompt
      }
    ]
  })
  return response.content[0].type === 'text' ? response.content[0].text : ''
}

export async function callClaudeStream(
  request: ClaudeRequest,
  onChunk: (text: string) => void
): Promise<string> {
  const response = await anthropic.messages.stream({
    model: 'claude-opus-4-6',
    max_tokens: request.maxTokens || 4096,
    system: request.system,
    messages: [
      {
        role: 'user',
        content: request.prompt
      }
    ]
  })
  let fullText = ''
  for await (const event of response) {
    if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
      fullText += event.delta.text
      onChunk(event.delta.text)
    }
  }
  return fullText
}
```

**Step 2: 安装 Anthropic SDK**

```bash
cd ai-drama-studio && npm install @anthropic-ai/sdk
```

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: add claude api service"
```

---

### Task 18: 创建 Agent 编排器

**Files:**
- Create: `ai-drama-studio/src/agents/orchestrator.ts`

**Step 1: 创建编排器**

```typescript
import { callClaude } from '../services/claudeApi'
import { AGENT_SYSTEM_PROMPTS } from './systemPrompts'
import { VISUAL_STYLE_LIBRARY, matchStyle } from './visualStyles'
import { HIT_ELEMENT_LIBRARY, HOOK_LIBRARY } from './hitElements'
import { Project, Character, Shot, VisualTag } from '../types'
import { createShot } from '../db/shot'

export interface WorkflowResult {
  status: 'success' | 'error'
  data?: any
  error?: string
}

export class AgentOrchestrator {
  private project: Project
  private characters: Character[]
  private storyOutline: string = ''
  private storyboards: Map<number, any[]> = new Map()

  constructor(project: Project, characters: Character[]) {
    this.project = project
    this.characters = characters
  }

  // Stage 1: IP Analysis (parallel)
  async analyzeWorldview(novelText: string): Promise<WorkflowResult> {
    try {
      const prompt = `请分析以下小说IP的世界观：

${novelText}

${AGENT_SYSTEM_PROMPTS.ipAnalyzer}`

      const result = await callClaude({
        system: '你是一位顶尖IP分析师。',
        prompt
      })
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }

  async analyzeCharacters(novelText: string): Promise<WorkflowResult> {
    try {
      const prompt = `请分析以下小说中的所有角色：

${novelText}

${AGENT_SYSTEM_PROMPTS.characterSystem}

请为每个重要角色生成完整的视觉特征Tag。`

      const result = await callClaude({
        system: '你是一位角色系统专家。',
        prompt
      })
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }

  async analyzeScenes(novelText: string): Promise<WorkflowResult> {
    try {
      const prompt = `请分析以下小说中的主要场景：

${novelText}

${AGENT_SYSTEM_PROMPTS.sceneDesign}`

      const result = await callClaude({
        system: '你是一位场景设计师。',
        prompt
      })
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }

  // Stage 2: Story Engine (serial)
  async generateStoryOutline(worldview: string, characters: string, scenes: string): Promise<WorkflowResult> {
    try {
      const prompt = `基于以下分析结果，生成完整的${this.project.episode_count}集分集大纲：

世界观：
${worldview}

角色：
${characters}

场景：
${scenes}

${AGENT_SYSTEM_PROMPTS.storyEngine}

注意：
- 必须完整输出所有${this.project.episode_count}集的大纲
- 每集必须有前3秒钩子
- 每集结尾必须有悬念
- 禁止使用占位符`

      const result = await callClaude({
        system: '你是一位AI编剧。',
        prompt,
        maxTokens: 8192
      })
      this.storyOutline = result
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }

  // Stage 3: Director Agent (serial)
  async generateStoryboard(episode: number, episodeScript: string): Promise<WorkflowResult> {
    try {
      const prompt = `请为第${episode}集生成详细的分镜脚本：

${episodeScript}

${AGENT_SYSTEM_PROMPTS.directorAgent}

请确保每个镜头的动作描述详细到可以执行。`

      const result = await callClaude({
        system: '你是一位AI导演。',
        prompt,
        maxTokens: 8192
      })
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }

  // Stage 4: Visual Agent (parallel with sound)
  async generateVisualPrompt(
    shotBrief: string,
    character: Character,
    sceneType: string
  ): Promise<WorkflowResult> {
    try {
      const style = matchStyle(sceneType)
      const styleSuffix = style.promptSuffix.join(', ')

      const prompt = `请将以下分镜转化为完整的英文视频Prompt：

分镜：${shotBrief}

角色信息：
- 视觉Tag：${character.visual_tags.map(t => `${t.tag}:${t.weight}`).join(', ')}

场景类型：${sceneType}
选定风格：${style.nameCN}

${AGENT_SYSTEM_PROMPTS.visualAgent}

风格加成：${styleSuffix}`

      const result = await callClaude({
        system: '你是一位AI视觉设计师。',
        prompt,
        maxTokens: 2048
      })
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }

  async generateSoundDesign(shotBrief: string): Promise<WorkflowResult> {
    try {
      const prompt = `请为以下分镜设计声音：

${shotBrief}

${AGENT_SYSTEM_PROMPTS.soundAgent}`

      const result = await callClaude({
        system: '你是一位AI声音设计师。',
        prompt
      })
      return { status: 'success', data: result }
    } catch (error: any) {
      return { status: 'error', error: error.message }
    }
  }
}
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: add agent orchestrator"
```

---

### Task 19: 创建工作流运行器

**Files:**
- Create: `ai-drama-studio/src/services/workflowRunner.ts`

**Step 1: 创建工作流运行器**

```typescript
import { AgentOrchestrator } from '../agents/orchestrator'
import { Project, Character } from '../types'
import { updateProjectStatus } from '../db/project'

export interface WorkflowProgress {
  stage: 'ip_analysis' | 'story_outline' | 'storyboard' | 'visual_prompt' | 'completed'
  progress: number
  currentTask: string
  result?: any
}

export type ProgressCallback = (progress: WorkflowProgress) => void

export async function runFullWorkflow(
  project: Project,
  characters: Character[],
  novelText: string,
  onProgress: ProgressCallback
): Promise<void> {
  const orchestrator = new AgentOrchestrator(project, characters)

  // Stage 1: Parallel IP Analysis
  onProgress({ stage: 'ip_analysis', progress: 0, currentTask: '分析世界观' })
  const worldviewResult = await orchestrator.analyzeWorldview(novelText)

  onProgress({ stage: 'ip_analysis', progress: 33, currentTask: '分析角色' })
  const charactersResult = await orchestrator.analyzeCharacters(novelText)

  onProgress({ stage: 'ip_analysis', progress: 66, currentTask: '分析场景' })
  const scenesResult = await orchestrator.analyzeScenes(novelText)

  if (worldviewResult.status === 'error' || charactersResult.status === 'error' || scenesResult.status === 'error') {
    throw new Error('IP分析阶段失败')
  }

  onProgress({
    stage: 'ip_analysis',
    progress: 100,
    currentTask: 'IP分析完成',
    result: {
      worldview: worldviewResult.data,
      characters: charactersResult.data,
      scenes: scenesResult.data
    }
  })

  // Update project status
  updateProjectStatus(project.id, 'outline_review')

  // Stage 2: Story Outline (等待用户审核后执行)
  // 此处仅生成，用户审核通过后继续
  onProgress({ stage: 'story_outline', progress: 0, currentTask: '生成剧本大纲' })
  const storyResult = await orchestrator.generateStoryOutline(
    worldviewResult.data,
    charactersResult.data,
    scenesResult.data
  )

  if (storyResult.status === 'error') {
    throw new Error('剧本大纲生成失败')
  }

  updateProjectStatus(project.id, 'storyboard_review')

  onProgress({
    stage: 'story_outline',
    progress: 100,
    currentTask: '剧本大纲完成',
    result: storyResult.data
  })
}

export async function continueStoryboardWorkflow(
  project: Project,
  orchestrator: AgentOrchestrator,
  episodeOutline: string,
  episode: number,
  onProgress: ProgressCallback
): Promise<void> {
  onProgress({ stage: 'storyboard', progress: 0, currentTask: `生成第${episode}集分镜` })

  const storyboardResult = await orchestrator.generateStoryboard(episode, episodeOutline)

  if (storyboardResult.status === 'error') {
    throw new Error(`第${episode}集分镜生成失败`)
  }

  onProgress({
    stage: 'storyboard',
    progress: 100,
    currentTask: `第${episode}集分镜完成`,
    result: storyboardResult.data
  })
}

export async function generateVisualPrompts(
  orchestrator: AgentOrchestrator,
  shots: Array<{ brief: string; character: Character; sceneType: string }>,
  onProgress: ProgressCallback
): Promise<string[]> {
  const prompts: string[] = []
  const total = shots.length

  for (let i = 0; i < total; i++) {
    const { brief, character, sceneType } = shots[i]
    onProgress({
      stage: 'visual_prompt',
      progress: Math.round((i / total) * 100),
      currentTask: `生成镜头${i + 1}的Prompt`
    })

    const result = await orchestrator.generateVisualPrompt(brief, character, sceneType)
    if (result.status === 'success') {
      prompts.push(result.data)
    }
  }

  onProgress({
    stage: 'visual_prompt',
    progress: 100,
    currentTask: '所有Prompt生成完成'
  })

  return prompts
}
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: add workflow runner"
```

---

## Phase 3 完成：Claude Agent系统构建 ✅

---

## Phase 4: 工作流与存储集成

### Task 20: 创建主工作流界面

**Files:**
- Create: `ai-drama-studio/src/components/WorkflowRunner.tsx`

**Step 1: 创建 WorkflowRunner 组件**

```tsx
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { runFullWorkflow, WorkflowProgress } from '../services/workflowRunner'
import { useProject } from '../hooks/useProject'

export function WorkflowRunner() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id || '0')
  const { project, characters, loading } = useProject(projectId)

  const [novelText, setNovelText] = useState('')
  const [progress, setProgress] = useState<WorkflowProgress | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    if (!novelText.trim()) {
      setError('请输入小说内容')
      return
    }
    if (!project) return

    setIsRunning(true)
    setError(null)
    setProgress(null)

    try {
      await runFullWorkflow(project, characters, novelText, setProgress)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsRunning(false)
    }
  }

  if (loading) return <div>加载中...</div>
  if (!project) return <div>项目不存在</div>

  const stages = [
    { key: 'ip_analysis', name: 'IP分析' },
    { key: 'story_outline', name: '剧本大纲' },
    { key: 'storyboard', name: '分镜脚本' },
    { key: 'visual_prompt', name: '视觉Prompt' },
    { key: 'completed', name: '完成' }
  ]

  return (
    <div className="workflow-runner">
      <h1>启动工作流：{project.name}</h1>

      <div className="novel-input">
        <h2>输入小说内容</h2>
        <textarea
          value={novelText}
          onChange={e => setNovelText(e.target.value)}
          placeholder="粘贴小说内容或简介..."
          disabled={isRunning}
        />
      </div>

      <button
        className="primary start-button"
        onClick={handleStart}
        disabled={isRunning}
      >
        {isRunning ? '运行中...' : '启动AI创作流程'}
      </button>

      {error && <div className="error">{error}</div>}

      {progress && (
        <div className="progress-panel">
          <h2>工作进度</h2>
          <div className="stages">
            {stages.map((stage, index) => {
              const currentIndex = stages.findIndex(s => s.key === progress.stage)
              const isComplete = index < currentIndex
              const isCurrent = stage.key === progress.stage

              return (
                <div
                  key={stage.key}
                  className={`stage ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''}`}
                >
                  <div className="stage-indicator">
                    {isComplete ? '✓' : index + 1}
                  </div>
                  <div className="stage-name">{stage.name}</div>
                  {isCurrent && (
                    <div className="stage-progress">
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{ width: `${progress.progress}%` }}
                        />
                      </div>
                      <div className="current-task">{progress.currentTask}</div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {progress.result && (
            <div className="result-preview">
              <h3>输出预览</h3>
              <pre>{JSON.stringify(progress.result, null, 2).substring(0, 500)}...</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
```

**Step 2: 添加路由**

```tsx
<Route path="/project/:id/workflow" element={<WorkflowRunner />} />
```

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: add workflow runner UI"
```

---

### Task 21: 创建审核节点组件

**Files:**
- Create: `ai-drama-studio/src/components/ReviewNodes.tsx`

**Step 1: 创建 ReviewNodes 组件**

```tsx
import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { updateProjectStatus } from '../db/project'

export function ReviewNodes() {
  const { id } = useParams<{ id: string }>()
  const projectId = parseInt(id || '0')

  const [outlineApproved, setOutlineApproved] = useState(false)
  const [first3Approved, setFirst3Approved] = useState(false)

  const handleApproveOutline = () => {
    updateProjectStatus(projectId, 'storyboard_review')
    setOutlineApproved(true)
  }

  const handleApproveFirst3 = () => {
    updateProjectStatus(projectId, 'producing')
    setFirst3Approved(true)
  }

  const currentStatus = outlineApproved ? 'storyboard_review' : 'draft'

  return (
    <div className="review-nodes">
      <h1>审核节点</h1>

      <div className="review-node">
        <h2>节点1：剧本大纲审核</h2>
        <p>审核AI生成的剧本大纲是否符合预期</p>
        <div className="node-actions">
          <Link to={`/project/${projectId}/outline`}>查看大纲</Link>
          <button
            className="primary"
            onClick={handleApproveOutline}
            disabled={outlineApproved}
          >
            {outlineApproved ? '已通过' : '通过审核'}
          </button>
        </div>
      </div>

      <div className="review-node">
        <h2>节点2：前3集分镜审核</h2>
        <p>审核前3集的分镜脚本和Prompt</p>
        <div className="node-actions">
          <Link to={`/project/${projectId}/episode/1/shots`}>查看分镜</Link>
          <button
            className="primary"
            onClick={handleApproveFirst3}
            disabled={!outlineApproved || first3Approved}
          >
            {first3Approved ? '已通过' : '通过审核'}
          </button>
        </div>
      </div>

      <div className="status-indicator">
        当前项目状态：{currentStatus}
      </div>
    </div>
  )
}
```

**Step 2: 添加路由**

```tsx
<Route path="/project/:id/review" element={<ReviewNodes />} />
```

**Step 3: 提交**

```bash
git add -A && git commit -m "feat: add review nodes UI"
```

---

### Task 22: 集成 Obsidian 导出功能

**Files:**
- Modify: `ai-drama-studio/src/components/ProjectDetail.tsx`

**Step 1: 添加导出按钮**

```tsx
import { exportToObsidian } from '../services/obsidianSync'
import { useProject } from '../hooks/useProject'
import { getShotsByProject } from '../db/shot'

// 在 ProjectDetail 组件中添加导出函数
const handleExport = () => {
  if (!project) return
  const characters = getCharactersByProject(project.id)
  const shots = getShotsByProject(project.id)
  exportToObsidian({ project, characters, shots })
  alert('已导出到Obsidian')
}

// 在界面上添加导出按钮
<button onClick={handleExport}>导出到Obsidian</button>
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: integrate obsidian export"
```

---

### Task 23: 添加错误处理和加载状态

**Files:**
- Modify: `ai-drama-studio/src/components/*.tsx`

**Step 1: 为关键组件添加错误边界**

```tsx
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: string | null }
> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error: error.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>出错了</h2>
          <p>{this.state.error}</p>
          <button onClick={() => window.location.reload()}>重新加载</button>
        </div>
      )
    }
    return this.props.children
  }
}
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: add error boundaries"
```

---

## Phase 4 完成：工作流与存储集成 ✅

---

## Phase 5: 端到端测试

### Task 24: 创建示例项目数据

**Files:**
- Create: `ai-drama-studio/src/db/seedData.ts`

**Step 1: 创建测试数据**

```typescript
import { createProject } from './project'
import { createCharacter } from './character'
import { createShot } from './shot'
import { VisualTag } from '../types'

export function createSampleProject() {
  const project = createProject('草莓与罐头', '原创', 'modern', 12)

  const maleTags: VisualTag[] = [
    { category: 'hair', tag: '(messy black hair:1.2)', weight: 1.2 },
    { category: 'face', tag: '(handsome face:1.1)', weight: 1.1 },
    { category: 'eyes', tag: '(cold dark eyes:1.3)', weight: 1.3 },
    { category: 'clothing', tag: '(black hoodie:1.2)', weight: 1.2 }
  ]
  createCharacter(project.id, '男主', '落魄但有梦想的青年', maleTags, 'ref-nan-001')

  const femaleTags: VisualTag[] = [
    { category: 'hair', tag: '(long wavy hair:1.2)', weight: 1.2 },
    { category: 'face', tag: '(sweet face:1.1)', weight: 1.1 },
    { category: 'eyes', tag: '(bright eyes:1.2)', weight: 1.2 },
    { category: 'clothing', tag: '(green dress:1.3)', weight: 1.3 }
  ]
  createCharacter(project.id, '女主', '健康饮食博主', femaleTags, 'ref-nv-001')

  // Episode 1, Scene 1
  createShot(
    project.id, 1, '场景1',
    1, 'Extreme Close-Up', 'push in',
    '女主（牛油果绿天使）表情从惊讶转为坚定',
    'Extreme Close-Up shot, push in camera movement. A beautiful young woman...',
    '轻快的木吉他BGM',
    '警报音效',
    'VO_Emotion: 惊讶'
  )

  return project
}
```

**Step 2: 提交**

```bash
git add -A && git commit -m "feat: add seed data"
```

---

### Task 25: 运行端到端测试

**Step 1: 启动开发服务器**

```bash
cd ai-drama-studio && npm run dev &
sleep 5
```

**Step 2: 测试项目列表页面**

```bash
curl -s http://localhost:3000 | grep -o '<h1>.*</h1>'
```

**Step 3: 测试创建项目**

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"测试项目","source":"测试","type":"modern","episodeCount":12}' \
  http://localhost:3000/api/projects
```

**Step 4: 提交**

```bash
git add -A && git commit -m "test: e2e verification"
```

---

### Task 26: 清理和文档

**Step 1: 创建 README**

```bash
cat > ai-drama-studio/README.md << 'EOF'
# AI漫剧工业化生产系统

## 项目介绍

一个人机协作的AI漫剧工业化生产系统，将小说IP自动转化为电影级AI漫剧生产资产。

## 技术栈

- 前端：React 18 + Vite + TypeScript
- 数据库：SQLite (better-sqlite3)
- 创作引擎：Claude API (多Agent协同)
- 内容存储：Obsidian Vault

## 快速开始

```bash
cd ai-drama-studio
npm install
npm run dev
```

## 核心功能

1. 项目管理
2. 角色管理（含视觉Tag）
3. 工作流自动化
4. 镜头审核
5. Obsidian导出

## 工作流程

1. 创建项目
2. 启动AI工作流（输入小说）
3. 审核剧本大纲
4. 审核前3集分镜
5. 批量生成Prompt
6. 导出到Obsidian

## 项目结构

```
src/
├── agents/        # Claude Agent系统
├── components/    # React组件
├── db/           # SQLite数据库操作
├── hooks/        # React Hooks
├── services/     # 业务服务
└── types/        # TypeScript类型
```
EOF
```

**Step 2: 最终提交**

```bash
git add -A && git commit -m "docs: add README"
```

---

## Phase 5 完成：端到端测试 ✅

---

## 实现计划完成

**总计：26个任务，分为5个阶段**

| Phase | 任务数 | 状态 |
|-------|--------|------|
| Phase 1: 前端基础设施 | 8 | ⬜ |
| Phase 2: 前端核心UI | 6 | ⬜ |
| Phase 3: Claude Agent系统 | 7 | ⬜ |
| Phase 4: 工作流集成 | 4 | ⬜ |
| Phase 5: 端到端测试 | 3 | ⬜ |

---

**Plan saved to:** `docs/plans/2026-03-24-ai-drama-studio-implementation-plan.md`
