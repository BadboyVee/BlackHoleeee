import { FadeIn } from './Reveal'

/** The small "(01) — About" marker at the top of each section. */
export function SectionLabel({ index, title, className = '' }: { index: string; title: string; className?: string }) {
  return (
    <FadeIn className={`label flex items-center gap-3 ${className}`} y={16}>
      <span className="text-ember">({index})</span>
      <span className="inline-block h-px w-8 bg-current opacity-40" />
      <span>{title}</span>
    </FadeIn>
  )
}
