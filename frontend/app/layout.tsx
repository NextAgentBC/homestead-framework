import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { AuthProvider } from "./providers";
import { getDesign, getSite } from "@/lib/api";
import { designCssVariables } from "@/lib/design";

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
  const [site, design] = await Promise.all([getSite(), getDesign()]);
  return (
    <html lang="en">
      <body style={designCssVariables(design)}>
        <AuthProvider>
          <div className="shell">
            <header className="topbar">
              <Link className="brand" href="/">
                <span className="mark" />
                <span>{site.name}</span>
              </Link>
              <nav className="nav" aria-label="Main navigation">
                <Link href="/blog">Blog</Link>
                <Link href="/contact">Contact</Link>
              </nav>
            </header>
            {children}
            <footer className="footer">Built for Oracle VM, Cloudflare, Flask, Next.js, and maintainable AI workflows.</footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
