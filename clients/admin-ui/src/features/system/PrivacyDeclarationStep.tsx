import {
  Box,
  Button,
  Divider,
  Heading,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { FormikHelpers } from "formik";
import NextLink from "next/link";
import { Fragment, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PrivacyDeclaration, System } from "~/types/api";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import ConnectedPrivacyDeclarationForm from "./PrivacyDeclarationForm";
import { useUpdateSystemMutation } from "./system.slice";

type FormValues = PrivacyDeclaration;

const transformFormValuesToDeclaration = (
  formValues: FormValues
): PrivacyDeclaration => ({
  ...formValues,
  data_qualifier:
    formValues.data_qualifier === "" ? undefined : formValues.data_qualifier,
});

interface Props {
  system: System;
  onSuccess: (system: System) => void;
}

const PrivacyDeclarationStep = ({ system, onSuccess }: Props) => {
  const toast = useToast();
  const [formDeclarations, setFormDeclarations] = useState<
    PrivacyDeclaration[]
  >(system?.privacy_declarations ? [...system.privacy_declarations] : []);
  const [updateSystemMutationTrigger, { isLoading }] =
    useUpdateSystemMutation();

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

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration
    );

    handleResult(updateSystemResult);
  };

  const handleEditDeclaration = (
    oldDeclaration: PrivacyDeclaration,
    newDeclaration: PrivacyDeclaration
  ) => {
    // Because the name can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    setFormDeclarations(
      formDeclarations.map((dec) =>
        dec.name === oldDeclaration.name ? newDeclaration : dec
      )
    );
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
    <Stack spacing={3}>
      <Heading as="h3" size="md">
        Data uses
      </Heading>
      <Text fontSize="sm">
        This is where you describe your system privacy characteristics. First,
        you declare a data processing activity (&quot;Data use&quot;) and then
        assign the Data categories and Data subjects that are related to this
        activity. Individual Data categories and subjects may be assigned to
        multiple Data uses. If you don&apos;t find the activity, category, or
        subject that you need, the taxonomy may need to be updated.{" "}
        <NextLink href="/taxonomy" passHref>
          <Text as="a" color="complimentary.600">
            Manage taxonomy
          </Text>
        </NextLink>
        .
      </Text>
      {formDeclarations.map((declaration) => (
        <Fragment key={declaration.name}>
          <PrivacyDeclarationAccordion
            privacyDeclaration={declaration}
            onEdit={(newValues) => {
              handleEditDeclaration(declaration, newValues);
            }}
          />
          <Divider m="0px !important" />
        </Fragment>
      ))}
      <ConnectedPrivacyDeclarationForm onSubmit={addDeclaration} />
      <Box>
        <Button
          colorScheme="primary"
          size="xs"
          isLoading={isLoading}
          data-testid="save-btn"
          onClick={handleSubmit}
        >
          Add a Data Use +
        </Button>
      </Box>
    </Stack>
  );
};

export default PrivacyDeclarationStep;
