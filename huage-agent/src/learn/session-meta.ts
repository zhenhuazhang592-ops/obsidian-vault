/**
 * 从 stage JSON 文件构建 session-meta.json
 * 设计：读取 outputDir 下所有 stage confirmed JSON，
 *       构建统一的 session-meta 对象供 extractor 使用。
 */

import * as fs from 'fs';
import * as path from 'path';
import { SessionMeta } from './types.js';

export class SessionMetaBuilder {
  private meta: SessionMeta;

  constructor(private outputDir: string) {
    this.meta = {
      topic: '',
      date: new Date().toISOString().split('T')[0],
      outputDir,
      stages: {
        topic: null,
        thesis: null,
        outline: null,
        writing: null,
        polish: null,
      },
      wikiInjected: [],
      images: [],
    };
  }

  async build(): Promise<void> {
    await this.loadTopic();
    await this.loadThesis();
    await this.loadOutline();
    await this.loadWriting();
    await this.loadPolish();
  }

  private async loadTopic(): Promise<void> {
    const file = path.join(this.outputDir, 'stage1-confirmed.json');
    if (!fs.existsSync(file)) return;
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
      this.meta.topic = data.selectedTitle ?? data.title ?? '';
      this.meta.stages.topic = {
        selected: data.selectedTitle ?? '',
        alternatives: (data.options ?? []).map((o: any) => o.title),
        reason: data.reasoning ?? '',
        targetReader: data.targetReader ?? '',
        painPoint: data.painPoint ?? '',
      };
    } catch {
      // skip corrupt file
    }
  }

  private async loadThesis(): Promise<void> {
    const file = path.join(this.outputDir, 'stage2-confirmed.json');
    if (!fs.existsSync(file)) return;
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
      const points = (data.supportingPoints ?? []).map((p: any) => ({
        text: p.point ?? '',
        type: (p.type ?? 'insight') as 'insight' | 'story' | 'data',
      }));
      this.meta.stages.thesis = { points };
    } catch {
      // skip
    }
  }

  private async loadOutline(): Promise<void> {
    const file = path.join(this.outputDir, 'stage3-confirmed.json');
    if (!fs.existsSync(file)) return;
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
      const sections = (data.sections ?? []).map((s: any) => ({
        heading: s.heading ?? '',
        function: s.framework ?? s.function ?? '',
      }));
      this.meta.stages.outline = {
        type: this.inferOutlineType(data),
        hooks: data.opening?.hook ? [data.opening.hook] : [],
        sections,
        opening: data.opening?.hook ?? '',
      };
    } catch {
      // skip
    }
  }

  private inferOutlineType(data: any): string {
    const heading = ((data.sections ?? [])[0]?.heading ?? '').toLowerCase();
    if (heading.includes('背景') || heading.includes('问题')) return '问题-方案式';
    if (heading.includes('故事') || heading.includes('经历')) return '故事线';
    if (heading.includes('对比') || heading.includes('比较')) return '对比式';
    return '通用结构';
  }

  private async loadWriting(): Promise<void> {
    const stage4File = path.join(this.outputDir, 'stage4-writing.json');
    const stage5File = path.join(this.outputDir, 'stage5-confirmed.json');
    let wordCount = 0;

    if (fs.existsSync(stage4File)) {
      try {
        const d = JSON.parse(fs.readFileSync(stage4File, 'utf-8'));
        wordCount = d.result?.wordCount ?? 0;
      } catch { /* skip */ }
    }
    if (fs.existsSync(stage5File)) {
      try {
        const d = JSON.parse(fs.readFileSync(stage5File, 'utf-8'));
        wordCount = Math.max(wordCount, d.wordCount ?? 0);
      } catch { /* skip */ }
    }

    if (wordCount > 0) {
      this.meta.stages.writing = { wordCount };
    }
  }

  private async loadPolish(): Promise<void> {
    const file = path.join(this.outputDir, 'stage5-confirmed.json');
    if (!fs.existsSync(file)) return;
    try {
      const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
      const violations = data.antiAiCheck?.violations ?? [];
      const antiAiScore = Math.max(0, 100 - violations.length * 12);
      this.meta.stages.polish = {
        antiAiScore,
        violations,
        seoKeywords: data.seoOptimization?.keywords ?? [],
        geoScore: data.geoOptimization?.aiReadableScore ?? 0,
      };
    } catch {
      // skip
    }
  }

  getMeta(): SessionMeta {
    return this.meta;
  }

  async save(): Promise<void> {
    const file = path.join(this.outputDir, 'session-meta.json');
    fs.writeFileSync(file, JSON.stringify(this.meta, null, 2), 'utf-8');
  }
}
