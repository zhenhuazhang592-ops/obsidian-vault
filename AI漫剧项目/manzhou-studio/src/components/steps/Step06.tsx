import { StepPanel, GenerateBtn, OutputBox } from '@/components/ui';
import { useStore } from '@/store';
import { useGenerate } from '@/hooks';
import { useCallback } from 'react';

export function Step06() {
  const { projectConfig, outputs, loading } = useStore();
  const { gen } = useGenerate();

  function genDoc() {
    const docPrompt = `生成一份专业、完整、可直接发给团队执行的《${projectConfig.title || '项目'} 制作操作手册》。
将已生成的角色档案、场景Prompt、分镜表进行归纳排版。
---项目配置---
平台：${projectConfig.platform}，类型：${projectConfig.type}，风格：${projectConfig.style}
---`;
    gen('doc', '你是执行制片人，负责撰写SOP手册。', docPrompt);
  }

  const handleDownload = useCallback(() => {
    if (!outputs['doc']) return;
    const blob = new Blob([outputs['doc'] as string], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${projectConfig.title || 'AI项目'}_工作手册.md`;
    a.click();
  }, [outputs['doc'], projectConfig.title]);

  return (
    <StepPanel title="FINAL · 导出制作手册" icon="📄">
      <GenerateBtn onClick={genDoc} loading={!!loading['doc']} label="📄 生成可交付 Markdown 格式手册" />
      <OutputBox content={outputs['doc'] ?? ''} loading={!!loading['doc']} />
      {outputs['doc'] && !loading['doc'] && (
        <button type="button" className="export-btn" onClick={handleDownload}>
          ⬇️ 下载 .md 操作手册
        </button>
      )}
    </StepPanel>
  );
}
