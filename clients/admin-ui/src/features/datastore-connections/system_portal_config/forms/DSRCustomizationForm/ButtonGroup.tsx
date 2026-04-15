import { Button, Flex } from "fidesui";
import React from "react";

type ButtonGroupProps = {
  isSubmitting: boolean;
  onCancelClick: () => void;
};

export const ButtonGroup = ({
  isSubmitting = false,
  onCancelClick,
}: ButtonGroupProps) => (
  <Flex gap="small">
    <Button onClick={onCancelClick}>Cancel</Button>
    <Button
      type="primary"
      disabled={isSubmitting}
      loading={isSubmitting}
      htmlType="submit"
    >
      Save
    </Button>
  </Flex>
);
