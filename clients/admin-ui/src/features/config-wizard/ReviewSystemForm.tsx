import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Divider,
  FormLabel,
  Heading,
  HStack,
  Stack,
  Tag,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import React from "react";

import { useGetSystemByFidesKeyQuery } from "../system/system.slice";
import { useGetOrganizationByFidesKeyQuery } from "./organization.slice";

const ReviewSystemForm: NextPage<{
  handleChangeStep: Function;
  handleChangeReviewStep: Function;
  handleCancelSetup: Function;
  systemFidesKey: string;
}> = ({
  handleCancelSetup,
  handleChangeStep,
  handleChangeReviewStep,
  systemFidesKey,
}) => {
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(systemFidesKey);
  const { data: existingOrg } = useGetOrganizationByFidesKeyQuery(
    "default_organization"
  );

  const initialValues = {
    name: existingOrg?.name ?? "",
    system_name: existingSystem?.name ?? "",
    system_key: existingSystem?.fides_key ?? "",
    system_description: existingSystem?.description ?? "",
    system_type: existingSystem?.system_type ?? "",
    system_dependencies: existingSystem?.system_dependencies ?? [],
    privacy_declarations: existingSystem?.privacy_declarations ?? [],
  };

  const handleSubmit = () => {
    handleChangeStep(5);
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
    >
      <Form>
        <Stack ml="100px" spacing={10}>
          <Heading as="h3" size="lg">
            {/* TODO FUTURE: Path when describing system from infra scanning */}
            Review {existingOrg?.name}
          </Heading>
          <Text mt="10px !important">
            Let’s quickly review our declaration before registering
          </Text>
          <Stack>
            <HStack>
              <FormLabel>System name:</FormLabel>
              <Text>{initialValues.system_name}</Text>
            </HStack>

            <HStack>
              <FormLabel>System key:</FormLabel>
              <Text>{initialValues.system_key}</Text>
            </HStack>
            <HStack>
              <FormLabel>System description:</FormLabel>
              <Text>{initialValues.system_description}</Text>
            </HStack>
            <HStack>
              <FormLabel>System type:</FormLabel>
              <Text>{initialValues.system_type}</Text>
            </HStack>
            <HStack>
              <FormLabel>System tags:</FormLabel>
              {initialValues.system_dependencies.map((dependency) => (
                <Tag
                  background="primary.400"
                  color="white"
                  key={dependency}
                  width="fit-content"
                >
                  {dependency}
                </Tag>
              ))}
            </HStack>
            <FormLabel>Privacy declarations:</FormLabel>
            {initialValues.privacy_declarations.length > 0
              ? initialValues.privacy_declarations.map((declaration: any) => (
                  <>
                    <Divider />
                    <Accordion
                      allowToggle
                      border="transparent"
                      key={declaration.name}
                      maxW="500px"
                      minW="500px"
                      width="500px"
                    >
                      <AccordionItem>
                        <>
                          <AccordionButton>
                            <Box flex="1" textAlign="left">
                              {declaration.name}
                            </Box>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel padding="0px" mt="20px">
                            <HStack mb="20px">
                              <Text color="gray.600">
                                Declaration categories
                              </Text>
                              {declaration.data_categories.map(
                                (category: any) => (
                                  <Tag
                                    background="primary.400"
                                    color="white"
                                    key={category}
                                    width="fit-content"
                                  >
                                    {category}
                                  </Tag>
                                )
                              )}
                            </HStack>
                            <HStack mb="20px">
                              <Text color="gray.600">Data use</Text>
                              <Tag
                                background="primary.400"
                                color="white"
                                width="fit-content"
                              >
                                {declaration.data_use}
                              </Tag>
                            </HStack>
                            <HStack mb="20px">
                              <Text color="gray.600">Data subjects</Text>
                              {declaration.data_subjects.map((subject: any) => (
                                <Tag
                                  background="primary.400"
                                  color="white"
                                  key={subject}
                                  width="fit-content"
                                >
                                  {subject}
                                </Tag>
                              ))}
                            </HStack>
                            <HStack mb="20px">
                              <Text color="gray.600">Data qualifier</Text>
                              <Tag
                                background="primary.400"
                                color="white"
                                width="fit-content"
                              >
                                {declaration.data_qualifier}
                              </Tag>
                            </HStack>
                          </AccordionPanel>
                        </>
                      </AccordionItem>
                    </Accordion>
                  </>
                ))
              : null}
          </Stack>
          <Box>
            <Button
              onClick={() => handleCancelSetup()}
              mr={2}
              size="sm"
              variant="outline"
            >
              Cancel
            </Button>
            {/* TODO FUTURE: This button doesn't do any registering yet until data maps are added */}
            <Button type="submit" colorScheme="primary" mr={2} size="sm">
              Confirm and Register
            </Button>
            <Button
              onClick={() => {
                handleChangeStep(4);
                handleChangeReviewStep(4);
              }}
              colorScheme="primary"
              size="sm"
            >
              Add another system manually
            </Button>
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};
export default ReviewSystemForm;
