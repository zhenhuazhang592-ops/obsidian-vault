interface TagsProps {
  options: string[];
  selected: string;
  onChange: (value: string) => void;
}

export function Tags({ options, selected, onChange }: TagsProps) {
  return (
    <div className="tags-container">
      {options.map((o) => {
        const on = selected === o;
        return (
          <button
            key={o}
            type="button"
            className={`tag-btn ${on ? 'tag-btn--active' : ''}`}
            onClick={() => onChange(o)}
          >
            {o}
          </button>
        );
      })}
    </div>
  );
}
