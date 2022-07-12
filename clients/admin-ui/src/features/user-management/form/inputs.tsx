// Adapted from https://github.com/ethyca/fides/blob/main/clients/admin-ui/src/features/common/form/inputs.tsx
// Should in the future consider pulling this into fidesui

import {
  Box,
  FormControl,
  FormErrorMessage,
  FormLabel,
  IconButton,
  Input,
  InputGroup,
  InputRightElement,
} from "@fidesui/react";
import { FieldHookConfig, useField } from "formik";
import { useState } from "react";

import { EyeIcon } from "../../common/Icon";

interface InputProps {
  disabled?: boolean;
  label: string;
}

export const CustomTextInput = ({
  label,
  disabled,
  ...props
}: InputProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const { type: initialType, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);

  const isPassword = initialType === "password";
  const [type, setType] = useState<"text" | "password">(
    isPassword ? "password" : "text"
  );

  const handleClickReveal = () =>
    setType(type === "password" ? "text" : "password");

  return (
    <FormControl isInvalid={isInvalid}>
      <FormLabel htmlFor={props.id || props.name} fontWeight="medium">
        {label}
      </FormLabel>
      <Box display="flex" alignItems="center">
        <InputGroup mr="2">
          <Input
            {...field}
            data-testid={`input-${field.name}`}
            type={type}
            placeholder={placeholder}
            pr={isPassword ? "10" : "3"}
            focusBorderColor="primary.500"
            isDisabled={disabled}
          />
          {isPassword ? (
            <InputRightElement pr="2">
              <IconButton
                size="xs"
                variant="unstyled"
                aria-label="Reveal/Hide Secret"
                icon={
                  <EyeIcon
                    boxSize="full"
                    color={type === "password" ? "gray.400" : "gray.700"}
                  />
                }
                onClick={handleClickReveal}
              />
            </InputRightElement>
          ) : null}
        </InputGroup>
      </Box>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
