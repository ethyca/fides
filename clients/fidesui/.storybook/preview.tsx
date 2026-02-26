import type { Preview } from "@storybook/react-vite";

import "../src/ant-theme/global.scss";
import "../src/tailwind.css";

import { withAntTheme, DEFAULT_THEME } from "./withAntTheme";

const preview: Preview = {
  /**
   * Registers the `theme` global so the toolbar dropdown has an initial value.
   * The actual current value lives in Storybook's globals store and is updated
   * whenever the user clicks a toolbar item.
   */

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
  },

  decorators: [withAntTheme],
};

export default preview;
