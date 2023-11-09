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
    />
  </VStack>
);

interface Props {
  disabled?: boolean;
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

const VendorSelector = ({ disabled, options, onVendorSelected }: Props) => {
  const isShowingSuggestions = useAppSelector(selectSuggestions);
  const [initialField, meta, { setValue }] = useField({
    name: "name",
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
    setTouched({ ...touched, name: true });
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
    <HStack alignItems="flex-start">
      <FormControl isInvalid={isInvalid}>
        <VStack alignItems="start" position="relative">
          <Flex alignItems="center">
            <Label htmlFor="name" fontSize="xs" my={0} mr={1}>
              System name
            </Label>
            <QuestionTooltip label="Enter the vendor to associate with the system" />
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
                setTouched({ ...touched, name: true });
                field.onBlur(e);
              }}
              onChange={(newValue, actionMeta) =>
                handleChange(newValue, actionMeta)
              }
              onInputChange={(e) => setSearchParam(e)}
              inputValue={searchParam}
              name="name"
              size="sm"
              onKeyDown={(e) => {
                if (e.key === "Tab") {
                  handleTabPressed();
                }
              }}
              classNamePrefix="custom-select"
              placeholder="Enter system name..."
              instanceId="select-name"
              isDisabled={disabled}
              menuPosition="absolute"
              isSearchable
              isClearable
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
            fieldName="name"
          />
        </VStack>
      </FormControl>
      <CompassButton
        active={!!values.vendor_id}
        disabled={!values.vendor_id || isShowingSuggestions === "showing"}
        onRefreshSuggestions={() => onVendorSelected(values.vendor_id)}
      />
    </HStack>
  );
};

export default VendorSelector;
