import type { Preview } from "@storybook/react-vite";
import { App, ConfigProvider } from "antd";
import React from "react";

import { defaultAntTheme } from "../src/ant-theme";
import { FidesUIProvider } from "../src/FidesUIProvider";

import "../src/ant-theme/global.scss";
import "../src/tailwind.css";

const StorybookThemeWrapper = ({
  children,
}: {
  children: React.ReactNode;
}) => (
  <ConfigProvider theme={defaultAntTheme}>
    <App>{children}</App>
  </ConfigProvider>
);

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
  decorators: [
    (Story) => {
      return (
        <FidesUIProvider antTheme={defaultAntTheme}>
          <StorybookThemeWrapper>
            <Story />
          </StorybookThemeWrapper>
        </FidesUIProvider>
      );
    },
  ],
};

export default preview;
