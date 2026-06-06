import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { NewsletterForm } from "@/components/newsletter-form";
import { SectionRenderer } from "@/components/sections";
import { cookies } from "next/headers";
import { getDesign, getPosts, getSite, getDesignPreview, PREVIEW_COOKIE } from "@/lib/api";
import { alternatesFor, loadMessages, normalizeLocale, t } from "@/lib/i18n";

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale: raw } = await params;
  return { alternates: alternatesFor(normalizeLocale(raw), "") };
}

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: raw } = await params;
  const locale = normalizeLocale(raw);
  const site = await getSite();
  const previewIndustry = site.demoPreview ? ((await cookies()).get(PREVIEW_COOKIE)?.value || "") : "";
  const [design, posts, messages] = await Promise.all([
    previewIndustry ? getDesignPreview(previewIndustry, locale) : getDesign(locale),
    getPosts(locale),
    loadMessages(locale)
  ]);
  const featured = posts.slice(0, 3);

  return (
    <main className="main">
      <SectionRenderer sections={design.sections ?? []} site={site} />

      <section className="section">
        <h2>{t(messages, "home.latest")}</h2>
        <div className="grid">
          {featured.length ? (
            featured.map((post) => (
              <Link className="post-card" href={`/${locale}/blog/${post.slug}`} key={post.id}>
                <h3>{post.title}</h3>
                <p>{post.excerpt}</p>
                <span className="button ghost">
                  {t(messages, "home.read")} <ArrowRight size={16} />
                </span>
              </Link>
            ))
          ) : (
            <div className="post-card">
              <h3>{t(messages, "home.noPosts")}</h3>
              <p>{t(messages, "home.noPostsBody")}</p>
            </div>
          )}
        </div>
      </section>

      <section className="section">
        <div className="panel newsletter-panel">
          <div>
            <p className="kicker">{t(messages, "home.newsletterKicker")}</p>
            <h2>{t(messages, "home.newsletterTitle")}</h2>
          </div>
          <NewsletterForm
            labels={{
              placeholder: t(messages, "newsletter.placeholder"),
              button: t(messages, "newsletter.button"),
              subscribing: t(messages, "newsletter.subscribing"),
              subscribed: t(messages, "newsletter.subscribed"),
              failed: t(messages, "newsletter.failed"),
              emailAria: t(messages, "newsletter.emailAria")
            }}
          />
        </div>
      </section>
    </main>
  );
}
