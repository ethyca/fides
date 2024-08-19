import {
  ActionMeta,
  chakraComponents,
  CreatableSelect,
  GroupBase,
  OptionProps,
  SingleValue,
} from "chakra-react-select";
import {
  Box,
  CloseButton,
  Flex,
  FormControl,
  HStack,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Spacer,
  Text,
  VStack,
} from "fidesui";
import { useField, useFormikContext } from "formik";
import React, { useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomTextInput,
  ErrorMessage,
  Label,
  Option,
} from "~/features/common/form/inputs";
import { CompassIcon } from "~/features/common/Icon/CompassIcon";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { DictOption } from "~/features/plus/plus.slice";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";
import { FormValues } from "~/features/system/form";

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
            <Text fontSize="xs" lineHeight={4}>
              Reset to Compass defaults
            </Text>
          </MenuItem>
        </MenuList>
      </Menu>
    </VStack>
  );
};

interface Props {
  label: string;
  isCreate: boolean;
  lockedForGVL: boolean;
  options: DictOption[];
  onVendorSelected: (vendorId: string | undefined) => void;
}

const CustomDictOption = ({
  children,
  ...props
}: OptionProps<Option, false, GroupBase<Option>>) => (
  <chakraComponents.Option {...props} type="option">
    <Flex flexDirection="column" padding={2}>
      <Text color="gray.700" fontSize="14px" lineHeight={5} fontWeight="medium">
        {props.data.label}
      </Text>

      {props.data.description ? (
        <Text
          color="gray.500"
          fontSize="12px"
          lineHeight={4}
          fontWeight="normal"
        >
          {props.data.description}
        </Text>
      ) : null}
    </Flex>
  </chakraComponents.Option>
);

const VendorSelector = ({
  label,
  isCreate,
  lockedForGVL,
  options,
  onVendorSelected,
}: Props) => {
  const dictSuggestionsState = useAppSelector(selectSuggestions);
  const [initialField, meta, { setValue }] = useField({
    name: "name",
  });
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const { touched, values, setTouched, setFieldValue, validateForm } =
    useFormikContext<FormValues>();

  const selected = options.find((o) => o.value === field.value) ?? {
    label: field.value,
    value: field.value,
    description: "",
  };

  const [searchParam, setSearchParam] = useState<string>("");

  const suggestions = options.filter((opt) =>
    opt.label.toLowerCase().startsWith(searchParam.toLowerCase()),
  );

  const isTypeahead = !field.value && !values.vendor_id;
  const hasVendorSuggestions = !!searchParam && suggestions.length > 0;
  const nameFieldLockedForGVL = lockedForGVL && !isCreate;

  useEffect(() => {
    validateForm();
  }, [isTypeahead, validateForm]);

  const handleClear = () => {
    setValue("");
    setSearchParam("");
    setFieldValue("vendor_id", undefined);
    onVendorSelected(undefined);
  };

  const handleTabPressed = () => {
    if (!searchParam) {
      return;
    }
    if (suggestions.length > 0 && searchParam !== suggestions[0].label) {
      setSearchParam(suggestions[0].label);
      setValue(suggestions[0].value);
    }
  };

  const handleSelectChange = (
    newValue: SingleValue<Option>,
    actionMeta: ActionMeta<Option>,
  ) => {
    if (actionMeta.action === "clear") {
      handleClear();
      return;
    }
    setValue(newValue ? newValue.label : "");
    setTouched(
      { ...touched, vendor_id: true, name: true },
      // do not validate if a new option was created; this prevents
      // incorrectly showing a "required field" error while a value is in
      // the field
      actionMeta.action !== "create-option",
    );
    if (newValue) {
      const newVendorId = options.some((opt) => opt.value === newValue.value)
        ? newValue.value
        : undefined;
      setFieldValue("vendor_id", newVendorId);
      onVendorSelected(newVendorId);
    }
  };

  const handleBlur = (event: React.FocusEvent) => {
    field.onBlur(event);
    if (searchParam) {
      setValue(searchParam);
    }
    setTouched(
      {
        ...touched,
        name: true,
      },
      // only validate if nothing is typed in the select's search input to
      // prevent incorrect "required field" error like above
      !searchParam,
    );
  };

  // we have to build the typeahead from scratch, too much context-specific
  // is needed to use the existing CustomCreatableSelect component
  const typeaheadSelect = (
    <FormControl isInvalid={isInvalid} isRequired width="100%">
      <VStack alignItems="start" position="relative" width="100%">
        <HStack spacing={1}>
          <Label htmlFor="name" fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          <QuestionTooltip label="Enter the system name" />
        </HStack>
        <Box width="100%" data-testid="input-name">
          <CreatableSelect
            name="name"
            id="name"
            options={suggestions}
            isRequired
            value={selected}
            onBlur={handleBlur}
            onChange={(newValue, actionMeta) =>
              handleSelectChange(newValue, actionMeta)
            }
            onInputChange={(e) => setSearchParam(e)}
            inputValue={searchParam}
            size="sm"
            onKeyDown={(e) => {
              if (e.key === "Tab") {
                handleTabPressed();
              }
            }}
            tabSelectsValue={hasVendorSuggestions}
            classNamePrefix="custom-select"
            placeholder="Enter system name..."
            instanceId="select-name"
            isDisabled={nameFieldLockedForGVL}
            menuPosition="absolute"
            isSearchable
            isClearable={!!searchParam}
            focusBorderColor="primary.600"
            formatCreateLabel={(inputValue) =>
              `Create new system "${inputValue}"...`
            }
            chakraStyles={{
              container: (provided) => ({
                ...provided,
                flexGrow: 1,
                backgroundColor: "white",
              }),
              option: (provided, state) => ({
                ...provided,
                background:
                  state.isSelected || state.isFocused ? "gray.50" : "unset",
              }),
              dropdownIndicator: (provided) => ({
                ...provided,
                display: "none",
              }),
              indicatorSeparator: (provided) => ({
                ...provided,
                display: "none",
              }),
            }}
            components={{ Option: CustomDictOption }}
          />
        </Box>
        <ErrorMessage
          isInvalid={isInvalid}
          message={meta.error}
          fieldName="name"
        />
        <Text
          aria-hidden
          position="absolute"
          backgroundColor="transparent"
          style={{ marginTop: "31.52px", marginLeft: "13px" }}
          pointerEvents="none"
          zIndex={1}
          fontSize="sm"
        >
          <Text as="span" color="transparent">
            {searchParam}
          </Text>
          {searchParam && suggestions.length > 0 ? (
            <Text as="span" color="complimentary.500">
              {suggestions[0].label.substring(searchParam.length)}
            </Text>
          ) : null}
        </Text>
      </VStack>
    </FormControl>
  );

  return (
    <HStack alignItems="flex-start" width="full">
      {isTypeahead ? (
        typeaheadSelect
      ) : (
        <CustomTextInput
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
