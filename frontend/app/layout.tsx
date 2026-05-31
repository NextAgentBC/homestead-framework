import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "./providers";
import { getDesign, getSite, getPages } from "@/lib/api";
import { designCssVariables } from "@/lib/design";
import { SiteNav } from "@/components/nav";

// Content (pages, blog, nav) is DB-driven and must reflect changes immediately,
// so render dynamically per request instead of statically prerendering at build.
// This also keeps the build from prerendering routes that fetch the API.
export const dynamic = "force-dynamic";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });

export async function generateMetadata(): Promise<Metadata> {
  const site = await getSite();
  const article = /^[aeiou]/i.test(site.industry) ? "an" : "a";
  return {
    title: {
      default: site.name,
      template: `%s | ${site.name}`
    },
    description: `${article[0].toUpperCase()}${article.slice(1)} ${site.industry} website framework with daily blogs, newsletter, Google login, SEO, and GEO.`,
    metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || site.url),
    openGraph: {
      title: site.name,
      description: `Daily ${site.industry} insights for ${site.audience}.`,
      url: site.url,
      siteName: site.name,
      type: "website"
    }
  };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const [site, design, pages] = await Promise.all([getSite(), getDesign(), getPages()]);
  const navPages = pages.filter((page) => page.showInNav).map((page) => ({ slug: page.slug, navLabel: page.navLabel }));
  return (
    <html lang="en" className={inter.variable}>
      <body style={designCssVariables(design)}>
        <AuthProvider>
          <div className="shell">
            <SiteNav siteName={site.name} pages={navPages} />
            {children}
            <footer className="footer">Built for Oracle VM, Cloudflare, Flask, Next.js, and maintainable AI workflows.</footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
