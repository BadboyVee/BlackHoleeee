import { Reveal } from "@/components/motion/reveal";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { faqs } from "@/lib/marketing-content";
import { ChatFaq } from "./chat-faq";
import { SectionShell, SectionTitle } from "./shared";

/**
 * Questions and answers. Agent turns them into a chat with Echo; the other
 * looks use an accordion (bold and editorial, or chunky color blocks).
 */
function FaqSection() {
  return (
    <SectionShell id="faq" label="FAQ">
      <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)] lg:gap-20">
        <SectionTitle
          title="Questions, answered."
          lead="Anything else? Book a campaign and we'll walk you through it on a call."
        />
        <div className="look-agent">
          <Reveal className="min-w-0">
            <ChatFaq faqs={faqs} />
          </Reveal>
        </div>
        <div className="look-renaissance">
          <Reveal className="min-w-0">
            <Accordion type="single" collapsible className="border-t border-border-strong">
              {faqs.map((faq) => (
                <AccordionItem key={faq.question} value={faq.question} className="border-border-strong">
                  <AccordionTrigger className="py-6 text-[clamp(1.125rem,1rem+0.5vw,1.5rem)] leading-tight font-bold tracking-[-0.035em] hover:text-brand-text sm:text-[clamp(1.125rem,1rem+0.5vw,1.5rem)]">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-[16px]">{faq.answer}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Reveal>
        </div>
        <div className="look-drop">
          <Reveal className="min-w-0">
            <Accordion type="single" collapsible className="flex flex-col gap-2.5">
              {faqs.map((faq) => (
                <AccordionItem
                  key={faq.question}
                  value={faq.question}
                  className="rounded-[1.5rem] border-0 bg-surface-2 px-5 transition-colors duration-300 ease-snap data-[state=open]:bg-block-1 data-[state=open]:text-white sm:px-6 [&[data-state=open]_[data-slot=accordion-content]>div]:text-white/90"
                >
                  <AccordionTrigger className="text-[17px] font-bold tracking-[-0.02em] sm:text-[19px] group-data-[state=open]:text-white">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-[16px]">{faq.answer}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Reveal>
        </div>
      </div>
    </SectionShell>
  );
}

export { FaqSection };
