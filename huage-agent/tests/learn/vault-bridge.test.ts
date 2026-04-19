import { VaultBridge } from '../../src/learn/vault-bridge';
import { ExtractedPattern } from '../../src/learn/types';
import * as fs from 'fs';
import * as path from 'path';
import { vi } from 'vitest';

const makePattern = (): ExtractedPattern => ({
  type: '钩子公式',
  domain: '文章开头',
  trigger: '当写作开头时',
  behavior: '用问题开场',
  evidence: '你身边有多少人...',
  boundary: '适用于：观点型',
  confidence: 0.6,
});

describe('VaultBridge', () => {
  const testInstinctDir = '/tmp/huage-learn-vault-test';
  const testSkillDir = '/tmp/huage-learn-skills-test';

  beforeAll(() => {
    fs.mkdirSync(testInstinctDir, { recursive: true });
    fs.mkdirSync(testSkillDir, { recursive: true });
  });

  afterAll(() => {
    fs.rmSync(testInstinctDir, { recursive: true });
    fs.rmSync(testSkillDir, { recursive: true });
  });

  describe('writeVaultInstinct', () => {
    it('should write instinct yaml to vault directory', async () => {
      const bridge = new VaultBridge({ vaultInstinctDir: testInstinctDir });
      const pattern = makePattern();
      await bridge.writeVaultInstinct(pattern, '2026-04-20');
      const files = fs.readdirSync(testInstinctDir).filter(f => f.endsWith('.yaml'));
      expect(files.length).toBe(1);
      expect(files[0]).toContain('钩子公式');
    });

    it('should set correct frontmatter fields', async () => {
      const bridge = new VaultBridge({ vaultInstinctDir: testInstinctDir });
      const pattern = makePattern();
      await bridge.writeVaultInstinct(pattern, '2026-04-20');
      const content = fs.readFileSync(
        path.join(testInstinctDir, fs.readdirSync(testInstinctDir)[0]),
        'utf-8'
      );
      expect(content).toContain('confidence: 0.6');
      expect(content).toContain('domain: 文章开头');
      expect(content).toContain('scope: huage-agent');
    });
  });

  describe('triggerSkillEvolution', () => {
    it('should call python with spawn', async () => {
      const spawnCalls: any[] = [];
      const mockSpawn = vi.fn((cmd: string, args: string[]) => {
        spawnCalls.push({ cmd, args });
        return {
          on: (event: string, cb: (code: number) => void) => {
            if (event === 'close') setTimeout(() => cb(0), 10);
          },
        };
      });

      const bridge = new VaultBridge({
        vaultInstinctDir: testInstinctDir,
        skillsDir: testSkillDir,
        spawn: mockSpawn as any,
      });

      const patterns = [makePattern()];
      patterns[0].confidence = 0.9;
      await bridge.triggerSkillEvolution(patterns);

      await new Promise(r => setTimeout(r, 50));
      expect(spawnCalls.length).toBeGreaterThan(0);
      expect(spawnCalls[0].cmd).toBe('python3');
    });

    it('should not throw when python spawn fails', async () => {
      const mockSpawn = vi.fn(() => ({
        on: (event: string, cb: (code: number) => void) => {
          if (event === 'close') setTimeout(() => cb(1), 10);
        },
      }));

      const bridge = new VaultBridge({
        vaultInstinctDir: testInstinctDir,
        skillsDir: testSkillDir,
        spawn: mockSpawn as any,
      });

      const patterns = [makePattern()];
      patterns[0].confidence = 0.9;
      await expect(bridge.triggerSkillEvolution(patterns)).resolves.not.toThrow();
    });
  });
});
