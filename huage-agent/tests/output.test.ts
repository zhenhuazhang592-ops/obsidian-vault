import { describe, it, expect, beforeAll } from 'vitest';
import { SEOGEOptimizer } from '../src/output/seo-geo';
import { HTMLExporter } from '../src/output/html';
import { ImageGenerator } from '../src/output/images';
import * as fs from 'fs';
import * as path from 'path';

const TEST_DIR = '/tmp/huage-agent-output-test';

beforeAll(() => {
  fs.mkdirSync(TEST_DIR, { recursive: true });
});

describe('SEOGEOptimizer', () => {
  it('should extract keywords from Chinese content', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const content = '时间管理是一个重要的话题。时间管理的技巧包括番茄工作法。';
    const seo = await optimizer.optimizeSEO(content);
    expect(seo.keywords.length).toBeGreaterThan(0);
    expect(seo.keywords).toContain('时间管理');
    expect(seo.metaDescription.length).toBeLessThanOrEqual(163);
  });

  it('should extract English keywords', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const content = 'Productivity and time management are important skills for modern workers.';
    const seo = await optimizer.optimizeSEO(content);
    expect(seo.keywords.length).toBeGreaterThan(0);
  });

  it('should check keyword density is in range [0.5, 3]', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const content = '时间管理时间管理时间管理时间管理时间管理'; // density very high
    const seo = await optimizer.optimizeSEO(content);
    expect(seo.densityCheck).toBe(false); // too high
  });

  it('should extract citations with curly quotes', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const content = '> "这是一句引用" — 作者名';
    const geo = await optimizer.optimizeGEO(content);
    expect(geo.citations.length).toBeGreaterThan(0);
    expect(geo.citations[0]).toContain('这是一句引用');
  });

  it('should return empty citations when none present', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const content = '这是一段普通文字，没有引用。';
    const geo = await optimizer.optimizeGEO(content);
    expect(geo.citations).toEqual([]);
  });

  it('should return 80 for AI readable score (placeholder)', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const geo = await optimizer.optimizeGEO('测试内容');
    expect(geo.aiReadableScore).toBe(80);
  });

  it('should save results to file', async () => {
    const optimizer = new SEOGEOptimizer(TEST_DIR);
    const seo = await optimizer.optimizeSEO('时间管理');
    const geo = await optimizer.optimizeGEO('时间管理');
    await optimizer.saveResults(seo, geo);
    const filePath = path.join(TEST_DIR, 'seo-geo-optimization.json');
    expect(fs.existsSync(filePath)).toBe(true);
    const saved = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    expect(saved.seo).toBeDefined();
    expect(saved.geo).toBeDefined();
  });
});

describe('HTMLExporter', () => {
  it('should export markdown to HTML', async () => {
    const exporter = new HTMLExporter(TEST_DIR);
    const markdown = '# Hello\n\nThis is a test.';
    const htmlPath = await exporter.export(markdown, 'Test Title');
    expect(fs.existsSync(htmlPath)).toBe(true);
    const html = fs.readFileSync(htmlPath, 'utf-8');
    expect(html).toContain('<h1>Hello</h1>');
    expect(html).toContain('Test Title');
    expect(html).toContain('<p>');
  });

  it('should include cover image when provided', async () => {
    const exporter = new HTMLExporter(TEST_DIR);
    const markdown = '# Test';
    const htmlPath = await exporter.export(markdown, 'Test', 'https://example.com/cover.jpg');
    const html = fs.readFileSync(htmlPath, 'utf-8');
    expect(html).toContain('https://example.com/cover.jpg');
    expect(html).toContain('alt="封面图"');
  });

  it('should handle bold and italic markdown', async () => {
    const exporter = new HTMLExporter(TEST_DIR);
    const markdown = 'This is **bold** and *italic*.';
    const htmlPath = await exporter.export(markdown, 'Test');
    const html = fs.readFileSync(htmlPath, 'utf-8');
    expect(html).toContain('<strong>bold</strong>');
    expect(html).toContain('<em>italic</em>');
  });

  it('should handle blockquote markdown', async () => {
    const exporter = new HTMLExporter(TEST_DIR);
    const markdown = '> 这是一段引用';
    const htmlPath = await exporter.export(markdown, 'Test');
    const html = fs.readFileSync(htmlPath, 'utf-8');
    expect(html).toContain('<blockquote>这是一段引用</blockquote>');
  });
});

describe('ImageGenerator', () => {
  it('should generate cover image (placeholder)', async () => {
    const generator = new ImageGenerator();
    const url = await generator.generateCover('测试标题');
    expect(url).toContain('placeholder.com');
    expect(url).toContain('image-');
  });

  it('should generate inline images (placeholder)', async () => {
    const generator = new ImageGenerator();
    const urls = await generator.generateInlineImages('配图内容段落一，配图内容段落二，配图内容段落三', 3);
    expect(urls.length).toBe(3);
    urls.forEach((url) => expect(url).toContain('placeholder.com'));
  });

  it('should generate correct number of inline images', async () => {
    const generator = new ImageGenerator();
    const urls = await generator.generateInlineImages('内容', 5);
    expect(urls.length).toBe(5);
  });
});
