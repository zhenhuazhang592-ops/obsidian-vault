/**
 * Dan Koe 方法论有效性验证
 *
 * 验证指标：
 * 1. 去 AI 味评分（目标 > 70）
 * 2. 选题多样性（目标 > 3 个不同领域）
 * 3. 读者反馈评分（待接入）
 *
 * 触发条件：完成 3 篇文章后自动运行
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../src/config';

interface ValidationResult {
  articleCount: number;
  avgWordCount: number;
  antiAiScore: number;
  topicVariety: number;
  recommendation: 'continue' | 'adjust' | 'pivot';
  nextSteps: string[];
}

export class DanKoeValidator {
  async validate(): Promise<ValidationResult> {
    const articles = this.loadArticles();

    if (articles.length < 3) {
      return {
        articleCount: articles.length,
        avgWordCount: 0,
        antiAiScore: 0,
        topicVariety: 0,
        recommendation: 'continue',
        nextSteps: ['继续完成至少 3 篇文章'],
      };
    }

    const avgWordCount = this.calcAvgWordCount(articles);
    const antiAiScore = await this.calcAntiAiScore(articles);
    const topicVariety = this.calcTopicVariety(articles);

    let recommendation: ValidationResult['recommendation'] = 'continue';
    const nextSteps: string[] = [];

    if (antiAiScore < 50) {
      recommendation = 'adjust';
      nextSteps.push('加强去 AI 味处理');
    }

    if (topicVariety < 0.3) {
      recommendation = 'adjust';
      nextSteps.push('扩展选题多样性');
    }

    if (recommendation === 'continue' && antiAiScore >= 70) {
      nextSteps.push('Dan Koe 方法论有效，继续沿用');
    }

    await this.writeReport({
      articleCount: articles.length,
      avgWordCount,
      antiAiScore,
      topicVariety,
      recommendation,
      nextSteps,
    });

    return {
      articleCount: articles.length,
      avgWordCount,
      antiAiScore,
      topicVariety,
      recommendation,
      nextSteps,
    };
  }

  private loadArticles(): string[] {
    const outputDir = config.outputPath();
    const articles: string[] = [];
    if (!fs.existsSync(outputDir)) return articles;

    for (const dateDir of fs.readdirSync(outputDir)) {
      const datePath = path.join(outputDir, dateDir);
      if (!fs.statSync(datePath).isDirectory()) continue;
      for (const articleDir of fs.readdirSync(datePath)) {
        const polished = path.join(datePath, articleDir, '05-润色稿.md');
        if (fs.existsSync(polished)) {
          articles.push(fs.readFileSync(polished, 'utf-8'));
        }
      }
    }
    return articles;
  }

  private calcAvgWordCount(articles: string[]): number {
    if (!articles.length) return 0;
    return Math.round(articles.reduce((s, a) => s + a.length, 0) / articles.length);
  }

  /**
   * 去 AI 味评分
   * - 句子平均长度 > 50 → -5（AI 句偏长）
   * - 文章不含"你" → -5（缺少对话感）
   * - 文章不含"？" → -3（缺少互动）
   * 基础分 70
   */
  private async calcAntiAiScore(articles: string[]): Promise<number> {
    let score = 70;
    for (const article of articles) {
      const sentences = article.split(/[.。!！?？]/);
      const avgLen = sentences.reduce((s, sen) => s + sen.length, 0) / (sentences.length || 1);
      if (avgLen > 50) score -= 5;
      if (!article.includes('你')) score -= 5;
      if (!article.includes('？')) score -= 3;
    }
    return Math.max(0, score);
  }

  private calcTopicVariety(articles: string[]): number {
    const topics = new Set<string>();
    for (const article of articles) {
      const match = article.match(/^#\s+(.+)$/m);
      if (match) topics.add(match[1].split(/\s+/)[0]);
    }
    return topics.size / articles.length;
  }

  private async writeReport(result: ValidationResult): Promise<void> {
    const reportPath = path.join(config.outputPath(), 'dan-koe-validation-report.md');
    const content = `# Dan Koe 方法论验证报告

生成时间：${new Date().toISOString()}

## 指标

- 文章数量：${result.articleCount}
- 平均字数：${result.avgWordCount}
- 去 AI 味评分：${result.antiAiScore}/100
- 选题多样性：${(result.topicVariety * 100).toFixed(0)}%

## 建议

**${result.recommendation === 'continue' ? '继续沿用' : result.recommendation === 'adjust' ? '调整优化' : '考虑转型'}**

${result.nextSteps.map((s) => `- ${s}`).join('\n')}`;

    fs.writeFileSync(reportPath, content, 'utf-8');
  }
}

if (require.main === module) {
  new DanKoeValidator().validate().then((r) => {
    console.log(JSON.stringify(r, null, 2));
    process.exit(r.recommendation === 'pivot' ? 1 : 0);
  });
}
