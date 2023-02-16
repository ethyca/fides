import { narrow } from "narrow-minded";

export const hasId = <I>(item: I): item is I & { id: string } =>
  narrow({ id: "string" }, item);

export const filterWithId = <I>(items?: I[]) => (items ?? []).filter(hasId);
