// 项目配置
export interface ProjectConfig {
  title: string;
  type: string;
  platform: string;
  duration: string;
  episodes: string;
  style: string;
  budget: string;
}

// 工作流步骤定义
export interface Step {
  id: number;
  label: string;
  icon: string;
  short: string;
}

// 资产项
export interface Asset {
  id: string;
  name: string;
  type: 'character' | 'scene' | 'video';
  dataUrl: string; // base64 blob URL
  prompt?: string; // 关联的生成 Prompt
  createdAt: number;
}

// 分镜项
export interface Shot {
  id: number;
  description: string;
  camera: string;
  imagePrompt: string;
  audioPrompt: string;
  duration?: number;
  imageUrl?: string;
  videoUrl?: string;
}

// API 配置
export interface ApiConfig {
  model: string;
  maxTokens: number;
  apiKey: string;
}

// 流式回调
export type StreamCallback = (chunk: string) => void;
export type DoneCallback = () => void;
