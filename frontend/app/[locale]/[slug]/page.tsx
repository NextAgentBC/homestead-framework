import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cookies } from "next/headers";
import { getPage, getSite, getPreviewPage, PREVIEW_COOKIE } from "@/lib/api";
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

  // Module-composed page (like the home), or a simple markdown page.
  if (page.sections && page.sections.length > 0) {
    return (
      <main className="main">
        <SectionRenderer sections={page.sections} site={site} />
      </main>
    );
  }

  return (
    <main className="main">
      <article className="article">
        <h1>{page.title}</h1>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{page.bodyMarkdown || ""}</ReactMarkdown>
      </article>
    </main>
  );
}
