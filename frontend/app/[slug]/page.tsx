import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { getPage, getSite } from "@/lib/api";
import { SectionRenderer } from "@/components/sections";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = await getPage(slug);
  if (!page) return {};
  return {
    title: page.metaTitle || page.title,
    description: page.metaDescription || undefined,
    alternates: { canonical: page.canonicalUrl || `/${page.slug}` }
  };
}

export default async function ContentPage({ params }: PageProps) {
  const { slug } = await params;
  const page = await getPage(slug);
  if (!page) notFound();

  // Module-composed page (like the home), or a simple markdown page.
  if (page.sections && page.sections.length > 0) {
    const site = await getSite();
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
        <ReactMarkdown>{page.bodyMarkdown || ""}</ReactMarkdown>
      </article>
    </main>
  );
}
