/**
 * Output 统一编排
 * 执行顺序：
 * 1. SEO/GEO 优化
 * 2. 配图生成
 * 3. HTML 排版
 * 4. wiki 回流（使用 WikiIngest）
 */

import * as fs from 'fs';
import * as path from 'path';
import { config } from '../config';
import { logger } from '../logger';
import { Stage5Polished } from '../types';
import { SEOGEOptimizer } from './seo-geo';
import { ImageGenerator } from './images';
import { HTMLExporter } from './html';
import { WikiIngest } from '../wiki/ingest';

export interface OutputResult {
  seo: import('../types').SEOResult;
  geo: import('../types').GEOResult;
  coverImage: string;
  inlineImages: string[];
  htmlPath: string;
  wikiCreated: string[];
  wikilinkErrors: import('../wiki/ingest').WikilinkError[];
}

export class OutputPipeline {
  private seoGeo: SEOGEOptimizer;
  private images: ImageGenerator;
  private html: HTMLExporter;
  private wikiIngest: WikiIngest;

  constructor(private outputDir: string) {
    this.seoGeo = new SEOGEOptimizer(outputDir);
    this.images = new ImageGenerator();
    this.html = new HTMLExporter(outputDir);
    this.wikiIngest = new WikiIngest();
  }

  async execute(polished: Stage5Polished): Promise<OutputResult> {
    logger.info('开始 Output 流程...');

    // 1. SEO/GEO
    const [seo, geo] = await Promise.all([
      this.seoGeo.optimizeSEO(polished.content),
      this.seoGeo.optimizeGEO(polished.content),
    ]);
    await this.seoGeo.saveResults(seo, geo);
    logger.success('SEO/GEO 优化完成');

    // 2. 配图
    const coverImage = await this.images.generateCover(polished.title);
    const inlineImages = await this.images.generateInlineImages(polished.content, 3);
    logger.success('配图生成完成');

    // 3. HTML
    const htmlPath = await this.html.export(polished.content, polished.title, coverImage);
    logger.success(`HTML 排版完成: ${htmlPath}`);

    // 4. wiki 回流
    const refinedContent = this.insertImages(polished.content, inlineImages);
    const markdownPath = path.join(this.outputDir, '06-发布稿.md');
    fs.writeFileSync(markdownPath, refinedContent, 'utf-8');

    const ingestResult = await this.wikiIngest.ingestFile(markdownPath);
    logger.success(`wiki 回流完成，创建了 ${ingestResult.created.length} 个页面`);

    if (ingestResult.wikilinkErrors.length > 0) {
      logger.warn(`wiki 回流发现 ${ingestResult.wikilinkErrors.length} 个 wikilink 错误`);
    }

    return {
      seo,
      geo,
      coverImage,
      inlineImages,
      htmlPath,
      wikiCreated: ingestResult.created,
      wikilinkErrors: ingestResult.wikilinkErrors,
    };
  }

  private insertImages(content: string, images: string[]): string {
    let imageIndex = 0;
    return content.replace(/^## (.+)$/gm, (match) => {
      const image = images[imageIndex++];
      if (image) return `${match}\n\n![配图](${image})`;
      return match;
    });
  }
}
