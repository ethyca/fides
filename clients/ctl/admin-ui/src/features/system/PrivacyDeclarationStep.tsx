import { Box, Button, Divider, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik, FormikHelpers } from "formik";
import React, { Fragment, useState } from "react";
import * as Yup from "yup";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { AddIcon } from "~/features/common/Icon";
import { PrivacyDeclaration, System } from "~/types/api";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import PrivacyDeclarationForm from "./PrivacyDeclarationForm";
import { useUpdateSystemMutation } from "./system.slice";

type FormValues = PrivacyDeclaration;

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Declaration name"),
  data_categories: Yup.array(Yup.string())
    .min(1, "Must assign at least one data category")
    .label("Data categories"),
  data_use: Yup.string().required().label("Data use"),
  data_subjects: Yup.array(Yup.string())
    .min(1, "Must assign at least one data subject")
    .label("Data subjects"),
});

const transformFormValuesToDeclaration = (
  formValues: FormValues
): PrivacyDeclaration => ({
  ...formValues,
  data_qualifier:
    formValues.data_qualifier === "" ? undefined : formValues.data_qualifier,
});

interface Props {
  system: System;
  onCancel: () => void;
  onSuccess: (system: System) => void;
  abridged?: boolean;
}

const PrivacyDeclarationStep = ({
  system,
  onCancel,
  onSuccess,
  abridged,
}: Props) => {
  const toast = useToast();
  const [formDeclarations, setFormDeclarations] = useState<
    PrivacyDeclaration[]
  >(system?.privacy_declarations ? [...system.privacy_declarations] : []);
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);

  const initialValues: PrivacyDeclaration = {
    name: "",
    data_categories: [],
    data_subjects: [],
    data_use: "",
    data_qualifier: "",
    dataset_references: [],
  };

  const handleSubmit = async () => {
    const systemBodyWithDeclaration = {
      ...system,
      privacy_declarations: formDeclarations,
    };

    const handleResult = (
      result:
        | { data: System }
        | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while updating the system. Please try again."
        );

        toast({
          status: "error",
          description: errorMsg,
        });
      } else {
        toast.closeAll();
        onSuccess(result.data);
      }
    };

    setIsLoading(true);

    const updateSystemResult = await updateSystem(systemBodyWithDeclaration);

    handleResult(updateSystemResult);
    setIsLoading(false);
  };

  const addDeclaration = (
    values: PrivacyDeclaration,
    formikHelpers: FormikHelpers<PrivacyDeclaration>
  ) => {
    const { resetForm } = formikHelpers;
    if (formDeclarations.filter((d) => d.name === values.name).length > 0) {
      toast({
        status: "error",
        description:
          "A declaration already exists with that name in this system. Please use a different name.",
      });
    } else {
      toast.closeAll();
      setFormDeclarations([
        ...formDeclarations,
        transformFormValuesToDeclaration(values),
      ]);
      resetForm({
        values: {
          name: "",
          data_subjects: [],
          data_categories: [],
          data_use: "",
          data_qualifier: "",
          dataset_references: [],
        },
      });
    }
  };

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={addDeclaration}
      validationSchema={ValidationSchema}
    >
      {({ dirty }) => (
        <Form data-testid="privacy-declaration-form">
          <Stack spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Privacy Declaration for {system.name}
            </Heading>
            <div>
              Now we’re going to declare our system’s privacy characteristics.
              Think of this as explaining who’s data the system is processing,
              what kind of data it’s processing and for what purpose it’s using
              that data and finally, how identifiable is the user with this
              data.
            </div>
            {formDeclarations.map((declaration) => (
              <Fragment key={declaration.name}>
                <PrivacyDeclarationAccordion privacyDeclaration={declaration} />
                <Divider m="0px !important" />
              </Fragment>
            ))}
            <PrivacyDeclarationForm abridged={abridged} />
            <Box>
              <Button
                type="submit"
                colorScheme="purple"
                variant="link"
                disabled={!dirty}
                isLoading={isLoading}
                data-testid="add-btn"
              >
                Add <AddIcon boxSize={10} />
              </Button>
            </Box>
            <Box>
              <Button
                onClick={onCancel}
                mr={2}
                size="sm"
                variant="outline"
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                colorScheme="primary"
                size="sm"
                disabled={formDeclarations.length === 0}
                isLoading={isLoading}
                data-testid="next-btn"
                onClick={handleSubmit}
              >
                Next
              </Button>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PrivacyDeclarationStep;
