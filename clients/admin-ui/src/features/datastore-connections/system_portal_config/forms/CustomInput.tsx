import {
  CircleHelpIcon,
  Flex,
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
} from "fidesui";
import { FieldHookConfig, useField } from "formik";

import { InputType } from "./types";

type CustomInputProps = {
  disabled?: boolean;
  displayHelpIcon?: boolean;
  helpIconVisibility?: boolean;
  isRequired?: boolean;
  label?: string;
  placeholder?: string;
  type?: InputType;
};

const CustomInput = ({
  disabled = false,
  displayHelpIcon = true,
  helpIconVisibility = false,
  isRequired = false,
  label,
  placeholder,
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
          color="neutral.900"
          fontSize="14px"
          fontWeight="semibold"
          htmlFor={props.id || props.name}
          minWidth="150px"
        >
          {label}
        </FormLabel>
      )}
      <VStack align="flex-start" w="inherit">
        {type === "number" && (
          <NumberInput
            allowMouseWheel
            color="neutral.700"
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
            color="neutral.700"
            isDisabled={disabled}
            placeholder={placeholder}
            size="sm"
          />
        )}
        {type === "textarea" && (
          <Textarea
            {...field}
            autoComplete="off"
            autoFocus={props.autoFocus}
            color="neutral.700"
            placeholder={placeholder}
            resize="none"
            size="sm"
            value={field.value || ""}
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
