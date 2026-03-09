export const FAKE_DATA_CATEGORIES = [
  { label: "Email address", value: 612 },
  { label: "Name", value: 487 },
  { label: "Phone number", value: 234 },
  { label: "Mailing address", value: 178 },
  { label: "Date of birth", value: 96 },
];

export const FAKE_DATA_USES = [
  { label: "Marketing", value: 423 },
  { label: "Analytics", value: 312 },
  { label: "Operations", value: 189 },
  { label: "Security", value: 134 },
  { label: "HR / Recruiting", value: 78 },
];

export const BRAND_COLORS = [
  "#b9704b", // terracotta
  "#999b83", // olive
  "#cdd2d3", // marble
  "#cecac2", // sandstone
  "#2b2e35", // minos
];

export const computePercent = (value: number, total: number): number =>
  total > 0 ? Math.round((value / total) * 100) : 0;
