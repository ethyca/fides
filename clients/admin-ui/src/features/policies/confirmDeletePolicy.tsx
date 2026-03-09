import { Typography, useModal } from "fidesui";

const { Text } = Typography;

export const confirmDeletePolicy = (
  modal: ReturnType<typeof useModal>,
  policyName: string,
  onConfirm: () => void | Promise<void>,
) => {
  modal.confirm({
    title: "Delete policy",
    icon: null,
    content: (
      <Text type="secondary">
        Are you sure you want to delete the policy &ldquo;{policyName}
        &rdquo;? This action cannot be undone and will also delete all
        associated rules.
      </Text>
    ),
    onOk: onConfirm,
    okText: "Delete",
    okButtonProps: { danger: true },
    centered: true,
  });
};
