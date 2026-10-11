import * as React from "react";

import { cn } from "@/lib/utils";
import { fieldControlClass } from "./input";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        fieldControlClass,
        "field-sizing-content min-h-28 px-3.5 py-3 leading-relaxed",
        className,
      )}
      {...props}
    />
  );
}

export { Textarea };
