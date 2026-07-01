import type { MetadataRoute } from "next";
import { getPages, getPosts, getSite } from "@/lib/api";
import { LOCALES } from "@/lib/i18n";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = await getSite();
  const base = (process.env.NEXT_PUBLIC_SITE_URL || site.url).replace(/\/$/, "");
  const locales = site.locales?.length ? site.locales : LOCALES;
  const entries: MetadataRoute.Sitemap = [];
  for (const locale of locales) {
    entries.push({ url: `${base}/${locale}`, changeFrequency: "daily", priority: 1 });
    entries.push({ url: `${base}/${locale}/blog`, changeFrequency: "daily", priority: 0.8 });
    const posts = await getPosts(locale);
    for (const post of posts) {
      entries.push({
        url: `${base}/${locale}/blog/${post.slug}`,
        lastModified: post.publishedAt || new Date().toISOString(),
        changeFrequency: "monthly" as const,
        priority: 0.7
      });
    }
    // Content pages. GET /api/pages only returns status="published" rows (the
    // backend filters in routes/public.py), so no draft URL can leak here.
    const pages = await getPages(locale);
    for (const page of pages) {
      entries.push({
        url: `${base}/${locale}/${page.slug}`,
        lastModified: page.publishedAt || new Date().toISOString(),
        changeFrequency: "monthly" as const,
        priority: 0.7
      });
    }
  }
  return entries;
}
