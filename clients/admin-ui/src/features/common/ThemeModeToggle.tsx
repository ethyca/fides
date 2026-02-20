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
