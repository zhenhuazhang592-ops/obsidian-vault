import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ProjectConfig, Asset, ApiConfig } from '@/types';

interface AppState {
  // 工作流
  currentStep: number;
  setCurrentStep: (step: number) => void;

  // 项目配置
  projectConfig: ProjectConfig;
  setProjectConfig: (config: Partial<ProjectConfig>) => void;

  // AI 输出内容
  outputs: Record<string, string>;
  saveOutput: (key: string, value: string) => void;
  clearOutput: (key: string) => void;

  // 加载状态
  loading: Record<string, boolean>;
  setLoading: (key: string, value: boolean) => void;

  // API 配置
  apiConfig: ApiConfig;
  setApiConfig: (config: Partial<ApiConfig>) => void;

  // 资产库
  assets: Asset[];
  addAsset: (asset: Asset) => void;
  removeAsset: (id: string) => void;

  // 数据重置
  clearAll: () => void;
}

const DEFAULT_CONFIG: ProjectConfig = {
  title: '',
  type: '动画',
  platform: '小红书',
  duration: '120',
  episodes: '10',
  style: '清新治愈',
  budget: '中等',
};

const DEFAULT_API_CONFIG: ApiConfig = {
  model: 'qwen-max',
  maxTokens: 8192,
  apiKey: '',
};

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      currentStep: 0,
      setCurrentStep: (step) => set({ currentStep: step }),

      projectConfig: DEFAULT_CONFIG,
      setProjectConfig: (config) =>
        set((state) => ({
          projectConfig: { ...state.projectConfig, ...config },
        })),

      outputs: {},
      saveOutput: (key, value) =>
        set((state) => ({
          outputs: { ...state.outputs, [key]: value },
        })),
      clearOutput: (key) =>
        set((state) => {
          const next = { ...state.outputs };
          delete next[key];
          return { outputs: next };
        }),

      loading: {},
      setLoading: (key, value) =>
        set((state) => ({
          loading: { ...state.loading, [key]: value },
        })),

      apiConfig: DEFAULT_API_CONFIG,
      setApiConfig: (config) =>
        set((state) => ({
          apiConfig: { ...state.apiConfig, ...config },
        })),

      assets: [],
      addAsset: (asset) =>
        set((state) => ({
          assets: [...state.assets, asset],
        })),
      removeAsset: (id) =>
        set((state) => ({
          assets: state.assets.filter((a) => a.id !== id),
        })),

      clearAll: () =>
        set({
          outputs: {},
          loading: {},
          assets: [],
          projectConfig: DEFAULT_CONFIG,
        }),
    }),
    {
      name: 'manzhou-studio-v2',
      partialize: (state) => ({
        projectConfig: state.projectConfig,
        apiConfig: {
          apiKey: state.apiConfig.apiKey,
          model: state.apiConfig.model,
          maxTokens: state.apiConfig.maxTokens,
        },
        outputs: state.outputs,
        assets: state.assets,
      }),
    },
  ),
);
