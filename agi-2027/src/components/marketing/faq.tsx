import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { faqs } from "@/lib/marketing-content";
import { Section, SectionHeader } from "./section";

function Faq() {
  return (
    <Section id="faq">
      <div className="grid gap-12 lg:grid-cols-[1fr_1.35fr] lg:gap-20">
        <SectionHeader
          kicker="FAQ"
          title="Questions, *answered*."
          description="Anything else? Book a campaign and we'll walk you through it on a call."
        />
        <Accordion type="single" collapsible className="border-t">
          {faqs.map((faq) => (
            <AccordionItem key={faq.question} value={faq.question}>
              <AccordionTrigger>{faq.question}</AccordionTrigger>
              <AccordionContent>{faq.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </Section>
  );
}

export { Faq };
