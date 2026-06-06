import type { Metadata } from "next";
import Link from "next/link";
import { Inter, Space_Grotesk, Spectral, Fraunces, Oswald } from "next/font/google";
import "../globals.css";
import { AuthProvider } from "../providers";
import { cookies } from "next/headers";
import { getDesign, getSite, getPages, getDesignPreview, getIndustries, PREVIEW_COOKIE } from "@/lib/api";
import { designCssVariables } from "@/lib/design";
import { SiteNav } from "@/components/nav";
import { ChatWidget } from "@/components/chat-widget";
import { PreviewBanner } from "@/components/preview-banner";
import { loadMessages, normalizeLocale, LOCALES, t } from "@/lib/i18n";
import type { DesignProfile } from "@/lib/api";

// Content (pages, blog, nav) is DB-driven and must reflect changes immediately,
// so render dynamically per request instead of statically prerendering at build.
export const dynamic = "force-dynamic";

// A small font palette loaded once; templates pick which face to use through
// their typography tokens (e.g. heading: "var(--font-display), serif").
const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const grotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-grotesk", display: "swap", weight: ["400", "500", "600", "700"] });
const serif = Spectral({ subsets: ["latin"], variable: "--font-display", display: "swap", weight: ["400", "500", "600", "700"] });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-fraunces", display: "swap", weight: ["400", "500", "600", "700"] });
const oswald = Oswald({ subsets: ["latin"], variable: "--font-condensed", display: "swap", weight: ["400", "500", "600", "700"] });
const fontVars = `${inter.variable} ${grotesk.variable} ${serif.variable} ${fraunces.variable} ${oswald.variable}`;

function hexLuminance(hex?: string): number | null {
  if (!hex) return null;
  let h = hex.trim().replace("#", "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  if (h.length !== 6) return null;
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  if ([r, g, b].some((v) => Number.isNaN(v))) return null;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function deriveMode(design: DesignProfile): "light" | "dark" {
  const lum = hexLuminance(design.tokens?.colors?.paper);
  return lum !== null && lum < 0.4 ? "dark" : "light";
}
function deriveThemeFamily(design: DesignProfile): string {
  const src = design.source || "";
  const prefix = "style-preset:";
  if (src.startsWith(prefix)) return src.slice(prefix.length);
  return (design.industry || "default").toLowerCase();
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params;
  const site = await getSite();
  const tagline = [site.industry, site.region].filter(Boolean).join(" · ");
  const description = tagline ? `${site.name} — ${tagline}.` : site.name;
  return {
    title: { default: site.name, template: `%s | ${site.name}` },
    description,
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || site.url),
    openGraph: { title: site.name, description, url: `${site.url}/${locale}`, siteName: site.name, type: "website" }
  };
}

export default async function LocaleLayout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  const locale = normalizeLocale(raw);
  const site = await getSite();
  // Per-visitor industry preview (cookie-scoped, never persisted). When set and the
  // demo is enabled, render that industry's template instead of the real design.
  const previewIndustry = site.demoPreview ? ((await cookies()).get(PREVIEW_COOKIE)?.value || "") : "";
  const [design, pages, messages, industries] = await Promise.all([
    previewIndustry ? getDesignPreview(previewIndustry, locale) : getDesign(locale),
    getPages(locale),
    loadMessages(locale),
    site.demoPreview ? getIndustries() : Promise.resolve([])
  ]);
  const navPages = pages.filter((page) => page.showInNav).map((page) => ({ slug: page.slug, navLabel: page.navLabel }));
  const localeList = site.locales?.length ? site.locales : LOCALES;
  return (
    <html
      lang={locale}
      data-mode={deriveMode(design)}
      data-theme={deriveThemeFamily(design)}
      className={fontVars}
      // Tokens must live on :root (<html>) — the derived vars (--page-bg, --tint,
      // shadows…) are declared in :root and resolve their nested var(--color-*)
      // against this element, not <body>. On <body> the dark templates' page
      // background would fall back to the light :root default.
      style={designCssVariables(design)}
    >
      <body>
        <AuthProvider>
          <div className="shell">
            {previewIndustry && <PreviewBanner label={design.name} messages={messages} />}
            <SiteNav siteName={site.name} pages={navPages} locale={locale} locales={localeList} messages={messages} />
            {children}
            <footer className="footer">
              <div className="footer-grid">
                <div className="footer-brand">
                  <span className="footer-brand-row">
                    <span className="mark" />
                    <strong>{site.name}</strong>
                  </span>
                  <p className="muted">{t(messages, "footer.tagline", { industry: site.industry })}</p>
                </div>
                <nav className="footer-col" aria-label={t(messages, "footer.pages")}>
                  <h4>{t(messages, "footer.pages")}</h4>
                  {navPages.map((page) => (
                    <Link href={`/${locale}/${page.slug}`} key={page.slug}>
                      {page.navLabel}
                    </Link>
                  ))}
                </nav>
                <nav className="footer-col" aria-label={t(messages, "footer.more")}>
                  <h4>{t(messages, "footer.more")}</h4>
                  <Link href={`/${locale}/blog`}>{t(messages, "footer.blog")}</Link>
                  <Link href={`/${locale}/contact`}>{t(messages, "footer.contact")}</Link>
                </nav>
              </div>
              <div className="footer-bottom">© {new Date().getFullYear()} {site.name}</div>
            </footer>
            <ChatWidget
              locale={locale}
              messages={messages}
              assistantName={site.assistantName}
              demoPreview={!!site.demoPreview}
              industries={industries}
              previewing={!!previewIndustry}
            />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
