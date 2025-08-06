import type { Preview } from "@storybook/react-vite";
import React from "react";

import { defaultAntTheme } from "../src/ant-theme";
import { FidesUIProvider } from "../src/FidesUIProvider";

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
    (Story, { parameters }) => {
      return (
        <FidesUIProvider antTheme={defaultAntTheme}>
          <Story />
        </FidesUIProvider>
      );
    },
  ],
};

export default preview;
