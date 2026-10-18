import { NoteBanner } from "@/components/auth/parts";

import { Panel } from "../panel";
import { CreateInviteForm } from "./create-invite-form";
import { InviteList } from "./invite-list";
import type { InviteView } from "./invite-view";
import { INVITES_GRID } from "./layout";

/**
 * The invites screen under the header: the form for a new link, then every
 * link made so far. Wide screens put them side by side.
 */
export function InvitesScreen({
  invites,
  preview = false,
}: {
  invites: InviteView[];
  /** Supabase isn't connected: sample links, and nothing is saved. */
  preview?: boolean;
}) {
  return (
    <div className={INVITES_GRID}>
      {preview ? (
        <NoteBanner
          className="xl:col-span-2"
          note={{
            tone: "info",
            text: "Sample links. Accounts aren't connected yet, so nothing you create or switch off here is saved.",
          }}
        />
      ) : null}
      <Panel
        id="new-invite"
        title="New link"
        description="Make one per group, so you can tell them apart."
        bodyClassName="p-4 sm:p-5"
      >
        <CreateInviteForm />
      </Panel>
      <InviteList invites={invites} />
    </div>
  );
}
