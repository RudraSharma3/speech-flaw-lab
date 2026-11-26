import React from 'react';
import { CheckCircle2, CircleAlert, CircleX, Info, TriangleAlert } from 'lucide-react';
import { flawMeta } from '../lib/catalog';

export const Panel: React.FC<{
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  bodyClassName?: string;
  children: React.ReactNode;
}> = ({ title, subtitle, actions, className = '', bodyClassName = 'p-5', children }) => (
  <section className={`min-w-0 rounded-card border border-line bg-surface ${className}`}>
    {(title || actions) && (
      <header className="flex flex-wrap items-start justify-between gap-3 border-b border-line px-5 py-3.5">
        <div className="min-w-0">
          {title && <h2 className="text-[15px] font-semibold text-ink">{title}</h2>}
          {subtitle && <p className="mt-0.5 max-w-[70ch] text-[13px] text-ink-2">{subtitle}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </header>
    )}
    <div className={bodyClassName}>{children}</div>
  </section>
);

export const FlawSwatch: React.FC<{ type: string; size?: number }> = ({ type, size = 10 }) => (
  <span
    aria-hidden
    className="inline-block shrink-0 rounded-[3px]"
    style={{ width: size, height: size, background: flawMeta(type).color }}
  />
);

export const FlawLabel: React.FC<{ type: string; className?: string }> = ({ type, className = '' }) => (
  <span className={`inline-flex items-center gap-1.5 ${className}`}>
    <FlawSwatch type={type} />
    <span>{flawMeta(type).label}</span>
  </span>
);

type Tone = 'good' | 'warn' | 'crit' | 'neutral' | 'info';

const TONE_CLASSES: Record<Tone, string> = {
  good: 'bg-good-soft text-good',
  warn: 'bg-warn-soft text-warn',
  crit: 'bg-crit-soft text-crit',
  neutral: 'bg-surface-2 text-ink-2',
  info: 'bg-accent-soft text-accent',
};

const TONE_ICONS: Record<Tone, React.FC<{ className?: string }>> = {
  good: CheckCircle2,
  warn: TriangleAlert,
  crit: CircleX,
  neutral: CircleAlert,
  info: Info,
};

/** Status always pairs colour with an icon and a word. */
export const StatusBadge: React.FC<{ tone: Tone; children: React.ReactNode; title?: string }> = ({
  tone,
  children,
  title,
}) => {
  const Icon = TONE_ICONS[tone];
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded px-1.5 py-0.5 text-[12px] font-medium ${TONE_CLASSES[tone]}`}
    >
      <Icon className="h-3.5 w-3.5" />
      {children}
    </span>
  );
};

export const Notice: React.FC<{ tone: Tone; title?: string; children: React.ReactNode }> = ({ tone, title, children }) => {
  const Icon = TONE_ICONS[tone];
  return (
    <div className={`flex items-start gap-2.5 rounded-md px-3 py-2.5 text-[13px] ${TONE_CLASSES[tone]}`}>
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="min-w-0 leading-relaxed">
        {title && <span className="font-semibold">{title} </span>}
        <span className="text-ink-2">{children}</span>
      </div>
    </div>
  );
};

export function Segmented<T extends string | number>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: { value: T; label: React.ReactNode; title?: string }[];
  value: T;
  onChange: (v: T) => void;
  ariaLabel: string;
}) {
  return (
    <div role="radiogroup" aria-label={ariaLabel} className="inline-flex flex-wrap gap-0.5 rounded-md border border-line bg-surface-2 p-0.5">
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={String(o.value)}
            role="radio"
            aria-checked={active}
            title={o.title}
            onClick={() => onChange(o.value)}
            className={`rounded-[5px] px-3 py-1.5 text-[13px] font-medium transition-colors ${
              active ? 'bg-surface text-ink shadow-[0_1px_2px_rgba(20,24,30,0.08)]' : 'text-ink-2 hover:text-ink'
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export const Metric: React.FC<{
  label: string;
  value: React.ReactNode;
  unit?: string;
  hint?: React.ReactNode;
}> = ({ label, value, unit, hint }) => (
  <div className="min-w-0">
    <div className="eyebrow">{label}</div>
    <div className="num mt-1 text-[17px] font-medium text-ink">
      {value}
      {unit && <span className="ml-1 text-[13px] font-normal text-ink-3">{unit}</span>}
    </div>
    {hint && <div className="mt-0.5 text-[12px] text-ink-3">{hint}</div>}
  </div>
);
