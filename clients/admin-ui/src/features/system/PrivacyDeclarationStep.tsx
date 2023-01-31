import { Box, Button, Divider, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { FormikHelpers } from "formik";
import { Fragment, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { changeReviewStep } from "~/features/config-wizard/config-wizard.slice";
import { PrivacyDeclaration, System } from "~/types/api";

import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import PrivacyDeclarationForm from "./PrivacyDeclarationForm";
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
  abridged?: boolean;
}

const PrivacyDeclarationStep = ({ system, onSuccess, abridged }: Props) => {
  const toast = useToast();
  const [formDeclarations, setFormDeclarations] = useState<
    PrivacyDeclaration[]
  >(system?.privacy_declarations ? [...system.privacy_declarations] : []);
  const [updateSystem] = useUpdateSystemMutation();
  const [isLoading, setIsLoading] = useState(false);
  const dispatch = useAppDispatch();

  const handleBack = () => {
    dispatch(changeReviewStep(1));
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
    <Stack spacing={10}>
      <Heading as="h3" size="lg">
        {/* TODO FUTURE: Path when describing system from infra scanning */}
        Privacy Declaration for {system.name}
      </Heading>
      <div>
        Now we’re going to declare our system’s privacy characteristics. Think
        of this as explaining who’s data the system is processing, what kind of
        data it’s processing and for what purpose it’s using that data and
        finally, how identifiable is the user with this data.
      </div>
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
      <PrivacyDeclarationForm onSubmit={addDeclaration} abridged={abridged} />
      <Box>
        <Button
          onClick={handleBack}
          mr={2}
          size="sm"
          variant="outline"
          data-testid="back-btn"
        >
          Back
        </Button>
        <Button
          colorScheme="primary"
          size="sm"
          isLoading={isLoading}
          data-testid="next-btn"
          onClick={handleSubmit}
        >
          Next
        </Button>
      </Box>
    </Stack>
  );
};

export default PrivacyDeclarationStep;
