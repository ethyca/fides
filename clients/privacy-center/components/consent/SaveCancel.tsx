import { Button, Stack } from "@fidesui/react";

const SaveCancel = ({
  onSave,
  onCancel,
}: {
  onSave: () => void;
  onCancel: () => void;
}) => (
  <Stack direction="row" justifyContent="flex-start" paddingX={12} width="full">
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
      Save
    </Button>
  </Stack>
);

export default SaveCancel;
