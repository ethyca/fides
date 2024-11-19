import {
  AntSelect as Select,
  Box,
  CloseButton,
  FormControl,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Spacer,
  Text as ChakraText,
  VStack,
} from "fidesui";
import { useField, useFormikContext } from "formik";
import { FocusEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomTextInput,
  ErrorMessage,
  Label,
} from "~/features/common/form/inputs";
import { CompassIcon } from "~/features/common/Icon/CompassIcon";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { DictOption as VendorOption } from "~/features/plus/plus.slice";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";
import { FormValues } from "~/features/system/form";

import { AutosuggestSuffix } from "../common/AutosuggestSuffix";

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
  const bgColor = { bg: active ? "complimentary.500" : "gray.100" };
  return (
    <VStack>
      <Spacer minHeight="18px" />
      <Menu>
        <MenuButton
          as={IconButton}
          size="sm"
          isDisabled={disabled}
          icon={
            <CompassIcon color={active ? "white" : "gray.700"} boxSize={4} />
          }
          aria-label="Update information from Compass"
          data-testid="refresh-suggestions-btn"
          _hover={{
            _disabled: bgColor,
          }}
          {...bgColor}
        />
        <MenuList>
          <MenuItem onClick={onRefreshSuggestions}>
            <ChakraText fontSize="xs" lineHeight={4}>
              Reset to Compass defaults
            </ChakraText>
          </MenuItem>
        </MenuList>
      </Menu>
    </VStack>
  );
};

interface VendorSelectorProps {
  label: string;
  isCreate: boolean;
  lockedForGVL: boolean;
  options: VendorOption[];
  isLoading?: boolean;
  onVendorSelected: (vendorId?: string | null) => void;
}

const VendorSelector = ({
  label,
  isCreate,
  lockedForGVL,
  options,
  isLoading,
  onVendorSelected,
}: VendorSelectorProps) => {
  const dictSuggestionsState = useAppSelector(selectSuggestions);
  const [initialField, meta, { setValue }] = useField("name");
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const { touched, values, setTouched, setFieldValue, validateForm } =
    useFormikContext<FormValues>();
  const [isTypeahead, setIsTypeahead] = useState(true);

  const selected = options.find((o) => o.value === field.value) ?? {
    label: field.value,
    value: field.value,
    description: "",
  };

  const filterFunction = (searchParam: string, option?: VendorOption) =>
    !!option?.label.toLowerCase().startsWith(searchParam.toLowerCase());

  const [searchParam, setSearchParam] = useState<string>("");

  const suggestions = useMemo(
    () => options.filter((o) => filterFunction(searchParam, o)),
    [options, searchParam],
  );

  const optionsWithCustom = useMemo(() => {
    let o = options;
    if (isCreate && searchParam) {
      o = [
        ...options,
        {
          label: `${NEW_SYSTEM_PREFIX} "${searchParam}"...`,
          value: searchParam,
        },
      ];
    }
    return o;
  }, [isCreate, options, searchParam]);
  const hasVendorSuggestions = !!searchParam && suggestions.length > 0;
  const nameFieldLockedForGVL = lockedForGVL && !isCreate;

  useEffect(() => {
    setIsTypeahead(!field.value && !values.vendor_id);
  }, [field.value, values.vendor_id, setIsTypeahead]);

  useEffect(() => {
    validateForm();
  }, [isTypeahead, validateForm]);

  const handleClear = async () => {
    setSearchParam("");
    setFieldValue("vendor_id", undefined);
    await setValue("");
    setTouched({ ...touched, vendor_id: false, name: false });
    onVendorSelected(undefined);
  };

  const handleChange = async (newValue: VendorOption) => {
    if (newValue) {
      const newVendorId = options.some((opt) => opt.value === newValue.value)
        ? newValue.value
        : undefined;
      setFieldValue("vendor_id", newVendorId);
      await setValue(
        newValue.label.startsWith(NEW_SYSTEM_PREFIX)
          ? newValue.value
          : newValue.label,
      );
      setTouched({ ...touched, vendor_id: true, name: true });
      onVendorSelected(newVendorId);
    }
  };

  // accept the value in the search input as is if it's not empty
  const handleBlur = async (event: FocusEvent) => {
    field.onBlur(event);
    if (searchParam) {
      await setValue(searchParam);
    }
    setTouched({ ...touched, name: true });
  };

  // complete the autosuggest
  const handleTabPressed = async (
    event: KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    if (suggestions.length > 0 && searchParam !== suggestions[0].label) {
      event.preventDefault();
      setSearchParam(suggestions[0].label);
      setFieldValue("vendor_id", suggestions[0].value);
      await setValue(suggestions[0].label);
      onVendorSelected(suggestions[0].value);
    } else {
      setFieldValue("vendor_id", undefined);
      await setValue(searchParam);
    }
    setTouched({ ...touched, name: true });
  };

  // we have to build the typeahead from scratch, too much context-specific
  // is needed to use the existing ControlledSelect component
  const typeaheadSelect = (
    <FormControl isInvalid={isInvalid} isRequired width="100%">
      <VStack alignItems="start" position="relative" width="100%">
        <HStack spacing={1}>
          <Label htmlFor="vendorName" fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          <QuestionTooltip label="Enter the system name" />
        </HStack>
        <Box width="100%" className="relative">
          <Select<VendorOption, VendorOption>
            id="vendorName"
            showSearch
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
            value={selected}
            placeholder="Enter system name..."
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
            status={isInvalid ? "error" : undefined}
            data-testid="vendor-name-select"
          />
          <AutosuggestSuffix
            searchText={searchParam}
            suggestion={suggestions.length ? suggestions[0].label : ""}
          />
        </Box>
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName="name"
        />
      </VStack>
    </FormControl>
  );

  return (
    <HStack alignItems="flex-start" width="full">
      {isTypeahead ? (
        typeaheadSelect
      ) : (
        <CustomTextInput
          autoFocus
          id="name"
          name="name"
          label="System name"
          tooltip="Enter the system name"
          variant="stacked"
          disabled={nameFieldLockedForGVL}
          isRequired
          inputRightElement={
            !nameFieldLockedForGVL ? (
              <CloseButton
                onClick={handleClear}
                size="sm"
                data-testid="clear-btn"
              />
            ) : null
          }
        />
      )}
      <CompassButton
        active={!!values.vendor_id || hasVendorSuggestions}
        disabled={!values.vendor_id || dictSuggestionsState === "showing"}
        onRefreshSuggestions={() => onVendorSelected(values.vendor_id)}
      />
    </HStack>
  );
};

export default VendorSelector;
