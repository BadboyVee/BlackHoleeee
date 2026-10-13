import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { siteConfig } from "@/lib/site";

/** A button that opens an email to the agency, or nothing when no address is set. */
function EmailUs({ label, subject }: { label: string; subject: string }) {
  const email = siteConfig.contactEmail.trim();
  if (!email) return null;
  return (
    <Button asChild size="lg">
      <a href={`mailto:${email}?subject=${encodeURIComponent(subject)}`}>
        <Mail />
        {label}
      </a>
    </Button>
  );
}

export { EmailUs };
