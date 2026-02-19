import type { ThemeMode } from "fidesui";
import { Button, Icons, Segmented, useThemeMode } from "fidesui";

// NOTE: This button is temporary, only for testing in dev.

export const ThemeModeSegmented = () => {
  const { mode, setMode } = useThemeMode();

  return (
    <Segmented
      size="small"
      value={mode}
      onChange={(value) => setMode(value as ThemeMode)}
      options={[
        {
          label: <Icons.Light size={14} />,
          value: "light",
        },
        {
          label: <Icons.Asleep size={14} />,
          value: "dark",
        },
      ]}
    />
  );
};

export const ThemeModeButton = () => {
  const { mode, setMode } = useThemeMode();

  const toggleMode = () => {
    setMode(mode === "light" ? "dark" : "light");
  };

  const getIcon = () => {
    if (mode === "dark") {
      return <Icons.Asleep size={16} />;
    }
    return <Icons.Light size={16} />;
  };

  const getTooltipText = () => {
    if (mode === "dark") {
      return "Dark mode (click for light)";
    }
    return "Light mode (click for dark)";
  };

  return (
    <Button
      type="primary"
      className="border-none bg-transparent hover:!bg-gray-700"
      icon={getIcon()}
      onClick={toggleMode}
      aria-label={getTooltipText()}
      title={getTooltipText()}
    />
  );
};
