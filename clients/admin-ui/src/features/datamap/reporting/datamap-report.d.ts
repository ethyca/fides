import { CustomField, DatamapReport } from "~/types/api";

// Extend the base datamap report type to also have custom fields
export type DatamapReportWithCustomFields = DatamapReport &
  Record<string, CustomField["value"]>;
