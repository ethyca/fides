import {
  Button as ChakraButton,
  ButtonGroup as ChakraButtonGroup,
} from "@fidesui/react";
import React from "react";

type ButtonGroupProps = {
  isSubmitting: boolean;
  onCancelClick: () => void;
};

export const ButtonGroup: React.FC<ButtonGroupProps> = ({
  isSubmitting = false,
  onCancelClick,
}) => (
  <ChakraButtonGroup size="sm" spacing="8px" variant="outline">
    <ChakraButton onClick={onCancelClick} variant="outline">
      Cancel
    </ChakraButton>
    <ChakraButton
      bg="primary.800"
      color="white"
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
