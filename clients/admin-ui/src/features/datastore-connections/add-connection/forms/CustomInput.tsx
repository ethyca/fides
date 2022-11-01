import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  Input,
  NumberDecrementStepper,
  NumberIncrementStepper,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  Textarea,
  VStack,
} from "@fidesui/react";
import { CircleHelpIcon } from "common/Icon";
import { FieldHookConfig, useField } from "formik";

import { InputType } from "./types";

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

  return (
    <FormControl
      display="flex"
      isRequired={isRequired}
      isInvalid={!!(meta.error && meta.touched)}
    >
      {label && (
        <FormLabel
          color="gray.900"
          fontSize="14px"
          fontWeight="semibold"
          htmlFor={props.id || props.name}
          minWidth="141px"
        >
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
          />
        )}
        <FormErrorMessage>{meta.error}</FormErrorMessage>
      </VStack>
      {displayHelpIcon && (
        <CircleHelpIcon
          marginLeft="8px"
          visibility={helpIconVisibility ? "visible" : "hidden"}
          _hover={{ cursor: "pointer" }}
        />
      )}
    </FormControl>
  );
};

export default CustomInput;
