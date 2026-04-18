import { WikiQuery } from './query';
import { WikiIngest } from './ingest';
import { WikiLint, LintResult } from './lint';
import { WikiGraphBuilder, WikiGraph } from './graph';

export class WikiManager {
  private query: WikiQuery;
  private ingest: WikiIngest;
  private _lint: WikiLint;
  private graph: WikiGraphBuilder;

  constructor() {
    this.query = new WikiQuery();
    this.ingest = new WikiIngest();
    this._lint = new WikiLint();
    this.graph = new WikiGraphBuilder();
  }

  async search(keyword: string) { return this.query.search(keyword); }
  async ingestSource(filePath: string) { return this.ingest.ingestFile(filePath); }
  async lint(): Promise<LintResult> { return this._lint.lint(); }
  async buildGraph(): Promise<WikiGraph> { return this.graph.build(); }
  async loadGraph(): Promise<WikiGraph | null> { return this.graph.loadLatest(); }
}
