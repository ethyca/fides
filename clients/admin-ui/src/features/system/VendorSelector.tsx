import { Flex, FormControl, HStack, Text, VStack } from "@fidesui/react";
import { Select, SingleValue } from "chakra-react-select";
import { useField, useFormikContext } from "formik";
import { useState } from "react";

import { ErrorMessage, Label, Option } from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { DictOption } from "~/features/plus/plus.slice";
import { DictSuggestionToggle } from "~/features/system/dictionary-form/ToggleDictSuggestions";

interface Props {
  disabled?: boolean;
  options: DictOption[];
}

const VendorSelector = ({ disabled, options }: Props) => {
  const [initialField, meta, { setValue }] = useField({ name: "vendor_id" });
  const isInvalid = !!(meta.touched && meta.error);
  const field = { ...initialField, value: initialField.value ?? "" };
  const { touched, setTouched } = useFormikContext();

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

  const handleChange = (newValue: SingleValue<Option>) => {
    if (newValue) {
      setValue(newValue.value);
    }
  };

  return (
    <HStack alignItems="flex-end">
      <FormControl isInvalid={isInvalid}>
        <VStack alignItems="start" position="relative">
          <Flex alignItems="center">
            <Label htmlFor="vendor" fontSize="xs" my={0} mr={1}>
              Vendor
            </Label>
            <QuestionTooltip label="Enter the vendor to associate with the system" />
          </Flex>
          <Flex
            position="relative"
            width="100%"
            data-testid={`input-${field.name}`}
          >
            <Select
              options={suggestions}
              onBlur={(e) => {
                setTouched({ ...touched, test_vendor: true });
                field.onBlur(e);
              }}
              onChange={handleChange}
              onInputChange={(e) => setSearchParam(e)}
              inputValue={searchParam}
              name="vendor_id"
              size="sm"
              onKeyDown={(e) => {
                if (e.key === "Tab") {
                  handleTabPressed();
                }
              }}
              classNamePrefix="custom-select"
              placeholder="Enter vendor name..."
              instanceId="select-vendor_id"
              isDisabled={disabled}
              menuPosition="absolute"
              isSearchable
              isClearable
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
                  visibility: searchParam ? "visible" : "hidden",
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
            message="test"
            fieldName="vendor"
          />
        </VStack>
      </FormControl>
      <DictSuggestionToggle />
    </HStack>
  );
};

export default VendorSelector;
