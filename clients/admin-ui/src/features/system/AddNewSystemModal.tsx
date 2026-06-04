import {
  Button,
  Flex,
  Form,
  FormRule,
  Input,
  Typography,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import ConfirmCloseModal from "~/features/common/modals/ConfirmCloseModal";
import { System } from "~/types/api";

import { useFeatures } from "../common/features";
import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  VendorSources,
} from "../common/helpers";
import { formatKey } from "../datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  selectDictEntry,
  useGetAllDictionaryEntriesQuery,
  usePostSystemVendorsMutation,
} from "../plus/plus.slice";
import {
  selectLockedForGVL,
  selectSuggestions,
  setLockedForGVL,
  setSuggestions,
} from "./dictionary-form/dict-suggestion.slice";
import { MOCK_COMPASS_VENDORS } from "./mockCompassVendors";
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

interface AddNewSystemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccessfulSubmit?: (fidesKey: string, newSystemName: string) => void;
  toastOnSuccess?: boolean;
}
export const AddNewSystemModal = ({
  isOpen,
  onClose,
  onSuccessfulSubmit,
  toastOnSuccess,
}: AddNewSystemModalProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const dispatch = useAppDispatch();
  const { tcf, dictionaryService, flags } = useFeatures();
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !dictionaryService,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);

  // The dictionary/compass service is often disabled in local dev. Behind the
  // explorer flag, fall back to mock compass vendors so the "Search Fides
  // Compass" path stays demoable; picking one creates a system tagged with its
  // vendor_id (compass-sourced), while a free-typed name creates a blank one.
  const useMockCompass = !dictionaryService && flags.webMonitorExplorer;
  const showCompassSearch = dictionaryService || useMockCompass;
  const vendorOptions = dictionaryService
    ? dictionaryOptions
    : MOCK_COMPASS_VENDORS;
  const lockedForGVL = useAppSelector(selectLockedForGVL);
  const suggestionsState = useAppSelector(selectSuggestions);
  const [getSystemQueryTrigger] = useLazyGetSystemsQuery();
  const [postVendorIds] = usePostSystemVendorsMutation();
  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const message = useMessage();

  const [form] = Form.useForm<FormValues>();

  const watchedValues = Form.useWatch([], form);
  const vendorId = Form.useWatch<string | undefined>("vendor_id", form);
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));

  const [submittable, setSubmittable] = useState(false);
  useEffect(() => {
    if (!isOpen) {
      return;
    }
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, watchedValues, isOpen]);

  // Dictionary auto-populate for the description field. Mirrors the legacy
  // `DictSuggestionTextArea` behavior without pulling in the Formik-bound
  // component.
  useEffect(() => {
    if (suggestionsState === "showing" && dictEntry?.description) {
      form.setFieldValue("description", dictEntry.description);
    }
  }, [suggestionsState, dictEntry, form]);

  const nameRules: FormRule[] = useMemo(
    () => [
      { required: true, message: "System name is a required field" },
      {
        async validator(_, value: string) {
          if (!value) {
            return;
          }
          const { data } = await getSystemQueryTrigger({
            page: 1,
            size: 10,
            search: value,
          });
          const similarSystemNames = data?.items || [];
          if (similarSystemNames.some((s) => s.name === value)) {
            throw new Error(
              `You already have a system called "${value}". Please specify a unique name for this system.`,
            );
          }
        },
      },
    ],
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
    onClose();
    form.resetFields();
    dispatch(setSuggestions("initial"));
    dispatch(setLockedForGVL(false));
  };

  const handleSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    // Only the real Compass service can mint vendor-backed systems via
    // system-vendors. With the mock path, a picked vendor_id rides along into
    // createSystem below (spread from `values`) so the system is still tagged
    // as compass-sourced offline.
    if (values.vendor_id && dictionaryService) {
      const result = await postVendorIds([values.vendor_id]);
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        const { data } = result;
        const newSystem = data.systems[0];
        onSuccessfulSubmit?.(newSystem.fides_key, newSystem.name);
        if (toastOnSuccess) {
          message.success(
            `${data.name} has been added to your system inventory.`,
          );
        }
        handleCloseModal();
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
        message.error(getErrorMessage(result.error));
      } else {
        const { fides_key: fidesKey, name } = result.data;
        onSuccessfulSubmit?.(fidesKey, name as string);
        if (toastOnSuccess) {
          message.success(
            `${values.name} has been added to your system inventory.`,
          );
        }
      }
      handleCloseModal();
    }
    setIsSubmitting(false);
  };

  return (
    <ConfirmCloseModal
      title="Add New System"
      open={isOpen}
      onClose={handleCloseModal}
      getIsDirty={() => form.isFieldsTouched()}
      centered
      data-testid="add-modal-content"
      destroyOnHidden
      footer={
        <Flex justify="space-between">
          <Button onClick={handleCloseModal} data-testid="cancel-btn">
            Cancel
          </Button>
          <Button
            type="primary"
            onClick={() => form.submit()}
            disabled={isLoading || !submittable}
            loading={isSubmitting}
            data-testid="save-btn"
          >
            Save
          </Button>
        </Flex>
      }
    >
      <Form<FormValues>
        form={form}
        initialValues={defaultInitialValues}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Flex vertical gap={20} className="pb-6 pt-4">
          <Text>
            {showCompassSearch
              ? "Select a known Compass vendor, or enter a new name to create a system in your inventory."
              : "Enter a name and save to add this system to your inventory."}
          </Text>
          {showCompassSearch ? (
            <VendorSelector
              label="Enter system name"
              options={vendorOptions}
              onVendorSelected={handleVendorSelected}
              isCreate
              lockedForGVL={lockedForGVL}
              isLoading={dictionaryService ? isLoading : false}
              nameRules={nameRules}
            />
          ) : (
            <Form.Item
              name="name"
              label="System name"
              required
              tooltip='Give the system a unique, and relevant name for reporting purposes. e.g. "Email Data Warehouse"'
              rules={nameRules}
              className="mb-0"
            >
              <Input data-testid="input-name" />
            </Form.Item>
          )}
        </Flex>
      </Form>
    </ConfirmCloseModal>
  );
};
