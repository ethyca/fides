import {
  Button,
  chakra,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
  Tooltip,
  useToast,
} from "@fidesui/react";
import { useFormik } from "formik";
import type { NextPage } from "next";
import React, { useState } from "react";

import { QuestionIcon } from "~/features/common/Icon";

import { useCreateOrganizationMutation } from "./organization.slice";

const useOrganizationInfoForm = (handleChangeStep: Function) => {
  const [createOrganization] = useCreateOrganizationMutation();
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
    },
    onSubmit: async (values) => {
      const organizationBody = {
        name: values.name,
        description: values.description,
        fides_key: "default_organization_19",
      };
      setIsLoading(true);

      // @ts-ignore
      const { error: createOrganizationError } = await createOrganization(
        organizationBody
      );

      setIsLoading(false);

      if (createOrganizationError) {
        toast({
          status: "error",
          description: "Creating organization failed.",
        });
      } else {
        handleChangeStep(1);
        toast.closeAll();
      }
    },
    validate: (values) => {
      const errors: {
        name?: string;
        description?: string;
      } = {};

      if (!values.name) {
        errors.name = "Organization name is required";
      }

      if (!values.description) {
        errors.description = "Organization description is equired";
      }

      return errors;
    },
  });

  return { ...formik, isLoading };
};

const OrganizationInfoForm: NextPage<{
  handleChangeStep: Function;
}> = ({ handleChangeStep }) => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    isLoading,
    touched,
    values,
  } = useOrganizationInfoForm(handleChangeStep);

  return (
    <chakra.form onSubmit={handleSubmit}>
      <Stack ml="50px" spacing="24px" w="80%">
        <Heading as="h3" size="lg">
          Tell us about your business
        </Heading>
        <div>
          Provide your organization information. This information is used to
          configure your organization in Fidesctl for{" "}
          <Tooltip
            fontSize="md"
            label="Wondering what a data map is? No problem, we've got your covered with this quick overview here"
            placement="right"
          >
            <Text display="inline" color="complimentary.500">
              data map
            </Text>
          </Tooltip>{" "}
          reporting purposes.
        </div>
        <Stack>
          <FormControl>
            <Stack direction="row" mb={5} justifyContent="flex-end">
              <FormLabel w="100%">Organization name</FormLabel>
              <Input
                type="text"
                id="name"
                name="name"
                focusBorderColor="gray.700"
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.name}
                isInvalid={touched.name && Boolean(errors.name)}
                minW="65%"
                w="65%"
              />
              <Tooltip
                fontSize="md"
                label="The legal name of your organization"
                placement="right"
              >
                <QuestionIcon boxSize={5} color="gray.400" />
              </Tooltip>
            </Stack>
            <Stack direction="row" justifyContent="flex-end">
              <FormLabel w="100%">Description</FormLabel>
              <Input
                type="text"
                id="description"
                name="description"
                focusBorderColor="gray.700"
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.description}
                isInvalid={touched.description && Boolean(errors.description)}
                minW="65%"
                w="65%"
              />
              <Tooltip
                fontSize="md"
                label="An explanation of the type of organization and primary activity. 
                  For example “Acme Inc. is an e-commerce company that sells scarves.”"
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
          disabled={!values.name || !values.description}
          isLoading={isLoading}
          type="submit"
        >
          Save and Continue
        </Button>
      </Stack>
    </chakra.form>
  );
};
export default OrganizationInfoForm;
