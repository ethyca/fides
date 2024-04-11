export interface DiscoveryMonitorItem {
  urn: string;
  name: string;
  description?: string;
  modified?: string;
  parent?: DiscoveryMonitorItem;
  children?: DiscoveryMonitorItem[];
}
