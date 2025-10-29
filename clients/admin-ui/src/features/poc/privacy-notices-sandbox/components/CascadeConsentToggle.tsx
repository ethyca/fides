import { AntTypography as Typography, Switch } from "fidesui";

const CascadeConsentToggle = ({
  isEnabled,
  onToggle,
}: {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
}) => {
  return (
    <div className="mb-4 flex items-center gap-3">
      <Typography.Text className="text-sm font-medium">
        Cascade consent to children:
      </Typography.Text>
      <Switch
        isChecked={isEnabled}
        onChange={(e) => onToggle(e.target.checked)}
        size="sm"
      />
    </div>
  );
};

export default CascadeConsentToggle;
