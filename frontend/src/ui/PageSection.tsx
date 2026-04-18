import type { ReactNode } from "react";

type PageSectionProps = {
  title: string;
  description: string;
  children: ReactNode;
};

export function PageSection({ title, description, children }: PageSectionProps) {
  return (
    <section className="page-section">
      <header className="page-header">
        <div>
          <p className="eyebrow">Workbench</p>
          <h2>{title}</h2>
        </div>
        <p className="section-description">{description}</p>
      </header>
      {children}
    </section>
  );
}
