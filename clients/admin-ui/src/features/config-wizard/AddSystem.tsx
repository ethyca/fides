import { Box, Heading, SimpleGrid, Stack, Text } from "@fidesui/react";

import { useAppDispatch } from "~/app/hooks";
import {
  AWSLogoIcon,
  ManualSetupIcon,
  OktaLogoIcon,
} from "~/features/common/Icon";
import { ValidTargets } from "~/types/api";

import { changeStep, setAddSystemsMethod } from "./config-wizard.slice";
import SystemOption, { DataFlowScannerOption } from "./SystemOption";
import { SystemMethods } from "./types";

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
    <Stack spacing={9} data-testid="add-systems">
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
        <SimpleGrid columns={{ sm: 2, md: 3 }} spacing="4">
          <SystemOption
            label="Add a system"
            icon={<ManualSetupIcon boxSize={8} />}
            description="Manually add a system for services not covered by automated scanners"
            onClick={() => {
              dispatch(changeStep(5));
              dispatch(setAddSystemsMethod(SystemMethods.MANUAL));
            }}
            data-testid="manual-btn"
          />
        </SimpleGrid>
      </Box>

      <Box data-testid="automated-options">
        <SectionTitle>Automated infrastructure scanning</SectionTitle>
        <SimpleGrid columns={{ sm: 2, md: 3 }} spacing="4">
          <SystemOption
            label="Scan your infrastructure (AWS)"
            description="Automatically discover new systems in your AWS infrastructure"
            icon={<AWSLogoIcon boxSize={8} />}
            onClick={() => {
              dispatch(setAddSystemsMethod(ValidTargets.AWS));
              dispatch(changeStep());
            }}
            data-testid="aws-btn"
          />
          <SystemOption
            label="Scan your Sign On Provider (Okta)"
            description="Automatically discover new systems in your Okta infrastructure"
            icon={<OktaLogoIcon boxSize={8} />}
            onClick={() => {
              dispatch(setAddSystemsMethod(ValidTargets.OKTA));
              dispatch(changeStep());
            }}
            data-testid="okta-btn"
          />
          <SystemOption
            label="Web Scanner"
            description="Run the web scanner"
            icon={<OktaLogoIcon boxSize={8} />}
            onClick={() => {
              dispatch(setAddSystemsMethod(ValidTargets.WEB_SCANNER));
              dispatch(changeStep());
            }}
            data-testid="okta-btn"
          />
          <DataFlowScannerOption
            onClick={() => {
              dispatch(changeStep());
              dispatch(setAddSystemsMethod(SystemMethods.DATA_FLOW));
            }}
          />
        </SimpleGrid>
      </Box>
    </Stack>
  );
};

export default AddSystem;
