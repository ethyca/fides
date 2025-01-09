import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Box,
  Text,
} from "fidesui";

import { useAppSelector } from "~/app/hooks";
import ConnectedCircle from "~/features/common/ConnectedCircle";
import { useFeatures } from "~/features/common/features";
import { DataFlowScannerLogo } from "~/features/common/Icon";
import { selectDataFlowScannerStatus } from "~/features/plus/plus.slice";
import { ClusterHealth } from "~/types/api";

interface SystemOptionProps extends ButtonProps {
  label: string;
  description: string;
  icon: React.ReactElement;
  onClick: () => void;
}

const SystemOption = ({
  label,
  description,
  icon,
  onClick,
  ...buttonProps
}: SystemOptionProps) => (
  <Button
    type="text"
    onClick={onClick}
    className="h-full min-h-[116px] rounded-lg border border-gray-300 p-4"
    {...buttonProps}
  >
    <Box
      as="span"
      display="flex"
      flexDirection="column"
      alignItems="start"
      justifyContent="space-between"
      height="100%"
      width="100%"
      whiteSpace="break-spaces"
      textAlign="left"
    >
      <Box as="span" display="flex" alignItems="center" mb={2}>
        {icon}
        <Text fontWeight="semibold" color="gray.900" as="span" ml={3}>
          {label}
        </Text>
      </Box>
      <Text color="gray.700" as="span" fontWeight="medium">
        {description}
      </Text>
    </Box>
  </Button>
);

/**
 * Wrapper around SystemOption which handles data flow scanner specific
 * logic, such as cluster health
 * @param param0
 * @returns
 */
export const DataFlowScannerOption = ({ onClick }: { onClick: () => void }) => {
  const { plus, dataFlowScanning } = useFeatures();
  const scannerStatus = useAppSelector(selectDataFlowScannerStatus);

  const clusterHealth = scannerStatus?.cluster_health ?? "unknown";
  const isClusterHealthy = clusterHealth === ClusterHealth.HEALTHY;

  // If Plus is not enabled, do not show this feature at all
  if (!plus) {
    return null;
  }

  let tooltip = "";
  if (!dataFlowScanning) {
    tooltip =
      "The data flow scanner is not enabled, please check your configuration.";
  } else if (!isClusterHealthy) {
    tooltip = `Your cluster appears not to be healthy. Its status is ${clusterHealth}.`;
  }

  const disabled = !dataFlowScanning || !isClusterHealthy;

  return (
    <Box position="relative">
      <SystemOption
        label="Data flow scan"
        description="Automatically discover new systems in your Kubernetes infrastructure"
        icon={<DataFlowScannerLogo boxSize={8} />}
        onClick={onClick}
        disabled={disabled}
        title={disabled ? tooltip : undefined}
        data-testid="data-flow-scan-btn"
      />
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

export default SystemOption;
