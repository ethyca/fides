import React from "react";
import type { Preview } from "@storybook/react-vite";

import { darkAntTheme, defaultAntTheme } from "../src/ant-theme";
import { FidesUIProvider } from "../src/FidesUIProvider";

import "../src/ant-theme/global.scss";
import "../src/tailwind.css";

import { withAntTheme, DEFAULT_THEME } from "./withAntTheme";

const preview: Preview = {
  initialGlobals: {
    theme: DEFAULT_THEME,
  },

  /**
   * Declares the toolbar UI for theme switching.
   * Add more entries to `items` (and to THEME_MAP in withAntTheme.tsx) to
   * expose additional Ant Design themes without touching anything else.
   */
  globalTypes: {
    theme: {
      description: "Ant Design theme",
      toolbar: {
        title: "Theme",
        icon: "paintbrush",
        items: [
          { value: "light", title: "Light", icon: "sun" },
          { value: "dark", title: "Dark", icon: "moon" },
        ],
        dynamicTitle: true,
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
    options: {
      storySort: {
        order: ['General', 'Layout', 'Navigation', 'Data Entry', 'Data Display', 'Feedback', 'Charts']
      }
    }
  },

  decorators: [withAntTheme],
};

export default preview;
