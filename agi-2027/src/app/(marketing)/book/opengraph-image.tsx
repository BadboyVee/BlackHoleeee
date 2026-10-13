import { dropImage, OgBookingForm } from "@/lib/og/drop-image";

/* The /book link preview: the booking form in front of "Let's go". */

export const alt = "Book a campaign with AGI 2027: the booking form in front of the words Let's go.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return dropImage({
    word: "Let's go",
    kicker: "For brands",
    line: "Tell us what you're launching and when.",
    cta: "Book a campaign",
    children: <OgBookingForm />,
  });
}
