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
import type { NextPage } from "next";
import React from "react";
import {
  AWSLogoIcon,
  ManualSetupIcon,
  OktaLogoIcon,
  QuestionIcon,
} from "~/features/common/Icon";
import { iconButtonSize } from "./constants";

const AddSystemForm: NextPage<{
  handleChangeStep: Function;
}> = ({ handleChangeStep }) => (
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
                  ml="5px !important"
                  width="auto"
                >
                  <Text display="inline" color="complimentary.500">
                    {isExpanded ? `(show less)` : `(show more)`}
                  </Text>
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
              background="white"
              height={`${iconButtonSize}px`}
              icon={<AWSLogoIcon />}
              onClick={() => handleChangeStep(2)}
              width={`${iconButtonSize}px`}
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
              background="white"
              height={`${iconButtonSize}px`}
              icon={<OktaLogoIcon />}
              onClick={() => handleChangeStep(2)}
              width={`${iconButtonSize}px`}
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
                background="white"
                height={`${iconButtonSize}px`}
                icon={<ManualSetupIcon />}
                onClick={() => handleChangeStep(4)}
                width={`${iconButtonSize}px`}
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
export default AddSystemForm;
