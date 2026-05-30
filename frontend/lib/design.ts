import type { CSSProperties } from "react";
import { fallbackDesign, type DesignProfile } from "./api";

type DesignVariables = CSSProperties & Record<`--${string}`, string>;

export function designCssVariables(design: DesignProfile): DesignVariables {
  const tokens = {
    colors: { ...fallbackDesign.tokens.colors, ...(design.tokens?.colors || {}) },
    typography: { ...fallbackDesign.tokens.typography, ...(design.tokens?.typography || {}) },
    radius: { ...fallbackDesign.tokens.radius, ...(design.tokens?.radius || {}) },
    layout: { ...fallbackDesign.tokens.layout, ...(design.tokens?.layout || {}) }
  };
  const colors = tokens.colors;
  const typography = tokens.typography;
  const radius = tokens.radius;
  const layout = tokens.layout;

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
