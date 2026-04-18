/**
 * 全局类型定义
 * 定义所有阶段产物和会话状态的 TypeScript 接口
 */

// ==================== 阶段产物类型 ====================

export interface Phase0Research {
  topic: string;
  tavilyResults: TavilyResult[];
  youtubeResults: YouTubeResult[];
  summary: string;
  keyInsights: string[];
  sources: Source[];
  completedAt: string;
}

export interface TavilyResult {
  title: string;
  url: string;
  content: string;
  score: number;
}

export interface YouTubeResult {
  title: string;
  videoId: string;
  channelName: string;
  duration: string;
  transcript?: string;
}

export interface Source {
  title: string;
  url: string;
  type: 'article' | 'video' | 'paper';
}

// ==================== Stage 1 选题 ====================

export interface Stage1Topic {
  selectedTitle: string;
  subtitle: string;
  targetReader: string;
  painPoint: string;
  uniqueValue: string;
  viralPotential: string;
  options: TopicOption[];
  reasoning: string; // Agent 思考过程
  decidedAt: string;
}

export interface TopicOption {
  title: string;
  subtitle: string;
  targetReader: string;
  painPoint: string;
  uniqueValue: string;
  viralPotential: string;
  titleFormula: string;
}

// ==================== Stage 2 观点 ====================

export interface Stage2Thesis {
  coreThesis: string;
  supportingPoints: ThesisPoint[];
  reasoning: string; // Agent 思考过程
  confirmedAt: string;
}

export interface ThesisPoint {
  point: string;
  commonMisconception: string;
  thinkersToCite: string[];
  logicalConnection: string;
}

// ==================== Stage 3 大纲 ====================

export interface Stage3Outline {
  title: string;
  opening: OpeningStructure;
  sections: OutlineSection[];
  conclusion: ConclusionStructure;
  reasoning: string; // Agent 思考过程
  confirmedAt: string;
}

export interface OpeningStructure {
  hook: string;
  transition: string;
  dataSupport?: string;
  vulnerability: string;
  promise: string;
  importance: string;
  expectation: string;
}

export interface OutlineSection {
  heading: string;
  keyPoints: string[];
  examples: string[];
  framework?: string; // 5步论证模型
}

export interface ConclusionStructure {
  summary: string;
  callToAction: string;
}

// ==================== Stage 4 正文 ====================

export interface Stage4Draft {
  title: string;
  content: string;
  wordCount: number;
  style: 'dan-koe';
  verifiedAt: string;
}

// ==================== Stage 5 润色 ====================

export interface Stage5Polished {
  title: string;
  content: string;
  wordCount: number;
  antiAiCheck: AntiAiCheckResult;
  seoOptimization: SEOResult;
  geoOptimization: GEOResult;
  finalAt: string;
}

export interface AntiAiCheckResult {
  passed: boolean;
  violations: string[];
}

export interface SEOResult {
  keywords: string[];
  densityCheck: boolean;
  metaDescription: string;
}

export interface GEOResult {
  citations: string[];
  entityOptimization: string[];
  aiReadableScore: number;
}

// ==================== Agent 会话状态 ====================

export interface AgentSession {
  sessionId: string;
  topic: string;
  outputDir: string;
  phase: PhaseState;
  currentStage: StageState;
  createdAt: string;
  updatedAt: string;
}

export type PhaseState = 'idle' | 'phase0' | 'stage1' | 'stage2' | 'stage3' | 'stage4' | 'stage5' | 'output' | 'completed';

export type StageState = 'pending' | 'thinking' | 'waiting_user' | 'confirmed' | 'done';

export interface StageOutput {
  stage: string;
  status: StageState;
  thinking?: string; // Agent 思考过程
  result?: unknown; // 阶段产物
  userDecision?: unknown; // 用户决策
  completedAt?: string;
}

// ==================== wiki 类型 ====================

export interface WikiPage {
  title: string;
  type: 'source' | 'entity' | 'concept' | 'synthesis';
  content: string;
  tags: string[];
  sources: string[];
  lastUpdated: string;
}

export interface WikiQueryResult {
  pages: WikiPage[];
  query: string;
  matchedAt: string;
}

// ==================== 会话消息 ====================

export interface ConversationMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking?: string; // Claude extended thinking
}

// ==================== LLM 模型选择 ====================

export type LLMModel = 'claude-sonnet' | 'claude-opus' | 'qwen3-max';

export interface ModelConfig {
  model: LLMModel;
  temperature: number;
  maxTokens: number;
}
