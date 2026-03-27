import { useState } from 'react';
import { StepPanel, Field, Input, Tags, GenerateBtn, OutputBox } from '@/components/ui';
import { useStore } from '@/store';
import { useGenerate } from '@/hooks';

const STYLE_PRESETS = ['都市职场', '清新治愈', '古风仙侠', '甜宠爱情', '悬疑惊悚', '复仇爽剧', '赛博朋克'];
const PLATFORMS = ['抖音', '小红书', '快手', '视频号', 'B站'];
const DRAMA_TYPES = ['都市', '动画', '古风', '甜宠', '悬疑', '复仇', '仙侠'];
const DURATIONS = ['60', '90', '120', '180'];

export function Step00() {
  const { projectConfig, setProjectConfig, setCurrentStep } = useStore();

  return (
    <StepPanel title="Step 00 · 项目全局配置" icon="⚙️">
      <div className="grid-2">
        <Field label="项目名称 (IP Title)">
          <Input
            value={projectConfig.title}
            onChange={(v) => setProjectConfig({ title: v })}
            placeholder="例：牛油果天使 / 格子间女人"
          />
        </Field>
        <Field label="剧集类型 (Genre)">
          <Tags
            options={DRAMA_TYPES}
            selected={projectConfig.type}
            onChange={(v) => setProjectConfig({ type: v })}
          />
        </Field>
        <Field label="核心投放平台">
          <Tags
            options={PLATFORMS}
            selected={projectConfig.platform}
            onChange={(v) => setProjectConfig({ platform: v })}
          />
        </Field>
        <Field label="单集目标时长">
          <Tags
            options={DURATIONS}
            selected={projectConfig.duration}
            onChange={(v) => setProjectConfig({ duration: v })}
          />
        </Field>
        <Field label="视觉风格预设 (Aesthetic)">
          <Tags
            options={STYLE_PRESETS}
            selected={projectConfig.style}
            onChange={(v) => setProjectConfig({ style: v })}
          />
        </Field>
      </div>
      <button type="button" className="primary-btn" onClick={() => setCurrentStep(1)}>
        进入编剧工作台 →
      </button>
    </StepPanel>
  );
}

export function Step01() {
  const { projectConfig, outputs, loading, setCurrentStep } = useStore();
  const { gen } = useGenerate();
  const [novel, setNovel] = useState('');

  function genStep1() {
    gen(
      's1',
      '你是顶级影视/短剧改编编剧。严格按以下格式输出，保持简洁有力。',
      `请将以下内容改编为AI视频生成专用的标准化剧本改编稿。
项目信息：项目名：${projectConfig.title || '未命名'} | 类型：${projectConfig.type} | 单集时长：${projectConfig.duration}秒 | 目标平台：${projectConfig.platform}
改编要求：
1. 删除内心独白，全部转化为可见动作/对话/视觉意象。
2. 每30秒一个小冲突，每60秒一个情绪转折。
3. 对白必须简练，每句台词不超过15个中文字符。
4. 开场5秒立刻抓取眼球（视觉冲击或情绪冲突）。
---原始素材---
${novel || '（未提供内容）'}
---`,
    );
  }

  return (
    <StepPanel title="Step 01 · 剧本降维转换" icon="📖">
      <Field label="输入原始文本 (文案/小说片段)" hint="字数建议在 3000 字以内，AI 会自动提炼动作与对白">
        <Input
          value={novel}
          onChange={setNovel}
          multiline
          rows={10}
          placeholder="在此粘贴小说或文案原文..."
        />
      </Field>
      <GenerateBtn onClick={genStep1} loading={!!loading['s1']} label="✨ 开始提炼剧本" />
      <OutputBox content={outputs['s1'] ?? ''} loading={!!loading['s1']} />
      {outputs['s1'] && !loading['s1'] && (
        <button type="button" className="next-btn" onClick={() => setCurrentStep(2)}>
          提取 IP 资产 →
        </button>
      )}
    </StepPanel>
  );
}

export function Step02() {
  const { outputs, loading, setCurrentStep } = useStore();
  const { gen } = useGenerate();
  const [charCount, setCharCount] = useState('3');
  const [sceneCount, setSceneCount] = useState('4');
  const [ipNotes, setIpNotes] = useState('');

  function genStep2() {
    gen(
      's2',
      '你是资深IP资产解析师。请生成标准化YAML格式的IP档案。',
      `请从以下改编稿中提取角色和场景资产，生成完整IP档案。
要求提取 ${charCount} 个主要角色和 ${sceneCount} 个核心场景。
输出YAML结构，包含外貌锁、风格锁、场景氛围等细节。
${ipNotes ? `额外要求：${ipNotes}` : ''}
---改编稿---
${outputs['s1'] || '（待生成）'}
---`,
    );
  }

  return (
    <StepPanel title="Step 02 · 核心 IP 资产解析" icon="🧬">
      <div className="grid-2" style={{ marginBottom: 20 }}>
        <Field label="锁定核心角色数">
          <Tags options={['2', '3', '4', '5']} selected={charCount} onChange={setCharCount} />
        </Field>
        <Field label="锁定主场景数">
          <Tags options={['3', '4', '5', '6']} selected={sceneCount} onChange={setSceneCount} />
        </Field>
      </div>
      <Field label="补充 IP 解析要求 (可选)">
        <Input
          value={ipNotes}
          onChange={setIpNotes}
          multiline
          rows={2}
          placeholder="例如：角色需要民国气质，场景要写实风格..."
        />
      </Field>
      <GenerateBtn onClick={genStep2} loading={!!loading['s2']} label="🧬 解析 IP 角色与场景" />
      <OutputBox content={outputs['s2'] ?? ''} loading={!!loading['s2']} />
      {outputs['s2'] && !loading['s2'] && (
        <button type="button" className="next-btn" onClick={() => setCurrentStep(3)}>
          进入导演剧本阶段 →
        </button>
      )}
    </StepPanel>
  );
}

export function Step03() {
  const { projectConfig, outputs, loading, setCurrentStep } = useStore();
  const { gen } = useGenerate();
  const [scriptNotes, setScriptNotes] = useState('');

  function genStep3() {
    gen(
      's3',
      '你是AI漫剧导演。生成包含：剧本内容+导演意图+音频标注的三合一剧本。',
      `根据改编稿和IP档案，生成第1集的标准化剧本。
目标时长：${projectConfig.duration}秒，风格：${projectConfig.style}。包含详细的景别、情绪值、BGM提示。
${scriptNotes ? `额外要求：${scriptNotes}` : ''}
---改编稿---
${outputs['s1'] || ''}
---IP档案---
${outputs['s2'] || '（IP档案待生成）'}
---`,
    );
  }

  return (
    <StepPanel title="Step 03 · 导演三合一剧本" icon="🎬">
      <Field label="补充导演要求 (可选)">
        <Input
          value={scriptNotes}
          onChange={setScriptNotes}
          multiline
          rows={2}
          placeholder="例如：增加悬疑感，配乐要紧凑..."
        />
      </Field>
      <GenerateBtn onClick={genStep3} loading={!!loading['s3']} label="🎬 生成分场剧本" />
      <OutputBox content={outputs['s3'] ?? ''} loading={!!loading['s3']} />
      {outputs['s3'] && !loading['s3'] && (
        <button type="button" className="next-btn" onClick={() => setCurrentStep(4)}>
          生成视觉 Prompt 库 →
        </button>
      )}
    </StepPanel>
  );
}
