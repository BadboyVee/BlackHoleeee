/** Simple geometric marks for the placeholder brands. Real logos come from the admin. */
function BrandGlyph({ index, className = "size-4" }: { index: number; className?: string }) {
  const shapes = [
    <circle key="c" cx="12" cy="12" r="8" />,
    <path key="t" d="M12 3.5 21 19.5H3Z" />,
    <rect key="d" x="6.5" y="6.5" width="11" height="11" rx="2" transform="rotate(45 12 12)" />,
    <path key="h" d="m12 3 7.8 4.5v9L12 21l-7.8-4.5v-9Z" />,
    <path key="r" d="M12 4a8 8 0 1 1 0 16 8 8 0 0 1 0-16Zm0 4.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" />,
    <path key="b" d="M5 5h5v14H5zM14 5h5v14h-5z" />,
    <path key="p" d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6Z" />,
    <path key="s" d="M12 4a8 8 0 0 1 0 16Z" />,
  ];
  return (
    <svg viewBox="0 0 24 24" aria-hidden className={`${className} shrink-0 fill-current`}>
      {shapes[index % shapes.length]}
    </svg>
  );
}

export { BrandGlyph };
