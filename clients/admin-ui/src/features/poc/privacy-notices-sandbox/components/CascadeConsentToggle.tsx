import { AntFlex as Flex, AntTypography as Typography, Switch } from "fidesui";

const CascadeConsentToggle = ({
  isEnabled,
  onToggle,
}: {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
}) => {
  return (
    <Flex align="center" gap={3} className="mb-4">
      <Typography.Text strong>Cascade consent to children:</Typography.Text>
      <Switch
        isChecked={isEnabled}
        onChange={(e) => onToggle(e.target.checked)}
        size="sm"
      />
    </Flex>
  );
};

export default CascadeConsentToggle;
