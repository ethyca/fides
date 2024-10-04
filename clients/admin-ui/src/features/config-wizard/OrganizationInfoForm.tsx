import {
  AntButton,
  chakra,
  FormControl,
  FormLabel,
  Heading,
  Input,
  QuestionIcon,
  Stack,
  Tooltip,
  useToast,
} from "fidesui";
import { useFormik } from "formik";
import { useEffect, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  DEFAULT_ORGANIZATION_FIDES_KEY,
  useCreateOrganizationMutation,
  useGetOrganizationByFidesKeyQuery,
  useUpdateOrganizationMutation,
} from "~/features/organization";
import { Organization } from "~/types/api";

import { changeStep, setOrganization } from "./config-wizard.slice";

const useOrganizationInfoForm = () => {
  const dispatch = useAppDispatch();
  const handleSuccess = (organization: Organization) => {
    dispatch(setOrganization(organization));
    dispatch(changeStep());
  };

  const [createOrganization] = useCreateOrganizationMutation();
  const [updateOrganization] = useUpdateOrganizationMutation();
  const { data: existingOrg, isLoading: isLoadingOrganization } =
    useGetOrganizationByFidesKeyQuery(DEFAULT_ORGANIZATION_FIDES_KEY);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  useEffect(() => {
    // Only consider a redirect when data has loaded but before a user has submitted anything
    if (isLoadingOrganization || hasSubmitted) {
      return;
    }
    // If the organization name and description already exist, we bypass this step
    if (existingOrg?.name && existingOrg?.description) {
      dispatch(changeStep());
    }
  }, [isLoadingOrganization, existingOrg, dispatch, hasSubmitted]);

  const toast = useToast();
  const formik = useFormik({
    initialValues: {
      name: existingOrg?.name ?? "",
      description: existingOrg?.description ?? "",
    },
    onSubmit: async (values) => {
      setHasSubmitted(true);
      const organizationBody = {
        name: values.name ?? existingOrg?.name,
        description: values.description ?? existingOrg?.description,
        fides_key: existingOrg?.fides_key ?? DEFAULT_ORGANIZATION_FIDES_KEY,
        organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
      };

      if (!existingOrg) {
        const createOrganizationResult =
          await createOrganization(organizationBody);

        if (isErrorResult(createOrganizationResult)) {
          const errorMsg = getErrorMessage(createOrganizationResult.error);

          toast({
            status: "error",
            description: errorMsg,
          });
          return;
        }
        toast.closeAll();
        handleSuccess(organizationBody);
      } else {
        const updateOrganizationResult =
          await updateOrganization(organizationBody);

        if (isErrorResult(updateOrganizationResult)) {
          const errorMsg = getErrorMessage(updateOrganizationResult.error);

          toast({
            status: "error",
            description: errorMsg,
          });
          return;
        }
        toast.closeAll();
        handleSuccess(organizationBody);
      }
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

  return formik;
};

const OrganizationInfoForm = () => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    touched,
    values,
    isSubmitting,
  } = useOrganizationInfoForm();

  return (
    <chakra.form
      onSubmit={handleSubmit}
      w="40%"
      data-testid="organization-info-form"
    >
      <Stack spacing={10}>
        <Heading as="h3" size="lg">
          Create your Organization
        </Heading>
        <div>
          Provide your organization information. This information is used to
          configure your organization in Fides for data map reporting purposes.
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
        <AntButton
          type="primary"
          htmlType="submit"
          disabled={!values.name || !values.description}
          loading={isSubmitting}
          data-testid="submit-btn"
        >
          Save and continue
        </AntButton>
      </Stack>
    </chakra.form>
  );
};
export default OrganizationInfoForm;
