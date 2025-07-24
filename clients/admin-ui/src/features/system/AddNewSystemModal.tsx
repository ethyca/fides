import {
  AntButton as Button,
  AntFlex as Flex,
  AntTypography as Typography,
  ModalProps,
} from "fidesui";
import { Form, Formik } from "formik";
import { useMemo, useRef, useState } from "react";
import * as Yup from "yup";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { System } from "~/types/api";

import { useFeatures } from "../common/features";
import { ControlledSelect } from "../common/form/ControlledSelect";
import { CustomTextInput } from "../common/form/inputs";
import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  VendorSources,
} from "../common/helpers";
import { useAlert } from "../common/hooks";
import { FormGuard } from "../common/hooks/useIsAnyFormDirty";
import FormModal from "../common/modals/FormModal";
import { formatKey } from "../datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  useGetAllDictionaryEntriesQuery,
  usePostSystemVendorsMutation,
} from "../plus/plus.slice";
import {
  dictSuggestionsSlice,
  selectLockedForGVL,
} from "./dictionary-form/dict-suggestion.slice";
import { DictSuggestionTextArea } from "./dictionary-form/DictSuggestionInputs";
import {
  useCreateSystemMutation,
  useLazyGetSystemsQuery,
} from "./system.slice";
import VendorSelector from "./VendorSelector";

const { Text } = Typography;

export interface FormValues {
  name: string;
  vendor_id?: string;
  description: string;
  tags: string[];
}

const defaultInitialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  description: "",
  tags: [],
};

interface AddNewSystemModalProps extends Omit<ModalProps, "children"> {
  onSuccessfulSubmit?: (fidesKey: string, newSystemName: string) => void;
  toastOnSuccess?: boolean;
}
export const AddNewSystemModal = ({
  onSuccessfulSubmit,
  toastOnSuccess,
  ...props
}: AddNewSystemModalProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const dispatch = useAppDispatch();
  const { tcf, dictionaryService } = useFeatures();
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !dictionaryService,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);
  const lockedForGVL = useAppSelector(selectLockedForGVL);
  const [getSystemQueryTrigger] = useLazyGetSystemsQuery();
  const [postVendorIds] = usePostSystemVendorsMutation();
  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const { successAlert, errorAlert } = useAlert();

  const { setSuggestions, setLockedForGVL } = dictSuggestionsSlice.actions;

  const formRef = useRef(null);

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        name: Yup.string()
          .required()
          .label("System name")
          .test("is-unique", "", async (value, context) => {
            const { data } = await getSystemQueryTrigger({
              page: 1,
              size: 10,
              search: value,
            });
            const systemResults = data?.items || [];
            const similarSystemNames = systemResults.filter(
              (s) => s.name === value,
            );
            if (similarSystemNames.some((s) => s.name === value)) {
              return context.createError({
                message: `You already have a system called "${value}". Please specify a unique name for this system.`,
              });
            }
            return true;
          }),
      }),
    [getSystemQueryTrigger],
  );

  const handleVendorSelected = (newVendorId?: string | null) => {
    if (!dictionaryService) {
      return;
    }
    if (!newVendorId) {
      dispatch(setSuggestions("hiding"));
      dispatch(setLockedForGVL(false));
      return;
    }
    dispatch(setSuggestions("showing"));
    if (tcf && extractVendorSource(newVendorId) === VendorSources.GVL) {
      dispatch(setLockedForGVL(true));
    } else {
      dispatch(setLockedForGVL(false));
    }
  };

  const handleCloseModal = () => {
    props.onClose();
    dispatch(setSuggestions("initial"));
    dispatch(setLockedForGVL(false));
  };

  const handleSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    if (values.vendor_id) {
      const result = await postVendorIds([values.vendor_id]);
      if (isErrorResult(result)) {
        errorAlert(getErrorMessage(result.error));
      } else {
        const { data } = result;
        const newSystem = data.systems[0];
        onSuccessfulSubmit?.(newSystem.fides_key, newSystem.name);
        if (toastOnSuccess) {
          successAlert(`${data.name} has been added to your system inventory.`);
        }
      }
    } else {
      const payload = {
        ...values,
        fides_key: formatKey(values.name),
        system_type: "",
        body: "",
        privacy_declarations: [],
      } as System;

      const result = await createSystemMutationTrigger(payload);

      if (isErrorResult(result)) {
        errorAlert(getErrorMessage(result.error));
      } else {
        const { fides_key: fidesKey, name } = result.data;
        onSuccessfulSubmit?.(fidesKey, name as string);
        if (toastOnSuccess) {
          successAlert(
            `${values.name} has been added to your system inventory.`,
          );
        }
      }
      handleCloseModal();
    }
    setIsSubmitting(false);
  };

  return (
    <FormModal title="Add New System" {...props} onClose={handleCloseModal}>
      <Formik
        initialValues={defaultInitialValues}
        onSubmit={handleSubmit}
        validationSchema={ValidationSchema}
        innerRef={formRef}
      >
        {({ dirty, isValid }) => (
          <Form>
            <FormGuard id="new-system-modal" name="Add New System" />
            <Flex vertical gap={20} className="pb-6 pt-4">
              <Text>
                Fides will add this system to your inventory and configure it
                for consent using the categories of consent listed below.
                Optionally, you can check if this system is listed within the
                Fides compass library by selecting the compass icon below.
              </Text>
              {dictionaryService ? (
                <VendorSelector
                  label="System name"
                  options={dictionaryOptions}
                  onVendorSelected={handleVendorSelected}
                  isCreate
                  lockedForGVL={lockedForGVL}
                  isLoading={isLoading}
                />
              ) : (
                <CustomTextInput
                  id="name"
                  name="name"
                  label="System name"
                  tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                  variant="stacked"
                  isRequired
                />
              )}
              <DictSuggestionTextArea
                id="description"
                name="description"
                label="Description"
                tooltip="What services does this system perform?"
                disabled={lockedForGVL}
              />
              {/* TODO [HJ-379] Add in the Categories of consent */}
              {/* TODO [HJ-373] Add in the Data steward support */}
              <ControlledSelect
                mode="tags"
                id="tags"
                name="tags"
                label="System Tags"
                options={[]}
                layout="stacked"
                tooltip="Are there any tags to associate with this system?"
                disabled={lockedForGVL}
              />
            </Flex>
            <Flex justify="space-between">
              <Button
                htmlType="reset"
                onClick={handleCloseModal}
                disabled={isLoading || !dirty || !isValid}
                data-testid="cancel-btn"
              >
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={isLoading || !dirty || !isValid}
                loading={isSubmitting}
                data-testid="save-btn"
              >
                Save
              </Button>
            </Flex>
          </Form>
        )}
      </Formik>
    </FormModal>
  );
};
