import {
  Flex,
  FormControl,
  HStack,
  IconButton,
  Spacer,
  Text,
  VStack,
} from "@fidesui/react";
import {
  ActionMeta,
  chakraComponents,
  CreatableSelect,
  GroupBase,
  OptionProps,
  SingleValue,
} from "chakra-react-select";
import { useField, useFormikContext } from "formik";
import React, { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { ErrorMessage, Label, Option } from "~/features/common/form/inputs";
import { CompassIcon } from "~/features/common/Icon/CompassIcon";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { DictOption } from "~/features/plus/plus.slice";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";
import { DictSuggestionTextInput } from "~/features/system/dictionary-form/DictSuggestionInputs";
import { FormValues } from "~/features/system/form";

const CompassButton = ({
  active,
  disabled,
  onRefreshSuggestions,
}: {
  active: boolean;
  disabled: boolean;
  onRefreshSuggestions: () => void;
}) => (
  <VStack>
    <Spacer minHeight="18px" />
    <IconButton
      size="sm"
      isDisabled={disabled}
      onClick={() => onRefreshSuggestions()}
      aria-label="Update information from Compass"
      bg={active ? "complimentary.500" : "gray.100"}
      icon={<CompassIcon color={active ? "white" : "gray.700"} boxSize={4} />}
      data-testid="refresh-suggestions-btn"
    />
  </VStack>
);

interface Props {
  fieldsSeparated: boolean;
  isCreate: boolean;
  lockedForGVL: boolean;
  options: DictOption[];
  onVendorSelected: (vendorId: string | undefined) => void;
}

const CustomDictOption: React.FC<
  OptionProps<Option, false, GroupBase<Option>>
> = ({ children, ...props }) => (
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
  fieldsSeparated,
  isCreate,
  lockedForGVL,
  options,
  onVendorSelected,
}: Props) => {
  const isShowingSuggestions = useAppSelector(selectSuggestions);
  const [initialField, meta, { setValue }] = useField({
    name: fieldsSeparated ? "vendor_id" : "name",
  });
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const { touched, values, setTouched, setFieldValue } =
    useFormikContext<FormValues>();

  const selected = options.find((o) => o.value === field.value) ?? {
    label: field.value,
    value: field.value,
    description: "",
  };

  const [searchParam, setSearchParam] = useState<string>("");

  const suggestions = options.filter((opt) =>
    opt.label.toLowerCase().startsWith(searchParam.toLowerCase())
  );

  const handleTabPressed = () => {
    if (suggestions.length > 0 && searchParam !== suggestions[0].label) {
      setSearchParam(suggestions[0].label);
      setValue(suggestions[0].value);
    }
  };

  const handleChange = (
    newValue: SingleValue<Option>,
    actionMeta: ActionMeta<Option>
  ) => {
    setValue(newValue ? newValue.label : "");
    setTouched({ ...touched, vendor_id: true, name: !fieldsSeparated });
    if (newValue) {
      const newVendorId = options.some((opt) => opt.value === newValue.value)
        ? newValue.value
        : undefined;
      setFieldValue("vendor_id", newVendorId);
      onVendorSelected(newVendorId);
    } else if (actionMeta.action === "clear") {
      setFieldValue("vendor_id", undefined);
      onVendorSelected(undefined);
    }
  };

  return (
    <>
      <HStack alignItems="flex-start">
        <FormControl isInvalid={isInvalid}>
          <VStack alignItems="start" position="relative">
            <Flex alignItems="center">
              <Label htmlFor="vendor_id" fontSize="xs" my={0} mr={1}>
                {fieldsSeparated ? "Vendor" : "System name"}
              </Label>
              <QuestionTooltip
                label={
                  fieldsSeparated
                    ? "Enter the vendor to associate with the system"
                    : "Enter the system name"
                }
              />
            </Flex>
            <Flex
              position="relative"
              width="100%"
              data-testid={`input-${field.name}`}
            >
              <CreatableSelect
                options={suggestions}
                value={selected}
                onBlur={(e) => {
                  setTouched({
                    ...touched,
                    vendor_id: true,
                    name: !fieldsSeparated,
                  });
                  field.onBlur(e);
                }}
                onChange={(newValue, actionMeta) =>
                  handleChange(newValue, actionMeta)
                }
                onInputChange={(e) => setSearchParam(e)}
                inputValue={searchParam}
                name={fieldsSeparated ? "vendor_id" : "name"}
                size="sm"
                onKeyDown={(e) => {
                  if (e.key === "Tab") {
                    handleTabPressed();
                  }
                }}
                classNamePrefix="custom-select"
                placeholder={
                  fieldsSeparated
                    ? "Enter vendor name..."
                    : "Enter system name..."
                }
                instanceId={
                  fieldsSeparated ? "select-vendor_id" : "select-name"
                }
                isDisabled={!isCreate && lockedForGVL}
                menuPosition="absolute"
                isSearchable
                isClearable
                focusBorderColor="primary.600"
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                formatCreateLabel={(_value) => null}
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
                  menu: (provided) => ({
                    ...provided,
                    visibility:
                      searchParam && suggestions.length > 0
                        ? "visible"
                        : "hidden",
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
              <Text
                aria-hidden
                style={{
                  position: "absolute",
                  backgroundColor: "transparent",
                  borderColor: "transparent",
                  marginTop: "5.52px",
                  marginLeft: "13px",
                  pointerEvents: "none",
                  fontSize: "14px",
                  zIndex: 1,
                }}
              >
                <span style={{ color: "transparent" }}>{searchParam}</span>
                {searchParam && suggestions.length > 0 ? (
                  <span style={{ color: "#824EF2" }}>
                    {suggestions[0].label.substring(searchParam.length)}
                  </span>
                ) : null}
              </Text>
            </Flex>
            <ErrorMessage
              isInvalid={isInvalid}
              message={meta.error}
              fieldName={fieldsSeparated ? "vendor_id" : "name"}
            />
          </VStack>
        </FormControl>
        <CompassButton
          active={!!values.vendor_id}
          disabled={!values.vendor_id || isShowingSuggestions === "showing"}
          onRefreshSuggestions={() => onVendorSelected(values.vendor_id)}
        />
      </HStack>
      {fieldsSeparated ? (
        <DictSuggestionTextInput
          id="name"
          name="name"
          dictField={(vendor) => vendor.name ?? (vendor.legal_name || "")}
          isRequired
          label="System name"
          tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
        />
      ) : null}
    </>
  );
};

export default VendorSelector;
