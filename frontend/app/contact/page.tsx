import type { Metadata } from "next";
import { ContactForm } from "./ui";

export const metadata: Metadata = {
  title: "Contact",
  description: "Get in touch — questions, ideas, or work together."
};

export default function ContactPage() {
  return (
    <main className="main">
      <header className="page-header">
        <p className="kicker">Contact</p>
        <h1>Get in touch</h1>
        <p className="lede">Questions, ideas, or want to work together? Send a message and we&apos;ll get back to you.</p>
      </header>
      <div className="contact-layout">
        <div className="panel">
          <ContactForm />
        </div>
        <aside className="contact-aside">
          <div className="contact-point">
            <h3>Response time</h3>
            <p className="muted">We usually reply within a day or two.</p>
          </div>
          <div className="contact-point">
            <h3>Newsletter</h3>
            <p className="muted">Prefer updates? Subscribe from the home page.</p>
          </div>
          <div className="contact-point">
            <h3>Blog</h3>
            <p className="muted">
              Read the latest on the <a href="/blog">blog</a>.
            </p>
          </div>
        </aside>
      </div>
    </main>
  );
}
