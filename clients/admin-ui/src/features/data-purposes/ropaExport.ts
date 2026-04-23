import type { DataPurpose, PurposeSummary } from "./data-purpose.slice";

const ROPA_HEADER = [
  "Reference",
  "Processing activity",
  "Description",
  "Purpose of processing",
  "Lawful basis (Art. 6)",
  "Special category basis (Art. 9)",
  "Categories of data subjects",
  "Categories of personal data",
  "Categories of personal data (detected)",
  "Retention period (days)",
  "Features",
  "Last reviewed",
];

const escapeCell = (value: unknown): string =>
  `"${String(value ?? "").replace(/"/g, '""')}"`;

export const downloadRoPA = (
  purposes: DataPurpose[],
  summaries: PurposeSummary[],
): void => {
  const summariesByKey = new Map(summaries.map((s) => [s.fides_key, s]));
  const rows = purposes.map((p) => [
    p.fides_key,
    p.name,
    p.description ?? "",
    p.data_use,
    p.legal_basis_for_processing ?? "",
    p.special_category_legal_basis ?? "",
    p.data_subject ?? "",
    (p.data_categories ?? []).join("; "),
    (summariesByKey.get(p.fides_key)?.detected_data_categories ?? []).join(
      "; ",
    ),
    p.retention_period ?? "",
    (p.features ?? []).join("; "),
    p.updated_at ?? "",
  ]);
  const csvBody = [ROPA_HEADER, ...rows]
    .map((r) => r.map(escapeCell).join(","))
    .join("\r\n");
  const csv = `\ufeff${csvBody}`;
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "ropa.csv";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(url), 100);
};
