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
import NextLink from "next/link";
import { useMemo, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { PrivacyDeclaration, System } from "~/types/api";

import { errorToastParams, successToastParams } from "../common/toast";
import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import ConnectedPrivacyDeclarationForm from "./PrivacyDeclarationForm";
import { setActiveSystem, useUpdateSystemMutation } from "./system.slice";

type FormValues = PrivacyDeclaration;

const transformFormValuesToDeclaration = (
  formValues: FormValues
): PrivacyDeclaration => ({
  ...formValues,
  // Fill in an empty string for name because of https://github.com/ethyca/fideslang/issues/98
  name: formValues.name ?? "",
});

interface Props {
  system: System;
}

const PrivacyDeclarationStep = ({ system }: Props) => {
  const toast = useToast();
  const dispatch = useAppDispatch();
  const [updateSystemMutationTrigger, { isLoading }] =
    useUpdateSystemMutation();
  // There's a step when going from empty state to the intial form
  const [showInitialForm, setShowInitialForm] = useState(false);
  const [initialDeclaration, setInitialDeclaration] = useState<
    PrivacyDeclaration | undefined
  >(undefined);

  const accordionDeclarations = useMemo(
    () => system.privacy_declarations,
    [system]
  );

  const save = async (updatedDeclarations: PrivacyDeclaration[]) => {
    const transformedDeclarations = updatedDeclarations.map((d) =>
      transformFormValuesToDeclaration(d)
    );
    const systemBodyWithDeclaration = {
      ...system,
      privacy_declarations: transformedDeclarations,
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

        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Data use case saved"));
        toast.closeAll();
        dispatch(setActiveSystem(result.data));
      }
    };

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration
    );

    handleResult(updateSystemResult);
  };

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclaration,
    newDeclaration: PrivacyDeclaration
  ) => {
    // Because the data use can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    const updatedDeclarations = accordionDeclarations.map((dec) =>
      dec.data_use === oldDeclaration.data_use ? newDeclaration : dec
    );
    await save(updatedDeclarations);
  };

  const saveNewDeclaration = async (values: PrivacyDeclaration) => {
    if (
      accordionDeclarations.filter((d) => d.data_use === values.data_use)
        .length > 0
    ) {
      toast(
        errorToastParams(
          "A declaration already exists with that data use in this system. Please supply a different data use."
        )
      );
    } else {
      toast.closeAll();
      setInitialDeclaration(values);
      const updatedDeclarations = [...accordionDeclarations, values];
      await save(updatedDeclarations);
      setShowInitialForm(false);
      setInitialDeclaration(undefined);
    }
  };

  const showAddDataUseButton = !showInitialForm;

  return (
    <Stack spacing={3}>
      <Heading as="h3" size="md">
        Data uses
      </Heading>
      <Text fontSize="sm">
        Data Uses describe the business purpose for which the personal data is
        processed or collected. Within a Data Use, you assign which categories
        of personal information are collected for this purpose and for which
        categories of data subjects. To update the available categories and
        uses, please visit{" "}
        <NextLink href="/taxonomy" passHref>
          <Text as="a" color="complimentary.600">
            Manage taxonomy
          </Text>
        </NextLink>
        .
      </Text>
      {accordionDeclarations.map((declaration) => (
        <Box key={declaration.data_use}>
          <PrivacyDeclarationAccordion
            privacyDeclaration={declaration}
            onEdit={(newValues) => {
              handleEditDeclaration(declaration, newValues);
            }}
          />
          <Divider m="0px !important" />
        </Box>
      ))}
      {showInitialForm ? (
        <Box backgroundColor="gray.50" p={6}>
          <ConnectedPrivacyDeclarationForm
            initialValues={initialDeclaration}
            onSubmit={saveNewDeclaration}
            withHeader
          />
        </Box>
      ) : null}
      {showAddDataUseButton ? (
        <Box py={2}>
          <Button
            colorScheme="primary"
            size="xs"
            isLoading={isLoading}
            data-testid="save-btn"
            onClick={() => setShowInitialForm(true)}
          >
            Add a Data Use +
          </Button>
        </Box>
      ) : null}
    </Stack>
  );
};

export default PrivacyDeclarationStep;
