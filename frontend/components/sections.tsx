import type { ReactNode } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles, Mail, Shield, Gauge, Layers, Zap, BookOpen, Cloud, Image as ImageIcon } from "lucide-react";
import type { Section, SectionCta, Site } from "@/lib/api";

const ICONS: Record<string, typeof Sparkles> = {
  sparkles: Sparkles,
  mail: Mail,
  shield: Shield,
  gauge: Gauge,
  layers: Layers,
  zap: Zap,
  book: BookOpen,
  cloud: Cloud
};

function SectionIcon({ name, color }: { name?: string; color?: string }) {
  const Cmp = (name && ICONS[name]) || Sparkles;
  return <Cmp size={24} strokeWidth={1.8} color={color || "var(--color-primary)"} />;
}

// Image slots ship empty in the industry templates (a student may have no image
// generator). When empty, show a designed placeholder carrying the prompt — the page
// looks intentional and tells you exactly what photo to drop in later.
function PromptHint({ prompt }: { prompt?: string }) {
  if (!prompt?.trim()) return null;
  return (
    <span className="img-prompt-hint">
      <ImageIcon size={13} strokeWidth={1.8} /> {prompt}
    </span>
  );
}

function HeroActions({ cta, secondaryCta }: { cta?: SectionCta; secondaryCta?: SectionCta }) {
  if (!cta?.label && !secondaryCta?.label) return null;
  return (
    <div className="hero-actions">
      {cta?.label && (
        <Link className="button secondary" href={cta.href || "#"}>
          {cta.label} <ArrowRight size={16} />
        </Link>
      )}
      {secondaryCta?.label && (
        <Link className="button ghost" href={secondaryCta.href || "#"}>
          {secondaryCta.label}
        </Link>
      )}
    </div>
  );
}

function SectionHead({ heading, subhead }: { heading?: string; subhead?: string }) {
  if (!heading && !subhead) return null;
  return (
    <div className="section-head">
      {heading && <h2>{heading}</h2>}
      {subhead && <p className="lede">{subhead}</p>}
    </div>
  );
}

function Hero({ section, site }: { section: Section; site: Site }) {
  const c = section.content ?? {};
  const variant = section.variant || "split";
  const image = c.image?.trim() ? c.image : "";
  const focal = c.imageFocal?.trim() ? { objectPosition: c.imageFocal } : undefined;
  const headline = c.headline || site.name;
  const copy = (
    <div className="hero-copy">
      {c.badge ? <span className="hero-badge">{c.badge}</span> : <p className="kicker">{c.kicker || site.industry}</p>}
      <h1>
        {headline}
        {c.headlineAccent && (
          <>
            <br />
            <span className="accent-text">{c.headlineAccent}</span>
          </>
        )}
      </h1>
      {c.subhead && <p className="lede">{c.subhead}</p>}
      <HeroActions cta={c.cta} secondaryCta={c.secondaryCta} />
    </div>
  );

  // split: a real two-column layout (copy beside a portrait image) when an image is set
  if (variant !== "centered" && variant !== "fullbleed") {
    return (
      <section className={`hero hero-split${image ? " hero-split-media" : ""}`}>
        {copy}
        <div className="hero-visual" aria-hidden={image ? undefined : "true"}>
          {image && <img className="hero-side-img" src={image} alt={c.imageAlt || ""} style={focal} />}
        </div>
      </section>
    );
  }

  // centered / fullbleed: full-bleed background photo + token-driven scrim for legibility
  const cls = variant === "fullbleed" ? "hero hero-fullbleed" : "hero hero-centered";
  return (
    <section className={`${cls}${image ? " hero-has-image" : ""}`}>
      {image && (
        <>
          <img className="hero-bg-img" src={image} alt={c.imageAlt || ""} style={focal} />
          <span className="hero-scrim" aria-hidden="true" />
        </>
      )}
      {!image && <PromptHint prompt={c.imagePrompt} />}
      {copy}
    </section>
  );
}

function Stats({ section }: { section: Section }) {
  const items = section.content?.items ?? [];
  if (!items.length) return null;
  return (
    <section className="stats">
      {items.map((item, index) => (
        <div className="stat" key={index}>
          <span className="stat-value">{item.value}</span>
          <span className="stat-label">{item.label}</span>
        </div>
      ))}
    </section>
  );
}

function Logos({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  if (!items.length) return null;
  return (
    <section className="logos">
      {c.heading && <p className="logos-heading">{c.heading}</p>}
      <div className="logos-row">
        {items.map((item, index) => (
          <span className="logo-chip" key={index}>
            {item.label}
          </span>
        ))}
      </div>
    </section>
  );
}

function Features({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  const minimal = section.variant === "minimal";
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className={minimal ? "feature-grid" : "grid"}>
        {items.map((item, index) => (
          <div className={minimal ? "feature" : "post-card"} key={index}>
            <SectionIcon name={item.icon} />
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Problem({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="grid">
        {items.map((item, index) => (
          <div className="post-card problem-card" key={index}>
            <SectionIcon name={item.icon} color="var(--color-accent)" />
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Comparison({ section }: { section: Section }) {
  const c = section.content ?? {};
  const left = c.left ?? {};
  const right = c.right ?? {};
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="compare">
        <div className="compare-col">
          <h3>{left.title}</h3>
          <ul>{(left.items ?? []).map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
        <div className="compare-col featured">
          <h3>{right.title}</h3>
          <ul>{(right.items ?? []).map((t, i) => <li key={i}>{t}</li>)}</ul>
        </div>
      </div>
    </section>
  );
}

function Testimonials({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="grid">
        {items.map((item, index) => (
          <figure className="post-card quote-card" key={index}>
            <blockquote>{item.quote}</blockquote>
            <figcaption>
              <strong>{item.author}</strong>
              {item.role && <span>{item.role}</span>}
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

function Pricing({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="grid">
        {items.map((item, index) => (
          <div className={`post-card price-card${item.featured ? " featured" : ""}`} key={index}>
            <h3>{item.name}</h3>
            <div className="price">
              <span className="price-value">{item.price}</span>
              {item.period && <span className="price-period">{item.period}</span>}
            </div>
            <ul className="price-features">{(item.features ?? []).map((f, i) => <li key={i}>{f}</li>)}</ul>
            {item.cta?.label && (
              <Link className={item.featured ? "button secondary" : "button ghost"} href={item.cta.href || "#"}>
                {item.cta.label}
              </Link>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function Faq({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="faq">
        {items.map((item, index) => (
          <details className="faq-item" key={index}>
            <summary>{item.q}</summary>
            <p>{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}

// --- Flexible "capture" section: a token-driven DSL the agent emits from a
// screenshot. Reads only design tokens, so it auto-harmonizes with the theme.
type FlexItem = NonNullable<NonNullable<Section["content"]>["items"]>[number];

function FlexItemView({ item }: { item: FlexItem }) {
  const kind = item.kind || "feature";
  if (kind === "stat") {
    return (
      <div className="flex-item flex-stat">
        <span className="stat-value">{item.value}</span>
        <span className="stat-label">{item.label}</span>
      </div>
    );
  }
  if (kind === "quote") {
    return (
      <figure className="flex-item quote-card">
        <blockquote>{item.quote}</blockquote>
        <figcaption>
          <strong>{item.author}</strong>
          {item.role && <span>{item.role}</span>}
        </figcaption>
      </figure>
    );
  }
  if (kind === "media") {
    return (
      <div className="flex-item flex-media">
        {item.image ? <img src={item.image} alt={item.title || ""} /> : <div className="flex-media-ph" aria-hidden="true" />}
        {item.title && <h3>{item.title}</h3>}
      </div>
    );
  }
  if (kind === "button") {
    return (
      <Link className="button ghost flex-item-btn" href={item.href || "#"}>
        {item.title || item.label}
      </Link>
    );
  }
  if (kind === "text") {
    return (
      <div className="flex-item flex-text">
        {item.title && <h3>{item.title}</h3>}
        {item.body && <p>{item.body}</p>}
      </div>
    );
  }
  // feature (default) | step — step shows an ordinal via CSS counter
  return (
    <div className={`flex-item ${kind === "step" ? "flex-step" : "flex-feature"}`}>
      {item.icon && <SectionIcon name={item.icon} />}
      {item.title && <h3>{item.title}</h3>}
      {item.body && <p>{item.body}</p>}
    </div>
  );
}

function FlexSection({ section }: { section: Section }) {
  const c = section.content ?? {};
  const layout = c.layout ?? {};
  const variant = section.variant || "grid";
  const tone = layout.tone || "plain";
  const align = layout.align || "left";
  const cols = Math.min(Math.max(Number(layout.columns) || 3, 1), 4);
  const items = c.items ?? [];
  const spread = variant === "stack" || variant === "banner";
  return (
    <section className={`section section-flex flex-${variant} tone-${tone} align-${align}`}>
      {(c.eyebrow || c.heading || c.subhead) && (
        <div className="section-head">
          {c.eyebrow && <p className="kicker">{c.eyebrow}</p>}
          {c.heading && <h2>{c.heading}</h2>}
          {c.subhead && <p className="lede">{c.subhead}</p>}
        </div>
      )}
      {items.length > 0 && (
        <div
          className="flex-items"
          style={spread ? undefined : { gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
        >
          {items.map((item, index) => (
            <FlexItemView key={index} item={item} />
          ))}
        </div>
      )}
      {c.cta?.label && (
        <div className="flex-cta">
          <Link className="button secondary" href={c.cta.href || "#"}>
            {c.cta.label} <ArrowRight size={16} />
          </Link>
        </div>
      )}
    </section>
  );
}

function Cta({ section }: { section: Section }) {
  const c = section.content ?? {};
  const image = c.image?.trim() ? c.image : "";
  return (
    <section className={`cta-banner${image ? " cta-banner-media" : ""}`}>
      {image && (
        <>
          <img className="cta-bg-img" src={image} alt="" />
          <span className="cta-scrim" aria-hidden="true" />
        </>
      )}
      {!image && <PromptHint prompt={c.imagePrompt} />}
      <div className="cta-copy">
        {c.headline && <h2>{c.headline}</h2>}
        {c.subhead && <p className="lede">{c.subhead}</p>}
      </div>
      {c.cta?.label && (
        <Link className="button secondary" href={c.cta.href || "#"}>
          {c.cta.label} <ArrowRight size={16} />
        </Link>
      )}
    </section>
  );
}

function Steps({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <ol className="steps">
        {items.map((item, index) => (
          <li className="step" key={index}>
            <span className="step-num">{index + 1}</span>
            <div className="step-body">
              {item.icon && <SectionIcon name={item.icon} />}
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Gallery({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="gallery">
        {items.map((item, index) => (
          <figure className="gallery-item" key={index}>
            {item.image ? (
              <img src={item.image} alt={item.caption || ""} loading="lazy" />
            ) : (
              <div className="gallery-ph img-ph">
                <ImageIcon size={22} strokeWidth={1.5} aria-hidden="true" />
                {item.imagePrompt && <span className="img-ph-prompt">{item.imagePrompt}</span>}
              </div>
            )}
            {item.caption && <figcaption>{item.caption}</figcaption>}
          </figure>
        ))}
      </div>
    </section>
  );
}

function Team({ section }: { section: Section }) {
  const c = section.content ?? {};
  const items = c.items ?? [];
  return (
    <section className="section">
      <SectionHead heading={c.heading} subhead={c.subhead} />
      <div className="grid">
        {items.map((item, index) => (
          <div className="post-card team-card" key={index}>
            {item.image ? (
              <img className="team-avatar" src={item.image} alt={item.name || ""} loading="lazy" />
            ) : (
              <span className="team-avatar team-initial" aria-hidden="true">
                {(item.name || "?").slice(0, 1)}
              </span>
            )}
            <h3>{item.name}</h3>
            {item.role && <p className="team-role">{item.role}</p>}
            {item.body && <p>{item.body}</p>}
          </div>
        ))}
      </div>
    </section>
  );
}

function Banner({ section }: { section: Section }) {
  const c = section.content ?? {};
  const tint = section.variant === "tint";
  return (
    <section className={`banner${tint ? " banner-tint" : ""}`}>
      <span className="banner-msg">
        {c.icon && <SectionIcon name={c.icon} />}
        {c.text}
      </span>
      {c.cta?.label && (
        <Link className="button ghost" href={c.cta.href || "#"}>
          {c.cta.label} <ArrowRight size={16} />
        </Link>
      )}
    </section>
  );
}

const RENDERERS: Record<string, (s: Section, site: Site) => ReactNode> = {
  hero: (s, site) => <Hero section={s} site={site} />,
  stats: (s) => <Stats section={s} />,
  logos: (s) => <Logos section={s} />,
  features: (s) => <Features section={s} />,
  problem: (s) => <Problem section={s} />,
  comparison: (s) => <Comparison section={s} />,
  testimonials: (s) => <Testimonials section={s} />,
  pricing: (s) => <Pricing section={s} />,
  faq: (s) => <Faq section={s} />,
  cta: (s) => <Cta section={s} />,
  section: (s) => <FlexSection section={s} />,
  steps: (s) => <Steps section={s} />,
  gallery: (s) => <Gallery section={s} />,
  team: (s) => <Team section={s} />,
  banner: (s) => <Banner section={s} />
};

export function SectionRenderer({ sections, site }: { sections: Section[]; site: Site }) {
  return (
    <>
      {sections.map((section, index) => {
        const render = RENDERERS[section.type];
        return render ? <div key={index}>{render(section, site)}</div> : null;
      })}
    </>
  );
}
