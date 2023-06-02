import { Button, Stack, StackProps } from "@fidesui/react";

const SaveCancel = ({
  onSave,
  onCancel,
  saveLabel = "Save",
  ...props
}: {
  onSave: () => void;
  onCancel: () => void;
  saveLabel?: string;
} & StackProps) => (
  <Stack direction="row" justifyContent="flex-start" width="full" {...props}>
    <Button size="sm" variant="outline" onClick={onCancel}>
      Cancel
    </Button>
    <Button
      bg="primary.800"
      _hover={{ bg: "primary.400" }}
      _active={{ bg: "primary.500" }}
      colorScheme="primary"
      size="sm"
      onClick={onSave}
      data-testid="save-btn"
    >
      {saveLabel}
    </Button>
  </Stack>
);

export default SaveCancel;
