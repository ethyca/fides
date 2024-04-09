import { Button, Stack, StackProps } from "@fidesui/react";
import { useI18n } from "~/common/i18nContext";

const SaveCancel = ({
  onSave,
  onCancel,
  ...props
}: {
  onSave: () => void;
  onCancel: () => void;
  saveLabel?: string;
} & StackProps) => {
  const { i18n } = useI18n();

  return (
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
        {i18n.t("exp.save_button_label")}
      </Button>
    </Stack>
  );
};

export default SaveCancel;
