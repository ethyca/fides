/**
 * Custom Storybook decorator that reads the `theme` global from the toolbar
 * and applies the matching Ant Design ThemeConfig to FidesUIProvider.
 *
 * Following the pattern described in:
 * https://github.com/storybookjs/storybook/blob/next/code/addons/themes/docs/api.md#writing-a-custom-decorator
 *
 * Usage in a story:
 *   // Force a specific story to always use the dark theme
 *   export const MyStory = { parameters: { theme: "dark" } };
 */
import { useGlobals } from "storybook/preview-api";
import type { DecoratorFunction, Renderer } from "storybook/internal/types";
import { theme as antTheme } from "antd";
import React, { useEffect } from "react";

import { darkAntTheme, defaultAntTheme } from "../src/ant-theme";
import { FidesUIProvider } from "../src/FidesUIProvider";
import type { ThemeConfig } from "../src/ant-theme";

const THEME_MAP: Record<string, ThemeConfig> = {
  light: defaultAntTheme,
  dark: darkAntTheme,
};

export const DEFAULT_THEME = "light";

export const withAntTheme: DecoratorFunction<Renderer> = (Story, context) => {
  const [globals] = useGlobals();

  // Story-level `parameters.theme` takes precedence over the toolbar global
  const selectedTheme: string =
    context.parameters.theme ?? globals.theme ?? DEFAULT_THEME;

  const themeConfig: ThemeConfig = THEME_MAP[selectedTheme] ?? defaultAntTheme;

  // Keep a data attribute on <body> so plain CSS rules can react to the theme
  useEffect(() => {
    document.body.dataset.antTheme = selectedTheme;
    return () => {
      delete document.body.dataset.antTheme;
    };
  }, [selectedTheme]);

  return (
    <FidesUIProvider antTheme={themeConfig}>
      <ThemeBackground>
        <Story />
      </ThemeBackground>
    </FidesUIProvider>
  );
};

/**
 * Reads the resolved Ant background token and applies it to the Storybook
 * canvas body so the full preview area reflects the current theme.
 */
const ThemeBackground = ({ children }: { children: React.ReactNode }) => {
  const { token } = antTheme.useToken();

  useEffect(() => {
    const prev = document.body.style.backgroundColor;
    document.body.style.backgroundColor = token.colorBgLayout;
    return () => {
      document.body.style.backgroundColor = prev;
    };
  }, [token.colorBgLayout]);

  return <>{children}</>;
};
