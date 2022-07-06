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
import React from "react";

import { useAppDispatch } from "~/app/hooks";
import {
  AWSLogoIcon,
  ManualSetupIcon,
  OktaLogoIcon,
  QuestionIcon,
} from "~/features/common/Icon";

import { changeStep } from "./config-wizard.slice";
import { iconButtonSize } from "./constants";

const AddSystemForm = () => {
  const dispatch = useAppDispatch();

  return (
    <chakra.form w="100%">
      <Stack ml="100px" spacing={10}>
        <Heading as="h3" size="lg">
          Add a system
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
        <Stack>
          <FormControl>
            <Stack direction="row" display="flex" alignItems="center" mb={5}>
              <IconButton
                aria-label="AWS"
                boxSize={iconButtonSize}
                minW={iconButtonSize}
                boxShadow="base"
                variant="ghost"
                icon={<AWSLogoIcon boxSize="full" />}
                onClick={() => dispatch(changeStep())}
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
            <Stack direction="row" display="flex" alignItems="center" mb={5}>
              <IconButton
                aria-label="Okta"
                boxSize={iconButtonSize}
                minW={iconButtonSize}
                boxShadow="base"
                variant="ghost"
                icon={<OktaLogoIcon boxSize="full" />}
                onClick={() => dispatch(changeStep())}
              />
              <Text>System Scan (Okta)</Text>
              <Tooltip
                fontSize="md"
                label="System scanning allows you to connect to your sign-on platform and automatically identify systems that should be on your data map."
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>
            <Stack direction="row" display="flex" alignItems="center">
              <HStack>
                <IconButton
                  aria-label="Manual setup"
                  boxSize={iconButtonSize}
                  minW={iconButtonSize}
                  boxShadow="base"
                  variant="ghost"
                  icon={<ManualSetupIcon boxSize="full" />}
                  onClick={() => dispatch(changeStep(5))}
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
          </FormControl>
        </Stack>
      </Stack>
    </chakra.form>
  );
};

export default AddSystemForm;
