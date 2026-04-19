/**
 * PatternExtractor — 从 SessionMeta 提取创作模式
 * 纯内存计算，无 I/O，无 LLM 调用。
 */

import { SessionMeta, ExtractedPattern } from './types.js';

export class PatternExtractor {
  constructor(private meta: SessionMeta) {}

  extract(): ExtractedPattern[] {
    const patterns: ExtractedPattern[] = [];

    if (this.meta.stages.topic?.selected) {
      patterns.push(this.extractTopicPattern());
      patterns.push(this.extractPositioningPattern());
    }
    if (this.meta.stages.thesis?.points.length) {
      patterns.push(this.extractThesisPattern());
    }
    if (this.meta.stages.outline) {
      patterns.push(this.extractOutlinePattern());
      if (this.meta.stages.outline.hooks.length) {
        patterns.push(this.extractHookPattern());
      }
    }
    if (this.meta.stages.polish?.violations.length) {
      patterns.push(this.extractAntiAiPattern());
    }
    if (this.meta.images.length) {
      patterns.push(this.extractImagePattern());
    }

    return patterns;
  }

  /** 打印摘要到 console（供用户确认前预览） */
  printSummary(patterns: ExtractedPattern[]): void {
    console.log('\n━━━ 提取到以下创作模式 ━━━');
    patterns.forEach((p, i) => {
      console.log(`\n[${i + 1}] ${p.type}（confidence: ${p.confidence}）`);
      console.log(`    触发: ${p.trigger}`);
      console.log(`    行为: ${p.behavior.slice(0, 80)}...`);
    });
    console.log('');
  }

  /** 将 Pattern 转为 Instinct YAML 字符串 */
  toYaml(p: ExtractedPattern): string {
    const id = `huage-agent-${p.type}-${this.meta.date.replace(/-/g, '')}`;
    return `---
id: ${id}
trigger: "${p.trigger}"
confidence: ${p.confidence}
domain: ${p.domain}
source: session-${this.meta.date.replace(/-/g, '')}
scope: huage-agent
---

# ${p.type}模式

## 行为
${p.behavior}

## 证据
- 会话：${this.meta.date}
- 案例：${p.evidence}

## 适用边界
${p.boundary}
`;
  }

  // ── private extractors ──────────────────────────────────────

  private extractTopicPattern(): ExtractedPattern {
    const topic = this.meta.stages.topic!;
    return {
      type: '选题',
      domain: '选题方向',
      trigger: `当用户提出"${topic.selected.slice(0, 10)}..."类话题时`,
      behavior: `有效选题方向：${topic.selected}。目标读者：${topic.targetReader}。痛点：${topic.painPoint}。`,
      evidence: topic.selected,
      boundary: '适用于：个人成长/职场/理财类话题\n不适用于：技术教程/新闻事件类',
      confidence: 0.6,
    };
  }

  private extractPositioningPattern(): ExtractedPattern {
    const topic = this.meta.stages.topic!;
    return {
      type: '定位',
      domain: '读者定位',
      trigger: `当文章目标读者是"${topic.targetReader}"时`,
      behavior: `目标读者设定为${topic.targetReader}，从${topic.painPoint}切入，能产生共鸣。`,
      evidence: `读者=${topic.targetReader}，痛点=${topic.painPoint}`,
      boundary: '适用于：经验分享/方法论类文章\n不适用于：纯知识科普/客观报道',
      confidence: 0.6,
    };
  }

  private extractThesisPattern(): ExtractedPattern {
    const points = this.meta.stages.thesis!.points;
    const types = points.map(p => p.type);
    const typeDist = types.join(' / ');
    return {
      type: '观点类型',
      domain: '观点结构',
      trigger: '当构建文章核心观点时',
      behavior: `观点类型分布：${typeDist}。${points.map(p => p.text).join('；')}。`,
      evidence: points.map(p => p.text).join('；'),
      boundary: '适用于：观点型/方法论类文章\n不适用于：纯叙事/故事类',
      confidence: 0.6,
    };
  }

  private extractOutlinePattern(): ExtractedPattern {
    const outline = this.meta.stages.outline!;
    const sectionFns = outline.sections.map(s => s.function).filter(Boolean);
    return {
      type: '大纲结构',
      domain: '文章结构',
      trigger: `当撰写"${outline.type}"类文章时`,
      behavior: `结构类型：${outline.type}。段落功能序列：${sectionFns.join(' → ')}。`,
      evidence: `类型=${outline.type}，段落数=${outline.sections.length}`,
      boundary: `适用于：${outline.type}类文章\n不适用于：其他结构类型的文章`,
      confidence: 0.6,
    };
  }

  private extractHookPattern(): ExtractedPattern {
    const hook = this.meta.stages.outline!.hooks[0];
    return {
      type: '钩子公式',
      domain: '文章开头',
      trigger: '当写作公众号开头，需要在第一段建立读者共鸣时',
      behavior: `问题开场：${hook}。第一段指向读者痛点，不超过3句话出现核心词。`,
      evidence: hook,
      boundary: '适用于：观点型/问题解决型文章\n不适用于：故事叙述型/个人感悟型',
      confidence: 0.6,
    };
  }

  private extractAntiAiPattern(): ExtractedPattern {
    const violations = this.meta.stages.polish!.violations;
    return {
      type: '去AI味',
      domain: '语言风格',
      trigger: '当润色文章时检测到 AI 腔时',
      behavior: `需替换的空洞词/句式：${violations.join('、')}。`,
      evidence: violations.join('、'),
      boundary: '适用于：所有公众号文章润色\n不适用于：正式新闻/公文写作',
      confidence: 0.6,
    };
  }

  private extractImagePattern(): ExtractedPattern {
    const img = this.meta.images[0];
    return {
      type: '配图风格',
      domain: '配图',
      trigger: '当需要为文章配图时',
      behavior: `有效图片风格：${img.promptStyle}。`,
      evidence: img.promptStyle,
      boundary: '适用于：公众号封面图/配图\n不适用于：技术示意图/数据图表',
      confidence: 0.6,
    };
  }
}
