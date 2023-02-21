import {
  Box,
  Button,
  Heading,
  Stack,
  Text,
  Tooltip,
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

  const [showNewForm, setShowNewForm] = useState(false);
  const [newDeclaration, setNewDeclaration] = useState<
    PrivacyDeclaration | undefined
  >(undefined);

  const accordionDeclarations = useMemo(() => {
    if (!newDeclaration) {
      return system.privacy_declarations;
    }
    return system.privacy_declarations.filter(
      (pd) => pd.data_use !== newDeclaration.data_use
    );
  }, [newDeclaration, system]);

  const checkAlreadyExists = (values: PrivacyDeclaration) => {
    if (
      accordionDeclarations.filter((d) => d.data_use === values.data_use)
        .length > 0
    ) {
      toast(
        errorToastParams(
          "A declaration already exists with that data use in this system. Please supply a different data use."
        )
      );
      return true;
    }
    return false;
  };

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
        return false;
      }
      toast.closeAll();
      toast(successToastParams("Data use case saved"));
      dispatch(setActiveSystem(result.data));
      return true;
    };

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration
    );

    return handleResult(updateSystemResult);
  };

  const handleEditDeclaration = async (
    oldDeclaration: PrivacyDeclaration,
    updatedDeclaration: PrivacyDeclaration
  ) => {
    // Do not allow editing a privacy declaration to have the same data use as one that already exists
    if (
      updatedDeclaration.data_use !== oldDeclaration.data_use &&
      checkAlreadyExists(updatedDeclaration)
    ) {
      return false;
    }
    // Because the data use can change, we also need a reference to the old declaration in order to
    // make sure we are replacing the proper one
    const updatedDeclarations = accordionDeclarations.map((dec) =>
      dec.data_use === oldDeclaration.data_use ? updatedDeclaration : dec
    );
    const success = await save(updatedDeclarations);
    return success;
  };

  const saveNewDeclaration = async (values: PrivacyDeclaration) => {
    if (checkAlreadyExists(values)) {
      return false;
    }

    toast.closeAll();
    setNewDeclaration(values);
    const updatedDeclarations = [...accordionDeclarations, values];
    const success = await save(updatedDeclarations);
    return success;
  };

  const handleShowNewForm = () => {
    setShowNewForm(true);
    setNewDeclaration(undefined);
  };

  const showAddDataUseButton =
    system.privacy_declarations.length > 0 ||
    (system.privacy_declarations.length === 0 && !showNewForm);

  return (
    <Stack spacing={3} data-testid="privacy-declaration-step">
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
      <PrivacyDeclarationAccordion
        privacyDeclarations={accordionDeclarations}
        onEdit={handleEditDeclaration}
      />
      {showNewForm ? (
        <Box backgroundColor="gray.50" p={6} data-testid="new-declaration-form">
          <ConnectedPrivacyDeclarationForm
            initialValues={newDeclaration}
            onSubmit={saveNewDeclaration}
          />
        </Box>
      ) : null}
      {showAddDataUseButton ? (
        <Box py={2}>
          <Tooltip
            label="Add another use case"
            hasArrow
            placement="top"
            isDisabled={accordionDeclarations.length === 0}
          >
            <Button
              colorScheme="primary"
              size="xs"
              isLoading={isLoading}
              data-testid="add-btn"
              onClick={handleShowNewForm}
              disabled={showNewForm && !newDeclaration}
            >
              Add a Data Use +
            </Button>
          </Tooltip>
        </Box>
      ) : null}
    </Stack>
  );
};

export default PrivacyDeclarationStep;
