import {
  Accordion,
  AccordionButton,
  AccordionItem,
  AccordionPanel,
  Button,
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

const AddSystemForm: NextPage<{
  handleChangeStep: Function;
}> = ({ handleChangeStep }) => (
    <chakra.form
    // onSubmit={handleSubmit}
    >
      <Stack ml="50px" spacing="24px" w="80%">
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
                    {isExpanded ? (
                      <Text display="inline" color="complimentary.500">
                        (show less)
                      </Text>
                    ) : (
                      <Text display="inline" color="complimentary.500">
                        (show more)
                      </Text>
                    )}
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
                height="107px"
                icon={<AWSLogoIcon />}
                width="107px"
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
                height="107px"
                icon={<OktaLogoIcon />}
                width="107px"
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
                  height="107px"
                  icon={<ManualSetupIcon />}
                  width="107px"
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
        <Button
          bg="primary.800"
          _hover={{ bg: "primary.400" }}
          _active={{ bg: "primary.500" }}
          colorScheme="primary"
          type="submit"
          onClick={() => handleChangeStep(2)}
        >
          Save and Continue
        </Button>
      </Stack>
    </chakra.form>
  );
export default AddSystemForm;
