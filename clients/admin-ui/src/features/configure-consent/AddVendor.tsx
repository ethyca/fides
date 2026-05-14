import {
  Button,
  ButtonProps,
  Flex,
  Form,
  FormRule,
  Input,
  Modal,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import {
  selectAllDictEntries,
  selectDictEntry,
  useGetAllDictionaryEntriesQuery,
} from "~/features/plus/plus.slice";
import {
  useCreateSystemMutation,
  useLazyGetSystemsQuery,
} from "~/features/system";
import {
  selectLockedForGVL,
  selectSuggestions,
  setLockedForGVL,
  setSuggestions,
} from "~/features/system/dictionary-form/dict-suggestion.slice";
import GVLNotice from "~/features/system/GVLNotice";
import VendorSelectorAnt from "~/features/system/VendorSelectorAnt";
import { System } from "~/types/api";

import {
  extractVendorSource,
  getErrorMessage,
  isErrorResult,
  VendorSources,
} from "../common/helpers";
import { EMPTY_DECLARATION, FormValues } from "./constants";
import DataUsesForm from "./DataUsesForm";

const defaultInitialValues: FormValues = {
  name: "",
  vendor_id: undefined,
  privacy_declarations: [EMPTY_DECLARATION],
};

const AddVendor = ({
  buttonLabel,
  onButtonClick,
  buttonProps,
}: {
  buttonLabel?: string;
  onButtonClick?: () => void;
  buttonProps?: ButtonProps;
}) => {
  const message = useMessage();
  const [isOpen, setIsOpen] = useState(false);
  const [form] = Form.useForm<FormValues>();
  const dispatch = useAppDispatch();

  const [getSystemQueryTrigger] = useLazyGetSystemsQuery();

  // Subscribe and get dictionary values
  const { tcf, dictionaryService } = useFeatures();
  const { isLoading } = useGetAllDictionaryEntriesQuery(undefined, {
    skip: !dictionaryService,
  });
  const dictionaryOptions = useAppSelector(selectAllDictEntries);
  const lockedForGVL = useAppSelector(selectLockedForGVL);

  const [createSystemMutationTrigger] = useCreateSystemMutation();
  const suggestionsState = useAppSelector(selectSuggestions);

  // Track form state for the Save button enable/disable.
  const watchedValues = Form.useWatch([], form);
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

  const watchedVendorId = Form.useWatch<string | undefined>("vendor_id", form);
  const dictEntry = useAppSelector(selectDictEntry(watchedVendorId || ""));

  const nameRules: FormRule[] = useMemo(
    () => [
      { required: true, message: "Vendor name is a required field" },
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
              `You already have a vendor called "${value}". Please specify a unique name for this vendor.`,
            );
          }
        },
      },
    ],
    [getSystemQueryTrigger],
  );

  const handleCloseModal = () => {
    setIsOpen(false);
    form.resetFields();
    dispatch(setSuggestions("initial"));
    dispatch(setLockedForGVL(false));
  };

  const handleSubmit = async () => {
    // Read the full form store, not just registered Form.Item fields. Each
    // privacy declaration carries `name` and `data_categories` that aren't
    // bound to a visible Form.Item but are required by the backend.
    const values = form.getFieldsValue(true) as FormValues;
    const transformedDeclarations = values.privacy_declarations
      .filter((dec) => dec.consent_use !== EMPTY_DECLARATION.consent_use)
      .flatMap((dec) => {
        // Convert the UI's cookieNames (string[]) into the API's cookies
        // shape. If the dictionary populated full cookie objects, keep the
        // match so domain/path survive; for user-typed names, default
        // `path: "/"`.
        // eslint-disable-next-line @typescript-eslint/naming-convention
        const { consent_use, cookieNames, cookies, ...rest } = dec;
        const cookiesByName = new Map((cookies ?? []).map((c) => [c.name, c]));
        const transformedCookies = (cookieNames ?? []).map(
          (name) => cookiesByName.get(name) ?? { name, path: "/" },
        );
        const base = { ...rest, cookies: transformedCookies };

        // for "marketing", we create two data uses on the backend
        if (dec.consent_use === "marketing" && !dec.data_use) {
          return [
            "marketing.advertising.first_party.targeted",
            "marketing.advertising.third_party.targeted",
          ].map((dataUse) => ({
            ...base,
            data_use: dataUse,
          }));
        }
        return {
          ...base,
          data_use: dec.data_use ? dec.data_use : dec.consent_use!,
        };
      });

    const payload = {
      ...dictEntry,
      ...values,
      fides_key: formatKey(values.name),
      system_type: "",
      privacy_declarations: transformedDeclarations,
    } as System;

    const result = await createSystemMutationTrigger(payload);

    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
      return;
    }
    message.success("Vendor successfully created!");
    handleCloseModal();
  };

  const handleVendorSelected = (vendorId?: string | null) => {
    if (!dictionaryService) {
      return;
    }
    if (!vendorId) {
      dispatch(setSuggestions("hiding"));
      dispatch(setLockedForGVL(false));
      return;
    }
    dispatch(setSuggestions("showing"));
    if (tcf && extractVendorSource(vendorId) === VendorSources.GVL) {
      dispatch(setLockedForGVL(true));
    } else {
      dispatch(setLockedForGVL(false));
    }
  };

  const handleOpenButtonClicked = () => {
    if (onButtonClick) {
      onButtonClick();
    } else {
      setIsOpen(true);
    }
  };

  return (
    <>
      <Button
        onClick={handleOpenButtonClicked}
        data-testid="add-vendor-btn"
        {...buttonProps}
      >
        {buttonLabel}
      </Button>
      <Modal
        open={isOpen}
        onCancel={handleCloseModal}
        centered
        destroyOnHidden
        title="Add a vendor"
        footer={
          <Flex justify="space-between">
            <Button onClick={handleCloseModal}>Cancel</Button>
            <Button
              type="primary"
              onClick={() => form.submit()}
              disabled={isLoading || !submittable}
              loading={isLoading}
              data-testid="save-btn"
            >
              Save vendor
            </Button>
          </Flex>
        }
      >
        <div data-testid="add-vendor-modal-content">
          {lockedForGVL ? <GVLNotice /> : null}
          <Form<FormValues>
            form={form}
            initialValues={defaultInitialValues}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Flex vertical gap="middle" align="stretch">
              {dictionaryService ? (
                <VendorSelectorAnt
                  label="Vendor name"
                  options={dictionaryOptions}
                  isLoading={isLoading}
                  onVendorSelected={handleVendorSelected}
                  isCreate
                  lockedForGVL={lockedForGVL}
                  nameRules={nameRules}
                />
              ) : (
                <Form.Item
                  name="name"
                  label="Vendor name"
                  required
                  tooltip='Give the system a unique, and relevant name for reporting purposes. e.g. "Email Data Warehouse"'
                  rules={nameRules}
                  className="mb-0"
                >
                  <Input data-testid="input-name" />
                </Form.Item>
              )}
              <DataUsesForm
                showSuggestions={suggestionsState === "showing"}
                isCreate
                disabled={lockedForGVL}
              />
            </Flex>
          </Form>
        </div>
      </Modal>
    </>
  );
};

export default AddVendor;
