// llms.txt is a community convention (llmstxt.org) — a plain-text site summary
// for LLM crawlers. Major engines haven't confirmed consuming it yet, but it is
// zero-cost to serve alongside sitemap.xml / robots.txt.
import { getPages, getSite } from "@/lib/api";

// Content is DB-driven; render per request instead of freezing it at build time
// (matches the layout's force-dynamic rationale).
export const dynamic = "force-dynamic";

export async function GET() {
  const site = await getSite();
  const pages = await getPages(site.defaultLocale);
  const base = (process.env.NEXT_PUBLIC_SITE_URL || site.url).replace(/\/$/, "");
  const tagline = [site.industry, site.region].filter(Boolean).join(" · ");
  const lines = [
    `# ${site.name}`,
    "",
    `> ${tagline ? `${site.name} — ${tagline}.` : site.name}`,
    "",
    "## Pages",
    ...pages.map((page) => `- [${page.navLabel || page.title}](${base}/${site.defaultLocale}/${page.slug})`)
  ];
  return new Response(lines.join("\n") + "\n", {
    headers: { "Content-Type": "text/plain; charset=utf-8" }
  });
}
