import { dropImage, OgLaunchPost } from "@/lib/og/drop-image";

/* The site's default link preview. X and other sites reuse it as the Twitter card image. */

export const alt = "AGI 2027, creator marketing for AI launches: a launch post in front of the word Launch.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return dropImage({
    word: "Launch",
    kicker: "For AI launches",
    line: "Your launch, posted by the creators your users already follow.",
    cta: "Book a campaign",
    children: <OgLaunchPost />,
  });
}
