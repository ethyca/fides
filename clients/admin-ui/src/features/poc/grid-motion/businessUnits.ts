export interface BusinessUnit {
  id: string;
  name: string;
  region: string;
}

export const BUSINESS_UNITS: BusinessUnit[] = [
  { id: "global", name: "Acme Global", region: "Worldwide" },
  { id: "emea", name: "Acme EMEA", region: "Europe, Middle East & Africa" },
  { id: "amer", name: "Acme Americas", region: "North & South America" },
  { id: "apac", name: "Acme APAC", region: "Asia Pacific" },
];

export const DEFAULT_BUSINESS_UNIT_ID = "global";
