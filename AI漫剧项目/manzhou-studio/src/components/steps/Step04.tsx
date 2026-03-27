import { StepPanel, Field, Input, GenerateBtn, OutputBox } from '@/components/ui';
import { useStore } from '@/store';
import { useGenerate } from '@/hooks';
import { useState } from 'react';

export function Step04() {
  const { projectConfig, outputs, loading, setCurrentStep } = useStore();
  const { gen } = useGenerate();
  const [charNotes, setCharNotes] = useState('');

  function genStep4() {
    gen(
      's4',
      '你是AI视觉总监。请为AI绘画/视频工具生成精准的 Prompt 参数。',
      `根据IP档案，生成角色DNA三视图提示词和场景图生成提示词（Midjourney/Niji/Seedance风格）。
包含：正面、侧面、日常穿搭、核心场景氛围图的详细英文与中文对照Prompt。
风格预设：${projectConfig.style}。
${charNotes ? `特殊要求：${charNotes}` : ''}
---IP档案---
${outputs['s2'] || '（IP档案待生成）'}
---`,
    );
  }

  return (
    <StepPanel title="Step 04 · AI 视觉 Prompt 库构建" icon="🎭">
      <Field label="补充视觉风格要求 (可选)">
        <Input
          value={charNotes}
          onChange={setCharNotes}
          multiline
          rows={2}
          placeholder="例如：角色需要民国气质，场景要写实风格..."
        />
      </Field>
      <GenerateBtn onClick={genStep4} loading={!!loading['s4']} label="🎨 生成一致性生图/视频 Prompt" />
      <OutputBox content={outputs['s4'] ?? ''} loading={!!loading['s4']} />
      {outputs['s4'] && !loading['s4'] && (
        <button type="button" className="next-btn" onClick={() => setCurrentStep(5)}>
          打磨最终分镜表 →
        </button>
      )}
    </StepPanel>
  );
}
