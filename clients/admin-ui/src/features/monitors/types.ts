import { PaginatedResponse } from "~/types/common/PaginationQueryParams";

// temporary artisanal types

export interface MonitorTemplateUpdate {
  id: string;
  name: string;
  rules: Array<string>[];
}

export interface MonitorTemplateResponse {
  id: string;
  name: string;
  regexMap: Array<string>[];
}

export interface MonitorTemplateFormValues {
  name: string;
  rules: {
    regex: string;
    dataCategory: string;
  }[];
}

export interface MonitorTemplateListItem {
  id: string;
  name: string;
  regexCount: string;
}

export interface MonitorTemplateListResponse
  extends PaginatedResponse<MonitorTemplateListItem> {}
