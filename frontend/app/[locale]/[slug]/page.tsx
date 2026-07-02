import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cookies } from "next/headers";
import { getPage, getSite, getPreviewPage, PREVIEW_COOKIE } from "@/lib/api";
import { breadcrumbJsonLd, faqPageJsonLd, serviceJsonLd, renderJsonLdScripts, type JsonLd } from "@/lib/schema";
import { SectionRenderer } from "@/components/sections";
import { alternatesFor, normalizeLocale } from "@/lib/i18n";

type PageProps = {
  params: Promise<{ slug: string; locale: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug, locale: raw } = await params;
  const locale = normalizeLocale(raw);
  const site = await getSite();
  const previewIndustry = site.demoPreview ? ((await cookies()).get(PREVIEW_COOKIE)?.value || "") : "";
  const page = previewIndustry ? await getPreviewPage(slug, previewIndustry, locale) : await getPage(slug, locale);
  if (!page) return {};
  return {
    title: page.metaTitle || page.title,
    description: page.metaDescription || undefined,
    alternates: alternatesFor(locale, `/${page.slug}`)
  };
}

export default async function ContentPage({ params }: PageProps) {
  const { slug, locale: raw } = await params;
  const locale = normalizeLocale(raw);
  const site = await getSite();
  const previewIndustry = site.demoPreview ? ((await cookies()).get(PREVIEW_COOKIE)?.value || "") : "";
  const page = previewIndustry ? await getPreviewPage(slug, previewIndustry, locale) : await getPage(slug, locale);
  if (!page) notFound();

  // Structured data for the page. Skipped entirely for demo/industry previews —
  // preview pages are template content (and carry no localBusinessOverrides).
  const jsonLdNodes: (JsonLd | null)[] = [];
  if (!previewIndustry) {
    for (const block of (page.sections ?? []).filter((s) => s.type === "faq")) {
      jsonLdNodes.push(faqPageJsonLd(block.content?.items ?? []));
    }
    const overrides = page.localBusinessOverrides;
    // Service node only when the page declares one AND the LocalBusiness node
    // it references by @id exists (i.e. NAP is configured in the layout).
    if (overrides?.service_type && site.nap?.legalName) {
      jsonLdNodes.push(
        serviceJsonLd(site, site.nap, {
          serviceType: overrides.service_type,
          description: page.metaDescription || page.title,
          areaServed: overrides.service_areas,
          url: `${site.url}/${locale}/${page.slug}`
        })
      );
    }
    jsonLdNodes.push(
      breadcrumbJsonLd([
        { name: site.name, url: `${site.url}/${locale}` },
        { name: page.navLabel || page.title, url: `${site.url}/${locale}/${page.slug}` }
      ])
    );
  }
  const jsonLdScripts = renderJsonLdScripts(jsonLdNodes);

  // Module-composed page (like the home), or a simple markdown page.
  if (page.sections && page.sections.length > 0) {
    return (
      <main className="main">
        {jsonLdScripts}
        <SectionRenderer sections={page.sections} site={site} />
      </main>
    );
  }

  return (
    <main className="main">
      {jsonLdScripts}
      <article className="article">
        <h1>{page.title}</h1>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{page.bodyMarkdown || ""}</ReactMarkdown>
      </article>
    </main>
  );
}
