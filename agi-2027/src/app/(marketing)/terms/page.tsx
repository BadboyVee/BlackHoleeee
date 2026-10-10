import type { Metadata } from "next";
import { FileText } from "lucide-react";

import { ComingSoon } from "@/components/layout/coming-soon";
import { PageHeader } from "@/components/layout/page-header";

export const metadata: Metadata = {
  title: "Terms",
  description: "The terms for brands and creators using AGI 2027.",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
      <PageHeader title="Terms" description="The terms for brands and creators using AGI 2027." />
      <ComingSoon
        icon={FileText}
        title="Terms are being written"
        description="The full terms for brands and creators will be published here."
        milestone={2}
      />
    </div>
  );
}
