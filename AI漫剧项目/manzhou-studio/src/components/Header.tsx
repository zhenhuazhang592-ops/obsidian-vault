import { useState } from 'react';
import { useStore } from '@/store';
import type { Step } from '@/types';
import { SettingsModal } from './SettingsModal';

const STEPS: Step[] = [
  { id: 0, label: '项目配置', icon: '⚙️', short: 'S00' },
  { id: 1, label: '小说改编', icon: '📖', short: 'S01' },
  { id: 2, label: 'IP解析', icon: '🧬', short: 'S02' },
  { id: 3, label: '剧本生成', icon: '🎬', short: 'S03' },
  { id: 4, label: '角色&场景', icon: '🎭', short: 'S05' },
  { id: 5, label: '分镜脚本', icon: '🎞️', short: 'S06' },
  { id: 6, label: '操作文档', icon: '📄', short: 'OUT' },
];

export { STEPS };

const STEP_OUTPUT_KEYS = ['s1', 's2', 's3', 's4', 's5', 's5', 'doc'];

export function Header() {
  const { apiConfig } = useStore();
  const [showSettings, setShowSettings] = useState(false);

  return (
    <>
      <header className="app-header">
        <div>
          <div className="app-logo">🎬 AI漫剧工业化创作站</div>
          <div className="app-tagline">Concept → IP → Script → Prompt → Storyboard 闭环系统</div>
        </div>
        <div className="header-right">
          {apiConfig.apiKey ? (
            <div className="api-status api-status--ready">
              🟢 API 就绪 · {apiConfig.model}
            </div>
          ) : (
            <div className="api-status api-status--warn">
              ⚠️ 点击右侧配置 API Key
            </div>
          )}
          <button type="button" className="settings-btn" onClick={() => setShowSettings(true)}>
            ⚙️ 设置
          </button>
        </div>
      </header>
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </>
  );
}

export { STEP_OUTPUT_KEYS };
