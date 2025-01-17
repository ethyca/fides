import { AntTooltip as Tooltip, Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { useAppSelector } from "~/app/hooks";
import ConnectedCircle from "~/features/common/ConnectedCircle";
import { useFeatures } from "~/features/common/features";
import { DataFlowScannerLogo } from "~/features/common/Icon";
import { selectDataFlowScannerStatus } from "~/features/plus/plus.slice";
import { ClusterHealth } from "~/types/api";

import CalloutNavCard from "../common/CalloutNavCard";

/**
 * Wrapper around CalloutNavCard which handles data flow scanner specific
 * logic, such as cluster health
 * @param param0
 * @returns
 */
const DataFlowScannerOption = ({ onClick }: { onClick: () => void }) => {
  const { plus, dataFlowScanning } = useFeatures();
  const scannerStatus = useAppSelector(selectDataFlowScannerStatus);

  const clusterHealth = scannerStatus?.cluster_health ?? "unknown";
  const isClusterHealthy = clusterHealth === ClusterHealth.HEALTHY;

  // If Plus is not enabled, do not show this feature at all
  if (!plus) {
    return null;
  }

  let tooltip = null;
  if (!dataFlowScanning) {
    tooltip =
      "The data flow scanner is not enabled, please check your configuration.";
  } else if (!isClusterHealthy) {
    tooltip = `Your cluster appears not to be healthy. Its status is ${clusterHealth}.`;
  }

  const disabled = !dataFlowScanning || !isClusterHealthy;

  return (
    <Box position="relative">
      <Tooltip title={tooltip} popupVisible={!!tooltip}>
        <button
          disabled={disabled}
          type="button"
          aria-label="Data flow scan"
          className="text-left"
          onClick={onClick}
        >
          <CalloutNavCard
            title="Data flow scan"
            color={palette.FIDESUI_NECTAR}
            description="Automatically discover new systems in your Kubernetes infrastructure"
            icon={<DataFlowScannerLogo boxSize={8} />}
            data-testid="data-flow-scan-btn"
          />
        </button>
      </Tooltip>
      {dataFlowScanning ? (
        <ConnectedCircle
          connected={isClusterHealthy}
          title={
            isClusterHealthy
              ? "Cluster is connected and healthy"
              : `Cluster is ${clusterHealth}`
          }
          position="absolute"
          right={-1}
          top={-1}
          data-testid="cluster-health-indicator"
        />
      ) : null}
    </Box>
  );
};

export default DataFlowScannerOption;
