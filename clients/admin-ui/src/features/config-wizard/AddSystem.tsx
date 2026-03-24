import {
  ChakraBox as Box,
  ChakraHeading as Heading,
  ChakraSimpleGrid as SimpleGrid,
  ChakraStack as Stack,
  ChakraText as Text,
  ManualSetupIcon,
  useModal,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useRouter } from "next/router";

import { useAppDispatch } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  ADD_SYSTEMS_MANUAL_ROUTE,
  ADD_SYSTEMS_MULTIPLE_ROUTE,
} from "~/features/common/nav/routes";
import { ValidTargets } from "~/types/api";

import CalloutNavCard from "../common/CalloutNavCard";
import AWSLogo from "../common/logos/AWSLogo";
import OktaLogo from "../common/logos/OktaLogo";
import { changeStep, setAddSystemsMethod } from "./config-wizard.slice";
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
  const modal = useModal();
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
          infrastructure or Okta accounts. For everything else, you may manually
          add systems to your map.
        </Text>
      </Stack>
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
              icon={<ManualSetupIcon size={24} />}
              description="Manually add a system for services not covered by AWS or Okta discovery"
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
                modal.confirm({
                  title: "Upgrade to choose vendors",
                  content:
                    "To choose vendors and have system information auto-populated using Fides Compass, you will need to upgrade Fides. Meanwhile, you can manually add individual systems using the button below.",
                  okText: "Upgrade",
                  cancelText: "Add vendors manually",
                  centered: true,
                  icon: null,
                  onOk: () => {
                    window.open("https://ethyca.com/speak-with-us");
                  },
                  onCancel: () => {
                    router.push(ADD_SYSTEMS_MANUAL_ROUTE);
                  },
                });
              }
            }}
            data-testid="multiple-btn"
          >
            <CalloutNavCard
              title="Add multiple systems"
              color={palette.FIDESUI_OLIVE}
              icon={<ManualSetupIcon size={24} />}
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
              icon={<AWSLogo size={24} />}
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
              icon={<OktaLogo size={24} />}
            />
          </button>
        </SimpleGrid>
      </Box>
    </Stack>
  );
};

export default AddSystem;
