import {
  CircleHelpIcon,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  FormLabelProps,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Textarea,
  VStack,
} from "@fidesui/react";
import { FieldHookConfig, useField } from "formik";

import { InputType } from "./types";

/**
 * This isn't the cleanest way to style these forms, but it's a quick hack. Ideally our form inputs
 * (like CustomSelect) would all use the same styles, or at least have a limited set of variants:
 * https://chakra-ui.com/docs/styled-system/component-style#styling-multipart-components
 *
 * Unfortunately the designs for these forms call for styles that are inconsistent with the other
 * forms in the app.
 */
export const CUSTOM_LABEL_STYLES: FormLabelProps = {
  color: "gray.600",
  fontSize: "14px",
  fontWeight: "semibold",
  minWidth: "150px",
};

type CustomInputProps = {
  disabled?: boolean;
  displayHelpIcon?: boolean;
  helpIconVisibility?: boolean;
  isRequired?: boolean;
  label?: string;
  type?: InputType;
};

const CustomInput = ({
  disabled = false,
  displayHelpIcon = true,
  helpIconVisibility = false,
  isRequired = false,
  label,
  type = "text",
  ...props
}: CustomInputProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);

  const testId = `custom-input-${field.name}`;

  return (
    <FormControl
      display="flex"
      isRequired={isRequired}
      isInvalid={!!(meta.error && meta.touched)}
    >
      {label && (
        <FormLabel htmlFor={props.id || props.name} {...CUSTOM_LABEL_STYLES}>
          {label}
        </FormLabel>
      )}
      <VStack align="flex-start" w="inherit">
        {type === "number" && (
          <NumberInput
            allowMouseWheel
            color="gray.700"
            defaultValue={0}
            min={0}
            size="sm"
          >
            <NumberInputField
              {...field}
              autoComplete="off"
              autoFocus={props.autoFocus}
              data-testid={testId}
            />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        )}
        {type === "text" && (
          <Input
            {...field}
            autoComplete="off"
            autoFocus={props.autoFocus}
            color="gray.700"
            isDisabled={disabled}
            placeholder={props.placeholder}
            size="sm"
            data-testid={testId}
          />
        )}
        {type === "textarea" && (
          <Textarea
            {...field}
            autoComplete="off"
            autoFocus={props.autoFocus}
            color="gray.700"
            placeholder={props.placeholder}
            resize="none"
            size="sm"
            value={field.value || ""}
            data-testid={testId}
          />
        )}
        <FormErrorMessage>{meta.error}</FormErrorMessage>
      </VStack>
      {displayHelpIcon && (
        <Flex
          alignContent="center"
          h="32px"
          visibility={helpIconVisibility ? "visible" : "hidden"}
        >
          <CircleHelpIcon marginLeft="8px" _hover={{ cursor: "pointer" }} />
        </Flex>
      )}
    </FormControl>
  );
};

export default CustomInput;
