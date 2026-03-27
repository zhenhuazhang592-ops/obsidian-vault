import { useState, useCallback } from 'react';

interface OutputBoxProps {
  content: string;
  loading: boolean;
}

export function OutputBox({ content, loading }: OutputBoxProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    if (!content) return;
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [content]);

  if (!content && !loading) return null;

  return (
    <div className="output-box">
      <div className="output-header">
        <div className={`output-status ${loading ? 'output-status--loading' : 'output-status--done'}`}>
          {loading ? '⏳ 实时生成中...' : '✅ 生成完成'}
        </div>
        {!loading && content && (
          <button
            type="button"
            className={`copy-btn ${copied ? 'copy-btn--copied' : ''}`}
            onClick={handleCopy}
          >
            {copied ? '已复制 ✔' : '📋 复制全部'}
          </button>
        )}
      </div>
      <pre className="output-content">
        {content}
        {loading && <span className="cursor-blink">▊</span>}
      </pre>
    </div>
  );
}
