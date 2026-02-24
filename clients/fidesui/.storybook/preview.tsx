import type { Preview } from "@storybook/react-vite";
import { App, ConfigProvider, ThemeConfig } from "antd";
import React from "react";

import { darkAntTheme, defaultAntTheme } from "../src/ant-theme";
import { FidesUIProvider } from "../src/FidesUIProvider";

import "../src/ant-theme/global.scss";
import "../src/tailwind.css";

const antThemes: Record<string, ThemeConfig> = {
  default: defaultAntTheme,
  dark: darkAntTheme,
};

const StorybookThemeWrapper = ({
  theme,
  children,
}: {
  theme: ThemeConfig;
  children: React.ReactNode;
}) => (
  <ConfigProvider theme={theme}>
    <App>{children}</App>
  </ConfigProvider>
);

const preview: Preview = {
  globalTypes: {
    antTheme: {
      name: "Ant Theme",
      description: "Switch between Ant Design themes",
      defaultValue: "default",
      toolbar: {
        icon: "paintbrush",
        items: [
          { value: "default", title: "Default (Light)" },
          { value: "dark", title: "Dark" },
        ],
      },
    },
  },
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [
    (Story, { globals }) => {
      const theme = antThemes[globals.antTheme] ?? defaultAntTheme;
      return (
        <FidesUIProvider antTheme={theme}>
          <StorybookThemeWrapper theme={theme}>
            <Story />
          </StorybookThemeWrapper>
        </FidesUIProvider>
      );
    },
  ],
};

export default preview;
