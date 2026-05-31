import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { NewsletterForm } from "@/components/newsletter-form";
import { SectionRenderer } from "@/components/sections";
import { getDesign, getPosts, getSite } from "@/lib/api";

export default async function HomePage() {
  const [site, design, posts] = await Promise.all([getSite(), getDesign(), getPosts()]);
  const featured = posts.slice(0, 3);

  return (
    <main className="main">
      <SectionRenderer sections={design.sections ?? []} site={site} />

      <section className="section">
        <h2>Latest</h2>
        <div className="grid">
          {featured.length ? (
            featured.map((post) => (
              <Link className="post-card" href={`/blog/${post.slug}`} key={post.id}>
                <h3>{post.title}</h3>
                <p>{post.excerpt}</p>
                <span className="button ghost">
                  Read <ArrowRight size={16} />
                </span>
              </Link>
            ))
          ) : (
            <div className="post-card">
              <h3>No posts yet</h3>
              <p>New articles will appear here as they are published.</p>
            </div>
          )}
        </div>
      </section>

      <section className="section">
        <div className="panel newsletter-panel">
          <div>
            <p className="kicker">Newsletter</p>
            <h2>Stay in the loop</h2>
          </div>
          <NewsletterForm />
        </div>
      </section>
    </main>
  );
}
