import { Button, Stack, StackProps } from "fidesui";

import useI18n from "~/common/hooks/useI18n";

const SaveCancel = ({
  onSave,
  onCancel,
  saveLabel,
  cancelLabel,
  ...props
}: {
  onSave: () => void;
  onCancel: () => void;
  saveLabel?: string;
  cancelLabel?: string;
} & StackProps) => {
  const { i18n } = useI18n();

  return (
    <Stack direction="row" justifyContent="flex-start" width="full" {...props}>
      <Button
        size="sm"
        variant="outline"
        onClick={onCancel}
        aria-label="Cancel"
      >
        {cancelLabel || "←"}
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
        {saveLabel || i18n.t("exp.save_button_label")}
      </Button>
    </Stack>
  );
};

export default SaveCancel;
