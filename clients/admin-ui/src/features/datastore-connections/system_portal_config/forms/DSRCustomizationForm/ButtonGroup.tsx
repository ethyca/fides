import {
  Button as ChakraButton,
  ButtonGroup as ChakraButtonGroup,
} from "fidesui";
import React from "react";

type ButtonGroupProps = {
  isSubmitting: boolean;
  onCancelClick: () => void;
};

export const ButtonGroup = ({
  isSubmitting = false,
  onCancelClick,
}: ButtonGroupProps) => (
  <ChakraButtonGroup size="sm" spacing="8px" variant="outline">
    <ChakraButton onClick={onCancelClick} variant="outline">
      Cancel
    </ChakraButton>
    <ChakraButton
      bg="primary.800"
      color="white"
      isDisabled={isSubmitting}
      isLoading={isSubmitting}
      loadingText="Submitting"
      size="sm"
      variant="solid"
      type="submit"
      _active={{ bg: "primary.500" }}
      _disabled={{ opacity: "inherit" }}
      _hover={{ bg: "primary.400" }}
    >
      Save
    </ChakraButton>
  </ChakraButtonGroup>
);
