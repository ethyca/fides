import {
  Button,
  CompassIcon,
  Dropdown,
  Flex,
  Form,
  FormRule,
  Icons,
  Input,
  MenuProps,
  Select,
} from "fidesui";
import { KeyboardEvent, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { AutosuggestSuffix } from "~/features/common/AutosuggestSuffix";
import { DictOption as VendorOption } from "~/features/plus/plus.slice";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";

const NEW_SYSTEM_PREFIX = "Create new system";

const CompassButton = ({
  active,
  disabled,
  onRefreshSuggestions,
}: {
  active: boolean;
  disabled: boolean;
  onRefreshSuggestions: () => void;
}) => {
  const items: MenuProps["items"] = useMemo(
    () => [
      {
        key: "reset",
        label: "Reset to Compass defaults",
        onClick: onRefreshSuggestions,
      },
    ],
    [onRefreshSuggestions],
  );

  return (
    <Dropdown menu={{ items }} disabled={disabled}>
      <Button
        icon={<CompassIcon />}
        aria-label="Update information from Compass"
        data-testid="refresh-suggestions-btn"
        disabled={disabled}
        type={active ? "primary" : undefined}
      />
    </Dropdown>
  );
};

export interface VendorSelectorAntProps {
  label: string;
  isCreate: boolean;
  lockedForGVL: boolean;
  options: VendorOption[];
  isLoading?: boolean;
  onVendorSelected: (vendorId?: string | null) => void;
  /**
   * Validation rules applied to the `name` field (e.g. uniqueness check).
   * Forwarded to the wrapped `Form.Item`.
   */
  nameRules?: FormRule[];
}

/**
 * antd-Form-native vendor name typeahead. Drop-in inside any antd `Form`
 * that exposes `name: string` and `vendor_id?: string` on its values.
 *
 * Forked from `VendorSelector.tsx`, which is still consumed by the
 * Formik-based `AddNewSystemModal` and `SystemInformationForm`. When those
 * migrate, swap their imports here and delete the Formik original.
 */
const VendorSelectorAnt = ({
  label,
  isCreate,
  lockedForGVL,
  options,
  isLoading,
  onVendorSelected,
  nameRules,
}: VendorSelectorAntProps) => {
  const form = Form.useFormInstance();
  const dictSuggestionsState = useAppSelector(selectSuggestions);
  const name = Form.useWatch<string | undefined>("name", form);
  const vendorId = Form.useWatch<string | undefined>("vendor_id", form);

  const [isTypeahead, setIsTypeahead] = useState(true);
  const [searchParam, setSearchParam] = useState<string>("");

  const filterFunction = (searchText: string, option?: VendorOption) =>
    !!option?.label.toLowerCase().startsWith(searchText.toLowerCase());

  const suggestions = useMemo(
    () => options.filter((o) => filterFunction(searchParam, o)),
    [options, searchParam],
  );

  const optionsWithCustom = useMemo(() => {
    if (isCreate && searchParam) {
      return [
        ...options,
        {
          label: `${NEW_SYSTEM_PREFIX} "${searchParam}"...`,
          value: searchParam,
        },
      ];
    }
    return options;
  }, [isCreate, options, searchParam]);

  const hasVendorSuggestions = !!searchParam && suggestions.length > 0;
  const nameFieldLockedForGVL = lockedForGVL && !isCreate;

  useEffect(() => {
    setIsTypeahead(!name && !vendorId);
  }, [name, vendorId]);

  const selectedOption = useMemo(() => {
    const match = options.find((o) => o.value === name);
    if (match) {
      return match;
    }
    if (!name) {
      return undefined;
    }
    return { label: name, value: name, description: "" } as VendorOption;
  }, [options, name]);

  const handleClear = () => {
    setSearchParam("");
    form.setFieldsValue({ name: "", vendor_id: undefined });
    form.validateFields(["name"]).catch(() => {});
    onVendorSelected(undefined);
  };

  const handleChange = (newValue: VendorOption | undefined) => {
    if (!newValue) {
      return;
    }
    const newVendorId = options.some((opt) => opt.value === newValue.value)
      ? newValue.value
      : undefined;
    const newName = newValue.label.startsWith(NEW_SYSTEM_PREFIX)
      ? newValue.value
      : newValue.label;
    form.setFieldsValue({ name: newName, vendor_id: newVendorId });
    form.validateFields(["name"]).catch(() => {});
    onVendorSelected(newVendorId);
  };

  // Accept typed value as the name on blur if nothing was picked.
  const handleBlur = () => {
    if (searchParam) {
      form.setFieldValue("name", searchParam);
    }
    form.validateFields(["name"]).catch(() => {});
  };

  // Tab completes the autosuggest.
  const handleTabPressed = (
    event: KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    if (suggestions.length > 0 && searchParam !== suggestions[0].label) {
      event.preventDefault();
      const [topSuggestion] = suggestions;
      setSearchParam(topSuggestion.label);
      form.setFieldsValue({
        name: topSuggestion.label,
        vendor_id: topSuggestion.value,
      });
      onVendorSelected(topSuggestion.value);
    } else {
      form.setFieldsValue({ name: searchParam, vendor_id: undefined });
    }
  };

  // Standalone typeahead UI — bypasses Form.Item value injection (Select uses
  // labelInValue, which is shaped { label, value } rather than a plain string).
  // The hidden Form.Item below registers `name` so rules and validation still
  // apply.
  const typeaheadSelect = (
    <Flex vertical align="stretch" gap="small" className="w-full">
      <Form.Item
        label={label}
        tooltip="Enter the system name"
        required
        validateStatus={undefined}
        htmlFor="vendorName"
        className="mb-0"
      >
        <div className="relative">
          <Select<VendorOption, VendorOption>
            id="vendorName"
            labelInValue
            autoFocus
            allowClear
            options={optionsWithCustom}
            loading={isLoading}
            filterOption={(value, option) =>
              filterFunction(value, option) ||
              !!option?.label.startsWith(NEW_SYSTEM_PREFIX)
            }
            optionFilterProp="label"
            value={selectedOption}
            placeholder="Enter system name..."
            aria-label="Select a system"
            disabled={nameFieldLockedForGVL}
            onChange={handleChange}
            onSearch={setSearchParam}
            onClear={handleClear}
            onBlur={handleBlur}
            onInputKeyDown={(e) => {
              if (searchParam && e.key === "Tab") {
                handleTabPressed(e);
              }
            }}
            data-testid="vendor-name-select"
          />
          <AutosuggestSuffix
            searchText={searchParam}
            suggestion={suggestions.length ? suggestions[0].label : ""}
          />
        </div>
      </Form.Item>
    </Flex>
  );

  const textInput = (
    <Form.Item
      label="System name"
      tooltip="Enter the system name"
      required
      htmlFor="vendorNameInput"
      className="mb-0 w-full"
    >
      <Input
        id="vendorNameInput"
        value={name ?? ""}
        onChange={(e) => form.setFieldValue("name", e.target.value)}
        autoFocus
        disabled={nameFieldLockedForGVL}
        suffix={
          !nameFieldLockedForGVL ? (
            <Button
              type="text"
              size="small"
              icon={<Icons.Close />}
              onClick={handleClear}
              aria-label="Clear vendor name"
              data-testid="clear-btn"
            />
          ) : undefined
        }
      />
    </Form.Item>
  );

  return (
    <>
      {/*
        Always-mounted hidden fields so Form.useWatch stays reactive across
        both the typeahead and text-input branches above. Without these, the
        registered Form.Item for "name" would unmount when the user picks an
        option and the UI flips from Select → Input, and "vendor_id" has no
        visible Form.Item at all.
      */}
      <Form.Item name="name" rules={nameRules} noStyle>
        <Input type="hidden" />
      </Form.Item>
      <Form.Item name="vendor_id" noStyle>
        <Input type="hidden" />
      </Form.Item>
      <Flex align="flex-end" gap="small" className="w-full">
        {isTypeahead ? typeaheadSelect : textInput}
        <CompassButton
          active={!!vendorId || hasVendorSuggestions}
          disabled={!vendorId || dictSuggestionsState === "showing"}
          onRefreshSuggestions={() => onVendorSelected(vendorId)}
        />
      </Flex>
    </>
  );
};

export default VendorSelectorAnt;
