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

export const ThemeModeToggle = () => {
  const { resolvedMode, setMode } = useThemeMode();
  const isDark = resolvedMode === "dark";
  return (
    <Button
      type="text"
      size="small"
      icon={isDark ? <Icons.Light size={16} /> : <Icons.Asleep size={16} />}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setMode(isDark ? "light" : "dark")}
    />
  );
};
