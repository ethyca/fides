import { DiscoveryMonitorItem } from "./types/DiscoveryMonitorItem";

interface DiscoveryMonitorItemsTableProps {
  discoveryMonitorItems: DiscoveryMonitorItem[];
  onMute: (urn: string) => void;
  onAccept: (urn: string) => void;
  onReject: (urn: string) => void;
  onMonitor: (urn: string) => void;
  onNavigate: (urn: string) => void;
}

const DiscoveryMonitorItemsTable: React.FC<DiscoveryMonitorItemsTableProps> = ({
  discoveryMonitorItems,
  onAccept,
  onMonitor,
  onMute,
  onReject,
}) => <span>Table</span>;
export default DiscoveryMonitorItemsTable;
