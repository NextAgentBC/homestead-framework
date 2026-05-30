import type { CSSProperties } from "react";
import type { DesignProfile } from "./api";

type DesignVariables = CSSProperties & Record<`--${string}`, string>;

export function designCssVariables(design: DesignProfile): DesignVariables {
  const colors = design.tokens.colors;
  const typography = design.tokens.typography;
  const radius = design.tokens.radius;
  const layout = design.tokens.layout;

  return {
    "--color-ink": colors.ink,
    "--color-muted": colors.muted,
    "--color-paper": colors.paper,
    "--color-surface": colors.surface,
    "--color-line": colors.line,
    "--color-primary": colors.primary,
    "--color-accent": colors.accent,
    "--color-highlight": colors.highlight,
    "--color-link": colors.link,
    "--font-body": typography.body,
    "--font-heading": typography.heading,
    "--font-mono": typography.mono,
    "--radius-card": radius.card,
    "--radius-control": radius.control,
    "--radius-pill": radius.pill,
    "--layout-content-max": layout.contentMaxWidth,
    "--layout-hero-min": layout.heroMinHeight,
    "--layout-card-padding": layout.cardPadding,
    "--layout-section-gap": layout.sectionGap
  };
}

