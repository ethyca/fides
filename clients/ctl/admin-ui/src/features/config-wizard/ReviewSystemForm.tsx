import {
  Box,
  Button,
  Center,
  Divider,
  FormLabel,
  Heading,
  HStack,
  Spinner,
  Stack,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import React, { Fragment } from "react";

import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useGetOrganizationByFidesKeyQuery,
} from "~/features/organization";
import { System } from "~/types/api";

import { useGetSystemByFidesKeyQuery } from "../system/system.slice";
import TaxonomyEntityTag from "../taxonomy/TaxonomyEntityTag";
import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";

interface Props {
  systemKey: System["fides_key"];
  onCancel: () => void;
  onSuccess: () => void;
}

const ReviewSystemForm = ({ systemKey, onCancel, onSuccess }: Props) => {
  const { data: existingSystem, isLoading } =
    useGetSystemByFidesKeyQuery(systemKey);
  const { data: existingOrg } = useGetOrganizationByFidesKeyQuery(
    DEFAULT_ORGANIZATION_FIDES_KEY
  );

  if (isLoading) {
    return (
      <Center>
        <Spinner />
      </Center>
    );
  }

  if (!existingSystem) {
    return (
      <Text>
        Could not find a system with key{" "}
        <Text as="span" fontWeight="semibold">
          {systemKey}
        </Text>
      </Text>
    );
  }

  const initialValues = {
    name: existingOrg?.name ?? "",
    system_name: existingSystem?.name ?? "",
    system_key: existingSystem?.fides_key ?? "",
    system_description: existingSystem?.description ?? "",
    system_type: existingSystem?.system_type ?? "",
    tags: existingSystem?.tags ?? [],
    privacy_declarations: existingSystem?.privacy_declarations ?? [],
  };

  const handleSubmit = () => {
    onSuccess();
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
    >
      <Form>
        <Stack spacing={10}>
          <Heading as="h3" size="lg">
            {/* TODO FUTURE: Path when describing system from infra scanning */}
            Review {existingOrg?.name}
          </Heading>
          <Text mt="10px !important">
            Let’s quickly review our declaration before registering
          </Text>
          <Stack spacing={4}>
            <HStack>
              <FormLabel fontWeight="semibold" m={0}>
                System name:
              </FormLabel>
              <Text>{initialValues.system_name}</Text>
            </HStack>
            <HStack>
              <FormLabel fontWeight="semibold" m={0}>
                System key:
              </FormLabel>
              <Text>{initialValues.system_key}</Text>
            </HStack>
            <HStack>
              <FormLabel fontWeight="semibold" m={0}>
                System description:
              </FormLabel>
              <Text>{initialValues.system_description}</Text>
            </HStack>
            <HStack>
              <FormLabel fontWeight="semibold" m={0}>
                System type:
              </FormLabel>
              <Text>{initialValues.system_type}</Text>
            </HStack>
            <HStack>
              <FormLabel fontWeight="semibold" m={0}>
                System tags:
              </FormLabel>
              {initialValues.tags.map((tag) => (
                <TaxonomyEntityTag key={tag} name={tag} />
              ))}
            </HStack>
            <FormLabel fontWeight="semibold">Privacy declarations:</FormLabel>
            {initialValues.privacy_declarations.map((declaration) => (
              <Fragment key={declaration.name}>
                <Divider />
                <PrivacyDeclarationAccordion privacyDeclaration={declaration} />
              </Fragment>
            ))}
          </Stack>
          <Box>
            <Button
              onClick={() => onCancel()}
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
          </Box>
        </Stack>
      </Form>
    </Formik>
  );
};
export default ReviewSystemForm;
