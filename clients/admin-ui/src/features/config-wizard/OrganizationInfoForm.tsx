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
import React, { useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { QuestionIcon } from "~/features/common/Icon";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useCreateOrganizationMutation,
  useGetOrganizationByFidesKeyQuery,
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { Organization } from "~/types/api";

import { isErrorWithDetail, isErrorWithDetailArray } from "../common/helpers";
import { changeStep, setOrganization } from "./config-wizard.slice";

const useOrganizationInfoForm = () => {
  const dispatch = useAppDispatch();
  const handleSuccess = (organization: Organization) => {
    dispatch(setOrganization(organization));
    dispatch(changeStep());
  };

  const [createOrganization] = useCreateOrganizationMutation();
  const [updateOrganization] = useUpdateOrganizationMutation();
  const { data: existingOrg } = useGetOrganizationByFidesKeyQuery(
    DEFAULT_ORGANIZATION_FIDES_KEY
  );
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const formik = useFormik({
    initialValues: {
      name: existingOrg?.name ?? "",
      description: existingOrg?.description ?? "",
    },
    onSubmit: async (values) => {
      const organizationBody = {
        name: values.name ?? existingOrg?.name,
        description: values.description ?? existingOrg?.description,
        fides_key: existingOrg?.fides_key ?? DEFAULT_ORGANIZATION_FIDES_KEY,
        organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
      };

      setIsLoading(true);

      if (!existingOrg) {
        const createOrganizationResult = await createOrganization(
          organizationBody
        );

        if ("error" in createOrganizationResult) {
          let errorMsg = "An unexpected error occurred. Please try again.";
          if (isErrorWithDetail(createOrganizationResult.error)) {
            errorMsg = createOrganizationResult.error.data.detail;
          } else if (isErrorWithDetailArray(createOrganizationResult.error)) {
            const { error } = createOrganizationResult;
            errorMsg = error.data.detail[0].msg;
          }
          toast({
            status: "error",
            description: errorMsg,
          });
          return;
        }
        toast.closeAll();
        handleSuccess(organizationBody);
      } else {
        const updateOrganizationResult = await updateOrganization(
          organizationBody
        );

        if ("error" in updateOrganizationResult) {
          let errorMsg = "An unexpected error occurred. Please try again.";
          if (isErrorWithDetail(updateOrganizationResult.error)) {
            errorMsg = updateOrganizationResult.error.data.detail;
          } else if (isErrorWithDetailArray(updateOrganizationResult.error)) {
            const { error } = updateOrganizationResult;
            errorMsg = error.data.detail[0].msg;
          }
          toast({
            status: "error",
            description: errorMsg,
          });
          return;
        }
        toast.closeAll();
        handleSuccess(organizationBody);
      }

      setIsLoading(false);
    },
    enableReinitialize: true,
    validate: (values) => {
      const errors: {
        name?: string;
        description?: string;
      } = {};

      if (!values.name) {
        errors.name = "Organization name is required";
      }

      if (!values.description) {
        errors.description = "Organization description is required";
      }

      return errors;
    },
  });

  return { ...formik, isLoading };
};

const OrganizationInfoForm = () => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    isLoading,
    touched,
    values,
  } = useOrganizationInfoForm();

  return (
    <chakra.form
      onSubmit={handleSubmit}
      w="100%"
      data-testid="organization-info-form"
    >
      <Stack spacing={10}>
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
                data-testid="input-name"
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
                data-testid="input-description"
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
          type="submit"
          variant="primary"
          isDisabled={!values.name || !values.description}
          isLoading={isLoading}
          data-testid="submit-btn"
        >
          Save and Continue
        </Button>
      </Stack>
    </chakra.form>
  );
};
export default OrganizationInfoForm;
