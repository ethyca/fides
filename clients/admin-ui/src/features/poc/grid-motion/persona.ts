export type Persona = "executive" | "cpo";

export type View = "trend" | "mosaic";

export const DEFAULT_VIEW_BY_PERSONA: Record<Persona, View> = {
  executive: "trend",
  cpo: "mosaic",
};

export const CURRENT_PERSONA: Persona = "executive";
