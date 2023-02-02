import {
  Box,
  Heading,
  HStack,
  IconButton,
  QuestionIcon,
  Stack,
  Text,
  Tooltip,
} from "@fidesui/react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ConnectedCircle from "~/features/common/ConnectedCircle";
import { useFeatures } from "~/features/common/features";
import {
  AWSLogoIcon,
  DataFlowScannerLogo,
  ManualSetupIcon,
  OktaLogoIcon,
} from "~/features/common/Icon";
import { selectDataFlowScannerStatus } from "~/features/plus/plus.slice";
import { ClusterHealth, ValidTargets } from "~/types/api";

import { changeStep, setAddSystemsMethod } from "./config-wizard.slice";
import { iconButtonSize } from "./constants";
import { SystemMethods } from "./types";

const DataFlowScannerOption = ({ onClick }: { onClick: () => void }) => {
  const { plus, dataFlowScanning } = useFeatures();
  const scannerStatus = useAppSelector(selectDataFlowScannerStatus);

  const clusterHealth = scannerStatus?.cluster_health ?? "unknown";
  const isClusterHealthy = clusterHealth === ClusterHealth.HEALTHY;

  // If Plus is not enabled, do not show this feature at all
  if (!plus) {
    return null;
  }

  let tooltip =
    "The scanner will connect to your infrastructure to automatically scan and create a list of all systems available.";
  if (!dataFlowScanning) {
    tooltip =
      "The data flow scanner is not enabled, please check your configuration.";
  } else if (!isClusterHealthy) {
    tooltip = `Your cluster appears not to be healthy. Its status is ${clusterHealth}.`;
  }

  const disabled = !dataFlowScanning || !isClusterHealthy;

  return (
    <Stack direction="row" display="flex" alignItems="center">
      <HStack position="relative">
        <IconButton
          aria-label="Data flow scan"
          boxSize={iconButtonSize}
          minW={iconButtonSize}
          boxShadow="base"
          variant="ghost"
          icon={<DataFlowScannerLogo boxSize="10" />}
          onClick={onClick}
          data-testid="data-flow-scan-btn"
          disabled={disabled}
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
            left={iconButtonSize - 12}
            top={-1}
            data-testid="cluster-health-indicator"
          />
        ) : null}
      </HStack>
      <Text>Data Flow Scan</Text>
      <Tooltip fontSize="md" label={tooltip} placement="right">
        <QuestionIcon boxSize={5} color="gray.400" />
      </Tooltip>
    </Stack>
  );
};

const SectionTitle = ({ children }: { children: string }) => (
  <Heading
    as="h4"
    size="xs"
    fontWeight="semibold"
    color="gray.600"
    textTransform="uppercase"
    mb={4}
  >
    {children}
  </Heading>
);

const AddSystem = () => {
  const dispatch = useAppDispatch();

  return (
    <Stack spacing={10} data-testid="add-systems">
      <Stack spacing={6} w={{ base: "100%", md: "50%" }}>
        <Heading as="h3" size="lg" fontWeight="semibold">
          Fides helps you map your systems to manage your privacy
        </Heading>
        <Text>
          In Fides, systems describe any services that store or process data for
          your organization, including third-party APIs, web applications,
          databases, and data warehouses.
        </Text>

        <Text>
          Fides can automatically discover new systems in your AWS
          infrastructure or Okta accounts. For services not covered by the
          automated scanners or analog processes, you may also manually add new
          systems to your map.
        </Text>
      </Stack>
      <Box data-testid="manual-options">
        <SectionTitle>Manually add systems</SectionTitle>
        <HStack>
          <HStack>
            <IconButton
              aria-label="Manual setup"
              boxSize={iconButtonSize}
              minW={iconButtonSize}
              boxShadow="base"
              variant="ghost"
              icon={<ManualSetupIcon boxSize="full" />}
              onClick={() => {
                dispatch(changeStep(5));
                dispatch(setAddSystemsMethod(SystemMethods.MANUAL));
              }}
              data-testid="manual-btn"
            />
          </HStack>
          <Text>Add a system manually</Text>
          <Tooltip
            fontSize="md"
            label="If you prefer to, you can add systems manually by entering information about them directly."
            placement="right"
          >
            <QuestionIcon boxSize={5} color="gray.400" />
          </Tooltip>
        </HStack>
      </Box>

      <Box data-testid="automated-options">
        <SectionTitle>Automated infrastructure scanning</SectionTitle>

        <HStack>
          <HStack>
            <IconButton
              aria-label="AWS"
              boxSize={iconButtonSize}
              minW={iconButtonSize}
              boxShadow="base"
              variant="ghost"
              icon={<AWSLogoIcon boxSize="full" />}
              onClick={() => {
                dispatch(setAddSystemsMethod(ValidTargets.AWS));
                dispatch(changeStep());
              }}
              data-testid="aws-btn"
            />
            <Text>Infrastructure Scan (AWS)</Text>
            <Tooltip
              fontSize="md"
              label="Infrastructure scanning allows you to connect to your cloud infrastructure and automatically identify systems that should be on your data map."
              placement="right"
            >
              <QuestionIcon boxSize={5} color="gray.400" />
            </Tooltip>
          </HStack>
          <HStack>
            <IconButton
              aria-label="Okta"
              boxSize={iconButtonSize}
              minW={iconButtonSize}
              boxShadow="base"
              variant="ghost"
              icon={<OktaLogoIcon boxSize="full" />}
              onClick={() => {
                dispatch(setAddSystemsMethod(ValidTargets.OKTA));
                dispatch(changeStep());
              }}
              data-testid="okta-btn"
            />
            <Text>System Scan (Okta)</Text>
          </HStack>
          <DataFlowScannerOption
            onClick={() => {
              dispatch(changeStep());
              dispatch(setAddSystemsMethod(SystemMethods.DATA_FLOW));
            }}
          />
        </HStack>
      </Box>
    </Stack>
  );
};

export default AddSystem;
