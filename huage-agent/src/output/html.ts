import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../logger';

export class HTMLExporter {
  constructor(private outputDir: string) {}

  async export(markdown: string, title: string, coverImage?: string): Promise<string> {
    logger.info('生成 HTML 排版...');
    const html = this.markdownToHTML(markdown, title, coverImage);
    const filePath = path.join(this.outputDir, 'index.html');
    fs.writeFileSync(filePath, html, 'utf-8');
    logger.success(`HTML 已保存: ${filePath}`);
    return filePath;
  }

  private markdownToHTML(markdown: string, title: string, coverImage?: string): string {
    let body = markdown
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/!\[(.+?)\]\((.+?)\)/g, '<img src="$2" alt="$1">');

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    body { max-width: 677px; margin: 0 auto; padding: 20px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      line-height: 1.75; color: #333; }
    h1 { font-size: 24px; margin: 24px 0 16px; }
    h2 { font-size: 20px; margin: 20px 0 12px; }
    h3 { font-size: 18px; margin: 16px 0 10px; }
    p { margin: 12px 0; }
    blockquote { border-left: 3px solid #ddbb88; padding: 8px 16px;
      margin: 16px 0; background: #f9f6f0; color: #555; }
    img { max-width: 100%; height: auto; margin: 16px 0; }
    strong { color: #000; }
    em { font-style: italic; }
  </style>
</head>
<body>
  ${coverImage ? `<img src="${coverImage}" alt="封面图" style="max-width:100%">` : ''}
  <p>${body}</p>
</body>
</html>`;
  }
}
