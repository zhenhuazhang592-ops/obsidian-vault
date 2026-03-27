import { useCallback, useRef } from 'react';
import { useStore } from '@/store';
import type { Asset } from '@/types';

interface AssetLibraryProps {
  type: 'character' | 'scene' | 'video';
  title: string;
  prompt?: string;
}

export function AssetLibrary({ type, title, prompt }: AssetLibraryProps) {
  const { assets, addAsset, removeAsset } = useStore();
  const inputRef = useRef<HTMLInputElement>(null);

  const filtered = assets.filter((a) => a.type === type);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files) return;

      Array.from(files).forEach((file) => {
        const reader = new FileReader();
        reader.onload = (ev) => {
          const dataUrl = ev.target?.result as string;
          const asset: Asset = {
            id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
            name: file.name,
            type,
            dataUrl,
            prompt,
            createdAt: Date.now(),
          };
          addAsset(asset);
        };
        reader.readAsDataURL(file);
      });

      // Reset input
      if (inputRef.current) inputRef.current.value = '';
    },
    [type, prompt, addAsset],
  );

  return (
    <div className="asset-library">
      <div className="asset-section-title">{title}</div>
      {filtered.length > 0 ? (
        <div className="asset-grid">
          {filtered.map((asset) => (
            <div key={asset.id} className="asset-thumb">
              <img src={asset.dataUrl} alt={asset.name} />
              <button
                type="button"
                className="asset-thumb-remove"
                onClick={() => removeAsset(asset.id)}
                title="删除"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="asset-empty">暂无资产，点击下方按钮上传</div>
      )}
      <label className="asset-upload-btn" role="button">
        <span>+</span> 上传图片
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </label>
    </div>
  );
}
