import { config } from '../config';
import { logger } from '../logger';

export class ImageGenerator {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = config.arkApiKey;
    this.baseUrl = config.arkBaseUrl;
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
    if (!this.apiKey) {
      logger.warn('ARK_API_KEY 未配置，使用占位图');
      return `https://placeholder.com/image-${Date.now()}.png`;
    }

    const url = `${this.baseUrl}/api/v3/images/generations`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        model: 'doubao-seedream-4-5-251128',
        prompt,
        response_format: 'url',
        size: '1920x1920',
        stream: false,
        watermark: false,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      logger.warn(`Seedream API 错误 ${response.status}: ${err.slice(0, 100)}`);
      return `https://placeholder.com/image-${Date.now()}.png`;
    }

    const data = await response.json() as {
      data?: Array<{ url?: string }>;
    };

    const imageUrl = data?.data?.[0]?.url;
    if (imageUrl) {
      logger.success(`配图生成成功: ${imageUrl.slice(0, 60)}...`);
      return imageUrl;
    }

    logger.warn('Seedream 返回格式异常，使用占位图');
    return `https://placeholder.com/image-${Date.now()}.png`;
  }
}
