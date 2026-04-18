import { config } from '../config';
import { logger } from '../logger';

export class ImageGenerator {
  private apiKey: string;

  constructor() {
    this.apiKey = config.arkApiKey;
  }

  async generateCover(title: string, style: string = '简洁大气'): Promise<string> {
    logger.info('生成封面图...');
    const prompt = `公众号封面图，主题：${title}，风格：${style}，文字清晰`;
    return this.callSeedream(prompt);
  }

  async generateInlineImages(content: string, count: number = 3): Promise<string[]> {
    logger.info(`生成 ${count} 张文中配图...`);
    const images: string[] = [];
    for (let i = 0; i < count; i++) {
      const prompt = `配图 ${i + 1}：${content.slice(i * 200, i * 200 + 200)}`;
      images.push(await this.callSeedream(prompt));
    }
    return images;
  }

  private async callSeedream(prompt: string): Promise<string> {
    // TODO: 实现 Doubao-Seedream-4.5 API 调用（待 Task 11 CLI 入口接入）
    return `https://placeholder.com/image-${Date.now()}.png`;
  }
}
