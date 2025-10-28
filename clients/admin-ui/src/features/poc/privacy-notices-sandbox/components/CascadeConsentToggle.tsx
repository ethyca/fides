import { AntTypography as Typography, Switch } from "fidesui";
import { useCallback } from "react";

const CascadeConsentToggle = ({
  isEnabled,
  onToggle,
}: {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
}) => {
  const handleToggle = useCallback(
    (checked: boolean) => {
      onToggle(checked);
    },
    [onToggle],
  );

  return (
    <div className="mb-4 flex items-center gap-3">
      <Typography.Text className="text-sm font-medium">
        Cascade consent to children:
      </Typography.Text>
      <Switch
        isChecked={isEnabled}
        onChange={(e) => handleToggle(e.target.checked)}
        size="sm"
      />
    </div>
  );
};

export default CascadeConsentToggle;
