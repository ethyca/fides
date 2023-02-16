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

import { errorToastParams, successToastParams } from "../common/toast";
import PrivacyDeclarationAccordion from "./PrivacyDeclarationAccordion";
import ConnectedPrivacyDeclarationForm from "./PrivacyDeclarationForm";
import { useUpdateSystemMutation } from "./system.slice";

interface Props {
  system: System;
}

const PrivacyDeclarationStep = ({ system }: Props) => {
  const toast = useToast();
  const [accordionDeclarations, setAccordionDeclarations] = useState<
    PrivacyDeclaration[]
  >(system?.privacy_declarations ? [...system.privacy_declarations] : []);
  const [updateSystemMutationTrigger, { isLoading }] =
    useUpdateSystemMutation();
  // There's a step when going from empty state to the intial form
  const [showInitialForm, setShowInitialForm] = useState(false);
  const [initialDeclaration, setInitialDeclaration] = useState<
    PrivacyDeclaration | undefined
  >(undefined);

  const save = async (updatedDeclarations: PrivacyDeclaration[]) => {
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
        console.log({ result });

        toast(errorToastParams(errorMsg));
      } else {
        toast(successToastParams("Data use case saved"));
        toast.closeAll();
      }
    };

    console.log({ updatedDeclarations });

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

  const addDeclaration = async (
    values: PrivacyDeclaration
    // formikHelpers: FormikHelpers<PrivacyDeclaration>
  ) => {
    // const { resetForm } = formikHelpers;
    if (
      accordionDeclarations.filter((d) => d.data_use === values.data_use)
        .length > 0
    ) {
      toast({
        status: "error",
        description:
          "A declaration already exists with that name in this system. Please use a different name.",
      });
    } else {
      toast.closeAll();
      setInitialDeclaration(values);
      const updatedDeclarations = [...accordionDeclarations, values];
      // setFormDeclarations([
      //   ...formDeclarations,
      //   transformFormValuesToDeclaration(values),
      // ]);
      await save(updatedDeclarations);
      // resetForm({
      //   values: {
      //     name: "",
      //     data_subjects: [],
      //     data_categories: [],
      //     data_use: "",
      //     data_qualifier: "",
      //     dataset_references: [],
      //   },
      // });
    }
  };

  const handleAddDataUse = () => {
    if (accordionDeclarations.length === 0) {
      setShowInitialForm(true);
    } else {
      if (initialDeclaration) {
        setAccordionDeclarations([
          ...accordionDeclarations,
          initialDeclaration,
        ]);
      }
      setInitialDeclaration(undefined);
      setShowInitialForm(true);
    }
  };

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
      {showInitialForm ? (
        <Box backgroundColor="gray.50" p={6}>
          <ConnectedPrivacyDeclarationForm
            initialValues={initialDeclaration}
            onSubmit={addDeclaration}
          />
        </Box>
      ) : null}
      <Box py={2}>
        <Button
          colorScheme="primary"
          size="xs"
          isLoading={isLoading}
          data-testid="save-btn"
          onClick={handleAddDataUse}
        >
          Add a Data Use +
        </Button>
      </Box>
    </Stack>
  );
};

export default PrivacyDeclarationStep;
