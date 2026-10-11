import type { Metadata } from "next";

import { CreatorNotifications } from "@/components/creator/notifications";

export const metadata: Metadata = { title: "Notifications" };

export default function CreatorNotificationsPage() {
  return <CreatorNotifications />;
}
