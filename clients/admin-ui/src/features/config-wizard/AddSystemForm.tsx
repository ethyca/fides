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

import { useAppDispatch } from "~/app/hooks";
import { useFeatures } from "~/features/common/features.slice";
import {
  AWSLogoIcon,
  ManualSetupIcon,
  OktaLogoIcon,
  QuestionIcon,
  RuntimeScannerLogo,
} from "~/features/common/Icon";
import { ValidTargets } from "~/types/api";

import { changeStep, setAddSystemsMethod } from "./config-wizard.slice";
import { iconButtonSize } from "./constants";
import { SystemMethods } from "./types";

const AddSystemForm = () => {
  const dispatch = useAppDispatch();
  const { plus } = useFeatures();

  return (
    <chakra.form w="100%" data-testid="add-system-form">
      <Stack spacing={10}>
        <Heading as="h3" size="lg">
          Scan for Systems
        </Heading>
        <Accordion allowToggle border="transparent">
          <AccordionItem>
            {({ isExpanded }) => (
              <>
                <h2>
                  The building blocks of your data map are the list of systems
                  that exist in your organization. Think of systems as anything
                  that might store or process data in your organization, from a
                  web application, to a database or data warehouse.
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
            {plus ? (
              <Stack direction="row" display="flex" alignItems="center">
                <HStack>
                  <IconButton
                    aria-label="Data flow scan"
                    boxSize={iconButtonSize}
                    minW={iconButtonSize}
                    boxShadow="base"
                    variant="ghost"
                    icon={<RuntimeScannerLogo boxSize="10" />}
                    onClick={() => {
                      dispatch(changeStep());
                      dispatch(setAddSystemsMethod(SystemMethods.RUNTIME));
                    }}
                    data-testid="runtime-scan-btn"
                  />
                </HStack>
                <Text>Data Flow Scan</Text>
                <Tooltip
                  fontSize="md"
                  label="The scanner will connect to your infrastructure to automatically scan and create a list of all systems available."
                  placement="right"
                >
                  <QuestionIcon boxSize={5} color="gray.400" />
                </Tooltip>
              </Stack>
            ) : null}
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
