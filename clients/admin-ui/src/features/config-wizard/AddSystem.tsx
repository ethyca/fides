import { Box, Heading, SimpleGrid, Stack, Text, useDisclosure } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";

import { useAppDispatch } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  AWSLogoIcon,
  ManualSetupIcon,
  OktaLogoIcon,
} from "~/features/common/Icon";
import { UpgradeModal } from "~/features/common/modals/UpgradeModal";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
} from "~/features/common/nav/routes";
import { ValidTargets } from "~/types/api";

import CalloutNavCard from "../common/CalloutNavCard";
import { changeStep, setAddSystemsMethod } from "./config-wizard.slice";
import DataFlowScannerOption from "./DataFlowScannerOption";
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
  const router = useRouter();
  const { isOpen, onClose, onOpen } = useDisclosure();
  const { dictionaryService: isCompassEnabled } = useFeatures();

  return (
    <Stack spacing={9} data-testid="add-systems">
      <Stack spacing={6} maxWidth="600px">
        <Heading as="h3" size="md" fontWeight="semibold">
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
      <UpgradeModal
        isOpen={isOpen}
        onConfirm={() => {
          window.open("https://fid.es/upgrade-compass");
        }}
        onCancel={() => {
          router.push(ADD_SYSTEMS_MANUAL_ROUTE);
        }}
        onClose={onClose}
      />
      <Box data-testid="manual-options">
        <SectionTitle>Manually add systems</SectionTitle>
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing="4">
          <button
            className="flex flex-col text-left"
            type="button"
            aria-label="Add a system"
            onClick={() => {
              dispatch(setAddSystemsMethod(SystemMethods.MANUAL));
              router.push(ADD_SYSTEMS_MANUAL_ROUTE);
            }}
            data-testid="manual-btn"
          >
            <CalloutNavCard
              title="Add a system"
              color={palette.FIDESUI_SANDSTONE}
              icon={<ManualSetupIcon boxSize={6} />}
              description="Manually add a system for services not covered by automated scanners"
            />
          </button>
          <button
            className="flex flex-col text-left"
            type="button"
            aria-label="Add multiple systems"
            onClick={() => {
              if (isCompassEnabled) {
                dispatch(setAddSystemsMethod(SystemMethods.MANUAL));
                router.push(ADD_SYSTEMS_MULTIPLE_ROUTE);
              } else {
                onOpen();
              }
            }}
            data-testid="multiple-btn"
          >
            <CalloutNavCard
              title="Add multiple systems"
              color={palette.FIDESUI_OLIVE}
              icon={<ManualSetupIcon boxSize={6} />}
              description="Choose vendors and automatically populate system details"
            />
          </button>
        </SimpleGrid>
      </Box>

      <Box data-testid="automated-options">
        <SectionTitle>Automated infrastructure scanning</SectionTitle>
        <SimpleGrid columns={{ base: 1, md: 2, xl: 3 }} spacing="4">
          <button
            className="flex flex-col text-left"
            type="button"
            aria-label="Scan your infrastructure (AWS)"
            onClick={() => {
              dispatch(setAddSystemsMethod(ValidTargets.AWS));
              dispatch(changeStep());
            }}
            data-testid="aws-btn"
          >
            <CalloutNavCard
              title="Scan your infrastructure (AWS)"
              color={palette.FIDESUI_TERRACOTTA}
              description="Automatically discover new systems in your AWS infrastructure"
              icon={<AWSLogoIcon boxSize={6} />}
            />
          </button>
          <button
            className="flex flex-col text-left"
            type="button"
            aria-label="Scan your Sign On Provider (Okta)"
            onClick={() => {
              dispatch(setAddSystemsMethod(ValidTargets.OKTA));
              dispatch(changeStep());
            }}
            data-testid="okta-btn"
          >
            <CalloutNavCard
              title="Scan your Sign On Provider (Okta)"
              color={palette.FIDESUI_MINOS}
              description="Automatically discover new systems in your Okta infrastructure"
              icon={<OktaLogoIcon boxSize={6} />}
            />
          </button>
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
