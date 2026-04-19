/**
 * 本能学习模块的类型定义
 */

export interface Instinct {
  id: string;
  trigger: string;
  confidence: number;
  domain: string;           // 文章开头 | 大纲结构 | 去AI味 | 配图风格 | 选题 | 观点
  source: string;          // session-YYYYMMDD
  scope: string;            // 'huage-agent'
  behavior: string;         // 具体行为描述
  evidence: string;         // 证据/案例
  boundary: string;         // 适用边界
}

export interface SessionMeta {
  topic: string;
  date: string;
  outputDir: string;
  stages: {
    topic: {
      selected: string;
      alternatives: string[];
      reason: string;
      targetReader: string;
      painPoint: string;
    } | null;
    thesis: {
      points: Array<{ text: string; type: 'insight' | 'story' | 'data' }>;
    } | null;
    outline: {
      type: string;
      hooks: string[];
      sections: Array<{ heading: string; function: string }>;
      opening: string;
    } | null;
    writing: {
      wordCount: number;
    } | null;
    polish: {
      antiAiScore: number;
      violations: string[];
      seoKeywords: string[];
      geoScore: number;
    } | null;
  };
  wikiInjected: string[];
  images: Array<{ section: string; promptStyle: string }>;
}

export interface ExtractedPattern {
  type: '选题' | '定位' | '观点类型' | '大纲结构' | '钩子公式' | '去AI味' | '配图风格';
  domain: string;
  trigger: string;
  behavior: string;
  evidence: string;
  boundary: string;
  confidence: number;        // 初始 0.6
}
