import { pageNote, type PageNote } from "./messages";
import { safeNextPath } from "./routes";

type SearchParams = Record<string, string | string[] | undefined>;

/** One value of a query parameter: the first when it's repeated, null when it's missing. */
export function firstParam(params: SearchParams, name: string): string | null {
  const value = params[name];
  return (Array.isArray(value) ? value[0] : value) ?? null;
}

/** What a sign-in page needs from its URL: where to go next (checked) and a note to show. */
export function authPageParams(params: SearchParams, contactEmail: string): { next: string | null; note: PageNote | null } {
  return {
    next: safeNextPath(firstParam(params, "next")),
    note: pageNote({ status: firstParam(params, "status"), error: firstParam(params, "error") }, contactEmail),
  };
}
