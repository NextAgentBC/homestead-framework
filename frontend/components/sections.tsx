import Link from "next/link";
import { ArrowRight, Sparkles, Mail, Shield, Gauge, Layers, Zap, BookOpen, Cloud } from "lucide-react";
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

function SectionIcon({ name }: { name?: string }) {
  const Cmp = (name && ICONS[name]) || Sparkles;
  return <Cmp size={24} strokeWidth={1.8} color="var(--color-primary)" />;
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

function Hero({ section, site }: { section: Section; site: Site }) {
  const c = section.content ?? {};
  const variant = section.variant || "split";
  const headline = c.headline || site.name;
  const copy = (
    <div className="hero-copy">
      {c.badge ? <span className="hero-badge">{c.badge}</span> : c.kicker ? <p className="kicker">{c.kicker}</p> : <p className="kicker">{site.industry}</p>}
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
  if (variant === "centered") return <section className="hero hero-centered">{copy}</section>;
  if (variant === "fullbleed") return <section className="hero hero-fullbleed">{copy}</section>;
  return (
    <section className="hero hero-split">
      {copy}
      <div className="hero-visual" aria-hidden="true" />
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
      {c.heading && <h2>{c.heading}</h2>}
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

function Cta({ section }: { section: Section }) {
  const c = section.content ?? {};
  return (
    <section className="cta-banner">
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

export function SectionRenderer({ sections, site }: { sections: Section[]; site: Site }) {
  return (
    <>
      {sections.map((section, index) => {
        if (section.type === "hero") return <Hero section={section} site={site} key={index} />;
        if (section.type === "stats") return <Stats section={section} key={index} />;
        if (section.type === "logos") return <Logos section={section} key={index} />;
        if (section.type === "features") return <Features section={section} key={index} />;
        if (section.type === "cta") return <Cta section={section} key={index} />;
        return null;
      })}
    </>
  );
}
