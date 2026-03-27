import { StepPanel, Field, Input, GenerateBtn, OutputBox } from '@/components/ui';
import { useStore } from '@/store';
import { useGenerate } from '@/hooks';
import { useState } from 'react';

export function Step05() {
  const { projectConfig, outputs, loading, setCurrentStep } = useStore();
  const { gen } = useGenerate();
  const [shotNotes, setShotNotes] = useState('');

  function genStep5() {
    gen(
      's5',
      '你是分镜大师。请生成可直接导入剪辑软件或AI视频生成器的完整分镜表。',
      `结合前序资产，生成按秒切分的详细分镜表。包含运镜方向（推拉摇移）、画面描述、图像Prompt和音效提示。
平台：${projectConfig.platform}，画幅：竖屏9:16。
${shotNotes ? `特殊要求：${shotNotes}` : ''}
---剧本---
${outputs['s3'] || ''}
---资产---
${outputs['s4'] || ''}
---`,
    );
  }

  return (
    <StepPanel title="Step 05 · 可执行分镜脚本" icon="🎞️">
      <Field label="补充分镜要求 (可选)">
        <Input
          value={shotNotes}
          onChange={setShotNotes}
          multiline
          rows={2}
          placeholder="例如：需要更多特写镜头，强调情感张力..."
        />
      </Field>
      <GenerateBtn onClick={genStep5} loading={!!loading['s5']} label="🎞️ 生成全要素分镜表" />
      <OutputBox content={outputs['s5'] ?? ''} loading={!!loading['s5']} />
      {outputs['s5'] && !loading['s5'] && (
        <button type="button" className="export-btn" onClick={() => setCurrentStep(6)}>
          🎉 导出最终项目操作手册
        </button>
      )}
    </StepPanel>
  );
}
