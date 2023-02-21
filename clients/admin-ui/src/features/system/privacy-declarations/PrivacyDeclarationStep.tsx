import { Heading, Spinner, Stack, Text, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import NextLink from "next/link";

import { useAppDispatch } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { setActiveSystem, useUpdateSystemMutation } from "~/features/system";
import { PrivacyDeclaration, System } from "~/types/api";

import { useTaxonomyData } from "./PrivacyDeclarationForm";
import PrivacyDeclarationManager from "./PrivacyDeclarationManager";

interface Props {
  system: System;
}

const PrivacyDeclarationStep = ({ system }: Props) => {
  const toast = useToast();
  const dispatch = useAppDispatch();
  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
  const { isLoading, ...dataProps } = useTaxonomyData();

  const handleSave = async (updatedDeclarations: PrivacyDeclaration[]) => {
    const systemBodyWithDeclaration = {
      ...system,
      privacy_declarations: updatedDeclarations,
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

  const collisionWarning = () => {
    toast(
      errorToastParams(
        "A declaration already exists with that data use in this system. Please supply a different data use."
      )
    );
  };

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
      {isLoading ? (
        <Spinner />
      ) : (
        <PrivacyDeclarationManager
          system={system}
          onCollision={collisionWarning}
          onSave={handleSave}
          {...dataProps}
        />
      )}
    </Stack>
  );
};

export default PrivacyDeclarationStep;
