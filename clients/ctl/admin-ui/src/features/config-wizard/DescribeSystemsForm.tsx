import { Box, Button, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import React, { useState } from "react";
import * as Yup from "yup";

import {
  CustomCreatableMultiSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { DEFAULT_ORGANIZATION_FIDES_KEY } from "~/features/organization";
import DescribeSystemsFormExtension from "~/features/system/DescribeSystemsFormExtension";
import { useCreateSystemMutation } from "~/features/system/system.slice";
import { System } from "~/types/api";

const initialValues = {
  description: "",
  fides_key: "",
  name: "",
  organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
  tags: [],
  system_type: "",
  privacy_declarations: [],
  data_responsibility_title: undefined,
  administrating_department: "",
  third_country_transfers: [],
  system_dependencies: [],
  joint_controller: {
    name: "",
    email: "",
    address: "",
    phone: "",
  },
  data_protection_impact_assessment: {
    is_required: "false",
    progress: "",
    link: "",
  },
};
type FormValues = typeof initialValues;

const ValidationSchema = Yup.object().shape({
  fides_key: Yup.string().required().label("System key"),
  system_type: Yup.string().required().label("System type"),
});

const transformFormValuesToSystem = (formValues: FormValues): System => ({
  ...formValues,
  data_protection_impact_assessment: {
    ...formValues.data_protection_impact_assessment,
    is_required:
      formValues.data_protection_impact_assessment.is_required === "true",
  },
});

interface Props {
  onCancel: () => void;
  onSuccess: (system: System) => void;
  abridged?: boolean;
}

const DescribeSystemsForm = ({ onCancel, onSuccess, abridged }: Props) => {
  const [createSystem] = useCreateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);

  const toast = useToast();

  const handleSubmit = async (values: FormValues) => {
    const systemBody = {
      ...values,
      organization_fides_key: DEFAULT_ORGANIZATION_FIDES_KEY,
      privacy_declarations: [],
    };

    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while creating the system. Please try again."
        );

        toast({
          status: "error",
          description: errorMsg,
        });
      } else {
        toast.closeAll();
        onSuccess(transformFormValuesToSystem(values));
      }
    };

    setIsLoading(true);

    const createSystemResult = await createSystem(systemBody);
    handleResult(createSystemResult);

    setIsLoading(false);
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ dirty }) => (
        <Form>
          <Stack spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Describe your system
            </Heading>
            <div>
              By providing a small amount of additional context for each system
              we can make reporting and understanding our tech stack much easier
              for everyone from engineering to legal teams. So let’s do this
              now.
            </div>
            <Stack spacing={4}>
              <CustomTextInput
                id="name"
                name="name"
                label="System name"
                tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
              />
              <CustomTextInput
                id="fides_key"
                name="fides_key"
                label="System key"
                // TODO FUTURE: This tooltip text is misleading since at the moment for MVP we are manually creating a fides key for this resource
                tooltip="System keys are automatically generated from the resource id and system name to provide a unique key for identifying systems in the registry."
              />
              <CustomTextInput
                id="description"
                name="description"
                label="System description"
                tooltip="If you wish you can provide a description which better explains the purpose of this system."
              />
              <CustomTextInput
                id="system_type"
                label="System Type"
                name="system_type"
                tooltip="Describe the type of system being modeled, examples include: Service, Application, Third Party, etc"
              />
              <CustomCreatableMultiSelect
                id="tags"
                name="tags"
                label="System Tags"
                options={
                  initialValues.tags
                    ? initialValues.tags.map((s) => ({
                        value: s,
                        label: s,
                      }))
                    : []
                }
                tooltip="Provide one or more tags to group the system. Tags are important as they allow you to filter and group systems for reporting and later review. Tags provide tremendous value as you scale - imagine you have thousands of systems, you’re going to thank us later for tagging!"
              />
              {!abridged ? <DescribeSystemsFormExtension /> : null}
            </Stack>
            <Box>
              <Button
                onClick={() => onCancel()}
                mr={2}
                size="sm"
                variant="outline"
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={!dirty}
                isLoading={isLoading}
                data-testid="confirm-btn"
              >
                Confirm and Continue
              </Button>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
export default DescribeSystemsForm;
