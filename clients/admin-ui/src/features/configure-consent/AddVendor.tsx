import {
  Box,
  Button,
  ButtonGroup,
  useDisclosure,
  useToast,
  VStack,
} from "@fidesui/react";
import { Form, Formik, FormikHelpers } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  CustomCreatableSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
} from "~/features/plus/plus.slice";
import {
  useCreateSystemMutation,
  useUpdateSystemMutation,
} from "~/features/system";
import { System } from "~/types/api";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import AddModal from "./AddModal";
import { EMPTY_DECLARATION, FormValues } from "./constants";
import DataUsesForm from "./DataUsesForm";

const defaultInitialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  privacy_declarations: [EMPTY_DECLARATION],
};

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Vendor name"),
});

const DictionaryValidationSchema = Yup.object().shape({
  vendor_id: Yup.string().required().label("Vendor"),
});

const AddVendor = ({
  passedInSystem,
  onCloseModal,
}: {
  passedInSystem?: System;
  onCloseModal?: () => void;
}) => {
  const defaultModal = useDisclosure();
  const modal = {
    ...defaultModal,
    isOpen: passedInSystem ? true : defaultModal.isOpen,
  };
  const toast = useToast();

  // Subscribe and get dictionary values
  const features = useFeatures();
  const { dictionaryService: hasDictionary } = features;
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !hasDictionary,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);

  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
  const [isShowingSuggestions, setIsShowingSuggestions] = useState(false);

  const handleCloseModal = () => {
    modal.onClose();
    if (onCloseModal) {
      onCloseModal();
    }
    setIsShowingSuggestions(false);
  };

  const initialValues = passedInSystem
    ? {
        name: passedInSystem.name ?? "",
        vendor_id: passedInSystem.vendor_id,
        privacy_declarations: passedInSystem.privacy_declarations.map(
          (dec) => ({
            ...dec,
            name: dec.name ?? "",
            cookies: dec.cookies ?? [],
            cookieNames: dec.cookies ? dec.cookies.map((c) => c.name) : [],
          })
        ),
      }
    : defaultInitialValues;

  const handleSubmit = async (
    values: FormValues,
    helpers: FormikHelpers<FormValues>
  ) => {
    const transformedDeclarations = values.privacy_declarations
      .filter((dec) => dec.data_use !== EMPTY_DECLARATION.data_use)
      .map((dec) => {
        // if a cookie from the form already exists on the declaration with full
        // information from the dictionary, use that; otherwise, make the cookie
        // name from the form into a new cookie
        const transformedCookies = dec.cookieNames.map((name) => {
          const existingCookie = dec.cookies.find((c) => c.name === name);
          return existingCookie ?? { name, path: "/" };
        });

        const { cookieNames, ...rest } = dec;
        return { ...rest, cookies: transformedCookies };
      });

    // We use vendor_id to potentially store a new system name
    // so now we need to clear out vendor_id if it's not a system in the dictionary
    const vendor = dictionaryOptions.find((o) => o.value === values.vendor_id);
    const vendorId = vendor ? vendor.value : undefined;
    let { name: newName } = values;
    if (vendor) {
      newName = vendor.label;
    } else if (values.vendor_id) {
      // This is the case where the user created their own vendor name
      newName = values.vendor_id;
    }

    const payload = {
      vendor_id: vendorId,
      name: passedInSystem ? passedInSystem.name : newName,
      fides_key: passedInSystem ? passedInSystem.fides_key : formatKey(newName),
      system_type: "",
      privacy_declarations: transformedDeclarations,
    };

    const result = passedInSystem
      ? await updateSystemMutationTrigger(payload)
      : await createSystemMutationTrigger(payload);

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(
      successToastParams(
        `Vendor successfully ${passedInSystem ? "updated" : "created"}!`
      )
    );
    helpers.resetForm();
    handleCloseModal();
  };

  const validationSchema = hasDictionary
    ? DictionaryValidationSchema
    : ValidationSchema;

  return (
    <>
      <Button
        onClick={modal.onOpen}
        data-testid="add-vendor-btn"
        size="sm"
        colorScheme="primary"
      >
        Add vendor
      </Button>
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ dirty, values, isValid, resetForm }) => {
          let suggestionsState;
          if (values.vendor_id == null) {
            suggestionsState = "disabled" as const;
          } else if (isShowingSuggestions) {
            suggestionsState = "showing" as const;
          }
          return (
            <AddModal
              isOpen={modal.isOpen}
              onClose={modal.onClose}
              title={passedInSystem ? "Edit vendor" : "Add a vendor"}
              onSuggestionClick={() => {
                setIsShowingSuggestions(true);
              }}
              suggestionsState={suggestionsState}
            >
              <Box data-testid="add-vendor-modal-content" my={4}>
                <Form>
                  <VStack alignItems="start" spacing={6}>
                    {hasDictionary ? (
                      <CustomCreatableSelect
                        id="vendor"
                        name="vendor_id"
                        label="Vendor"
                        placeholder="Select a vendor"
                        singleValueBlock
                        options={dictionaryOptions}
                        tooltip="Select the vendor that matches the system"
                        isCustomOption
                        variant="stacked"
                        isDisabled={!!passedInSystem}
                        isRequired
                      />
                    ) : null}
                    {(passedInSystem && !passedInSystem.vendor_id) ||
                    !hasDictionary ? (
                      <CustomTextInput
                        id="name"
                        name="name"
                        isRequired
                        label="Vendor name"
                        tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                        variant="stacked"
                        disabled={!!passedInSystem}
                      />
                    ) : null}
                    <DataUsesForm showSuggestions={isShowingSuggestions} />
                    <ButtonGroup
                      size="sm"
                      width="100%"
                      justifyContent="space-between"
                    >
                      <Button
                        variant="outline"
                        onClick={() => {
                          handleCloseModal();
                          resetForm();
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        variant="primary"
                        isDisabled={isLoading || !dirty || !isValid}
                        isLoading={isLoading}
                        data-testid="save-btn"
                      >
                        Save vendor
                      </Button>
                    </ButtonGroup>
                  </VStack>
                </Form>
              </Box>
            </AddModal>
          );
        }}
      </Formik>
    </>
  );
};

export default AddVendor;
