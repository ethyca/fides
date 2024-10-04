import { DATAMAP_GROUPING } from "~/types/api";

export type Link = {
  source: string;
  target: string;
};

export type SpatialData = {
  links: Link[];
  nodes: SystemNode[];
};

export type SystemNode = {
  ingress: string[];
  egress: string[];
  description: string;
  id: string;
  name: string;
};

export type SetSelectedSystemId = {
  setSelectedSystemId: (id: string) => void;
};

export type DatamapReportFilterSelections = {
  dataUses: string[];
  dataSubjects: string[];
  dataCategories: string[];
};

export interface CustomReportTableState {
  groupBy?: DATAMAP_GROUPING;
  filters?: DatamapReportFilterSelections;
  columnOrder?: string[];
  columnVisibility?: Record<string, boolean>;
}
