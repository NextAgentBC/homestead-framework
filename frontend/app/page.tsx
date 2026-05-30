import Link from "next/link";
import { ArrowRight, BookOpen, Cloud, Mail } from "lucide-react";
import { GoogleLoginBox } from "@/components/google-login";
import { NewsletterForm } from "@/components/newsletter-form";
import { getPosts, getSite } from "@/lib/api";

export default async function HomePage() {
  const [site, posts] = await Promise.all([getSite(), getPosts()]);
  const featured = posts.slice(0, 3);

  return (
    <main className="main">
      <section className="hero">
        <div>
          <p className="kicker">{site.industry} publishing system</p>
          <h1>{site.name}</h1>
          <p className="lede">
            A deployable website framework for students: Next.js on the front, Flask API on the back, Google login,
            newsletter email, daily AI blogs, and SEO/GEO-ready pages.
          </p>
        </div>
        <div className="stack">
          <GoogleLoginBox />
          <div className="panel stack">
            <div className="kicker">Newsletter</div>
            <NewsletterForm />
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Operating Model</h2>
        <div className="grid">
          <div className="post-card">
            <Cloud color="var(--color-primary)" />
            <h3>Cloudflare edge</h3>
            <p>Use Tunnel first: public domain, private origin, simple TLS, fewer firewall lessons on day one.</p>
          </div>
          <div className="post-card">
            <BookOpen color="var(--color-accent)" />
            <h3>Daily publishing</h3>
            <p>DeepSeek generates structured drafts or published posts through a Flask CLI and systemd timer.</p>
          </div>
          <div className="post-card">
            <Mail color="var(--color-link)" />
            <h3>User relationship</h3>
            <p>Google Sign-In creates accounts; newsletter subscriptions let the site email readers responsibly.</p>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Latest Blogs</h2>
        <div className="grid">
          {featured.length ? (
            featured.map((post) => (
              <Link className="post-card" href={`/blog/${post.slug}`} key={post.id}>
                <h3>{post.title}</h3>
                <p>{post.excerpt}</p>
                <span className="button">
                  Read <ArrowRight size={16} />
                </span>
              </Link>
            ))
          ) : (
            <div className="post-card">
              <h3>No posts yet</h3>
              <p>Run the daily blog command from the backend to create the first article.</p>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
