interface GenerateBtnProps {
  onClick: () => void;
  loading: boolean;
  label?: string;
}

export function GenerateBtn({ onClick, loading, label = '✨ 自动生成' }: GenerateBtnProps) {
  return (
    <button
      type="button"
      className="generate-btn"
      onClick={onClick}
      disabled={loading}
    >
      {loading ? '⏳ 正在连接 AI 大脑...' : label}
    </button>
  );
}
