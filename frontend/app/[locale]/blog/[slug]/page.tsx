import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { getPost } from "@/lib/api";
import { renderJsonLdScripts } from "@/lib/schema";
import { alternatesFor, normalizeLocale } from "@/lib/i18n";

type PageProps = {
  params: Promise<{ slug: string; locale: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug, locale: raw } = await params;
  const locale = normalizeLocale(raw);
  const post = await getPost(slug, locale);
  if (!post) return {};
  return {
    title: post.metaTitle || post.title,
    description: post.metaDescription || post.excerpt,
    alternates: alternatesFor(locale, `/blog/${post.slug}`),
    openGraph: {
      title: post.title,
      description: post.excerpt,
      type: "article",
      publishedTime: post.publishedAt || undefined,
      tags: post.tags
    }
  };
}

export default async function BlogDetailPage({ params }: PageProps) {
  const { slug, locale: raw } = await params;
  const locale = normalizeLocale(raw);
  const post = await getPost(slug, locale);
  if (!post) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.excerpt,
    inLanguage: locale,
    datePublished: post.publishedAt,
    author: { "@type": "Person", name: post.author },
    keywords: post.tags.join(", "),
    spatialCoverage: post.geoRegion
  };

  return (
    <main className="main">
      {renderJsonLdScripts([jsonLd])}
      <article className="article">
        <p className="kicker">{post.geoRegion}</p>
        <h1>{post.title}</h1>
        <p className="lede">{post.excerpt}</p>
        <div className="tags">
          {post.tags.map((tag) => (
            <span className="tag" key={tag}>
              {tag}
            </span>
          ))}
        </div>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{post.bodyMarkdown || ""}</ReactMarkdown>
      </article>
    </main>
  );
}
