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
import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
} from "~/features/plus/plus.slice";
import { useCreateSystemMutation } from "~/features/system";

import { getErrorMessage, isErrorResult } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import AddModal from "./AddModal";
import { EMPTY_DECLARATION, FormValues } from "./constants";
import DataUsesForm from "./DataUsesForm";

const initialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  // TODO(fides#4059): data categories will eventually be optional
  privacy_declarations: [EMPTY_DECLARATION],
};

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Vendor name"),
});

const DictionaryValidationSchema = Yup.object().shape({
  vendor_id: Yup.string().required().label("Vendor"),
});

const AddVendor = () => {
  const modal = useDisclosure();
  const toast = useToast();

  // Subscribe and get dictionary values
  const features = useFeatures();
  const { dictionaryService: hasDictionary } = features;
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !hasDictionary,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);

  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const [isShowingSuggestions, setIsShowingSuggestions] = useState(false);

  const handleSubmit = async (
    values: FormValues,
    helpers: FormikHelpers<FormValues>
  ) => {
    const transformedDeclarations = values.privacy_declarations
      .filter((dec) => dec.data_use !== EMPTY_DECLARATION.data_use)
      .map((dec) => {
        const transformedCookies = dec.cookies.map((name) => ({
          name,
          path: "/",
        }));
        return { ...dec, cookies: transformedCookies };
      });

    const name =
      dictionaryOptions.find((o) => o.value === values.vendor_id)?.label ??
      values.name;

    const payload = {
      ...values,
      name,
      fides_key: formatKey(name),
      system_type: "",
      privacy_declarations: transformedDeclarations,
    };
    const result = await createSystemMutationTrigger(payload);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }
    toast(successToastParams("Vendor successfully added!"));
    helpers.resetForm();
    modal.onClose();
  };

  const validationSchema = hasDictionary
    ? DictionaryValidationSchema
    : ValidationSchema;

  return (
    <>
      <Button onClick={modal.onOpen} data-testid="add-vendor-btn">
        Add vendor
      </Button>
      <Formik
        initialValues={initialValues}
        enableReinitialize
        onSubmit={handleSubmit}
        validationSchema={validationSchema}
      >
        {({ dirty, values, isValid, resetForm }) => (
          <AddModal
            isOpen={modal.isOpen}
            onClose={modal.onClose}
            title="Add a vendor"
            onSuggestionClick={() => {
              setIsShowingSuggestions(true);
            }}
            suggestionsDisabled={values.vendor_id == null}
          >
            <Box data-testid="add-vendor-modal-content">
              <Form>
                <VStack alignItems="start">
                  {hasDictionary ? (
                    <CustomSelect
                      id="vendor"
                      name="vendor_id"
                      label="Vendor"
                      placeholder="Select a vendor"
                      singleValueBlock
                      options={dictionaryOptions}
                      tooltip="Select the vendor that matches the system"
                      isCustomOption
                      variant="stacked"
                      isRequired
                    />
                  ) : (
                    <CustomTextInput
                      id="name"
                      name="name"
                      isRequired
                      label="Vendor name"
                      tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                      variant="stacked"
                    />
                  )}
                  <DataUsesForm showSuggestions={isShowingSuggestions} />
                  <ButtonGroup
                    size="sm"
                    width="100%"
                    justifyContent="space-between"
                  >
                    <Button
                      variant="outline"
                      onClick={() => {
                        modal.onClose();
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
        )}
      </Formik>
    </>
  );
};

export default AddVendor;
