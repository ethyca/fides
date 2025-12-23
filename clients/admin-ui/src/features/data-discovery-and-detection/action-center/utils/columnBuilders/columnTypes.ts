import { ActionCenterTabHash } from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterTabs";
import {
  ConsentAlertInfo,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

export interface ColumnBuilderParams {
  monitorId: string;
  readonly: boolean;
  allowIgnore?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  consentStatus?: ConsentAlertInfo;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
  isDataUsesExpanded: boolean;
  isLocationsExpanded: boolean;
  isDomainsExpanded: boolean;
  dataUsesVersion: number;
  locationsVersion: number;
  domainsVersion: number;
  setIsDataUsesExpanded: (value: boolean) => void;
  setIsLocationsExpanded: (value: boolean) => void;
  setIsDomainsExpanded: (value: boolean) => void;
  setDataUsesVersion: (fn: (prev: number) => number) => void;
  setLocationsVersion: (fn: (prev: number) => number) => void;
  setDomainsVersion: (fn: (prev: number) => number) => void;
}
