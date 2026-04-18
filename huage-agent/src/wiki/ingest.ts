import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { config } from '../config';
import { PromptEngine } from '../prompts/shared';
import { WIKI_REFLUX_PROMPT, WIKI_REFLUX_MODEL, WIKI_REFLUX_TEMPERATURE } from '../prompts/wiki-reflux';

const SourceIngestSchema = z.object({
  sourceContent: z.string(),
  slug: z.string(),
  date: z.string(),
  sourceFile: z.string(),
});

const WikiRefluxOutputSchema = z.object({
  sourcePage: z.object({ content: z.string() }),
  entities: z.array(z.object({ name: z.string(), type: z.string(), content: z.string() })),
  concepts: z.array(z.object({ name: z.string(), content: z.string() })),
  newConnections: z.array(z.object({ targetPage: z.string(), relationship: z.string() })),
});

export class WikiIngest {
  async ingestFile(filePath: string): Promise<IngestResult> {
    if (!fs.existsSync(filePath)) throw new Error(`File not found: ${filePath}`);
    const content = fs.readFileSync(filePath, 'utf-8');
    const slug = path.basename(filePath, path.extname(filePath)).toLowerCase().replace(/\s+/g, '-');
    const date = new Date().toISOString().split('T')[0];

    const result = await PromptEngine.callLLM({
      template: WIKI_REFLUX_PROMPT,
      vars: { title: slug, content: content.slice(0, 8000), sources: JSON.stringify([{ title: slug, url: filePath }]) },
      model: WIKI_REFLUX_MODEL,
      temperature: WIKI_REFLUX_TEMPERATURE,
      outputSchema: WikiRefluxOutputSchema,
    });

    const parsed = WikiRefluxOutputSchema.parse(result);
    const wikiDir = config.wikiPath();
    const sourcePath = path.join(wikiDir, `sources/${date}-${slug}.md`);
    fs.mkdirSync(path.dirname(sourcePath), { recursive: true });
    fs.writeFileSync(sourcePath, parsed.sourcePage.content, 'utf-8');
    const created: string[] = [sourcePath];

    for (const entity of parsed.entities) {
      const entityPath = path.join(wikiDir, `entities/${entity.name}.md`);
      fs.mkdirSync(path.dirname(entityPath), { recursive: true });
      fs.writeFileSync(entityPath, entity.content, 'utf-8');
      created.push(entityPath);
    }

    for (const concept of parsed.concepts) {
      const conceptPath = path.join(wikiDir, `concepts/${concept.name}.md`);
      fs.mkdirSync(path.dirname(conceptPath), { recursive: true });
      fs.writeFileSync(conceptPath, concept.content, 'utf-8');
      created.push(conceptPath);
    }

    const wikilinkErrors = this.validateWikilinks(created, wikiDir);
    return { created, wikilinkErrors };
  }

  private validateWikilinks(created: string[], wikiDir: string): WikilinkError[] {
    const errors: WikilinkError[] = [];
    const existingPages = new Set<string>();
    for (const file of this.listMdFiles(wikiDir)) existingPages.add(path.basename(file, '.md'));
    for (const file of created) existingPages.add(path.basename(file, '.md'));
    for (const file of created) {
      const content = fs.readFileSync(file, 'utf-8');
      const links = content.match(/\[\[([^\]|]+)\]\]/g) || [];
      for (const link of links) {
        const target = link.slice(2, -2).split('/').pop() || '';
        if (!existingPages.has(target)) errors.push({ source: path.basename(file, '.md'), target, type: 'broken' });
      }
    }
    return errors;
  }

  private listMdFiles(dir: string): string[] {
    const files: string[] = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) files.push(...this.listMdFiles(full));
      else if (entry.name.endsWith('.md')) files.push(full);
    }
    return files;
  }
}

export interface IngestResult {
  created: string[];
  wikilinkErrors: WikilinkError[];
}

export interface WikilinkError {
  source: string;
  target: string;
  type: 'broken' | 'orphan';
}
