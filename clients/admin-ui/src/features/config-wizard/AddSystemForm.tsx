import {
  Accordion,
  AccordionButton,
  AccordionItem,
  AccordionPanel,
  chakra,
  FormControl,
  Heading,
  HStack,
  IconButton,
  Stack,
  Text,
  Tooltip,
} from "@fidesui/react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ConnectedCircle from "~/features/common/ConnectedCircle";
import { useFeatures } from "~/features/common/features.slice";
import {
  AWSLogoIcon,
  DataFlowScannerLogo,
  ManualSetupIcon,
  OktaLogoIcon,
  QuestionIcon,
} from "~/features/common/Icon";
import { selectDataFlowScannerStatus } from "~/features/plus/plus.slice";
import { ADD_SYSTEM_DESCRIPTION } from "~/features/system/constants";
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

const AddSystemForm = () => {
  const dispatch = useAppDispatch();

  return (
    <chakra.form w="100%" data-testid="add-system-form">
      <Stack spacing={10}>
        <Heading as="h3" size="lg">
          Add Systems
        </Heading>
        <Accordion allowToggle border="transparent">
          <AccordionItem>
            {({ isExpanded }) => (
              <>
                <h2>
                  {ADD_SYSTEM_DESCRIPTION}
                  <AccordionButton
                    display="inline"
                    padding="0px"
                    ml="5px"
                    width="auto"
                    color="complimentary.500"
                  >
                    {isExpanded ? `(show less)` : `(show more)`}
                  </AccordionButton>
                </h2>
                <AccordionPanel padding="0px" mt="20px">
                  Let’s get started by adding systems that contain data in our
                  organization. You can speed this up by using the automated
                  scanners or adding your systems manually.
                </AccordionPanel>
              </>
            )}
          </AccordionItem>
        </Accordion>
        <FormControl>
          <Stack spacing={5}>
            <Stack direction="row" display="flex" alignItems="center">
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
            </Stack>
            <Stack direction="row" display="flex" alignItems="center">
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
            </Stack>
            <DataFlowScannerOption
              onClick={() => {
                dispatch(changeStep());
                dispatch(setAddSystemsMethod(SystemMethods.DATA_FLOW));
              }}
            />
            <Stack direction="row" display="flex" alignItems="center">
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
            </Stack>
          </Stack>
        </FormControl>
      </Stack>
    </chakra.form>
  );
};

export default AddSystemForm;
