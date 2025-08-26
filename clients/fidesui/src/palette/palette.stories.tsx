import type { Meta, StoryObj } from "@storybook/react-vite";
import { ColorPicker, List } from "antd";

import palette from "./palette.module.scss";

const meta = {
  title: "Palette",
} satisfies Meta<typeof List>;

export default meta;
type Story = StoryObj<typeof meta>;

// More on writing stories with args: https://storybook.js.org/docs/writing-stories/args
export const Palette: Story = {
  render: () => (
    <List
      dataSource={Object.entries(palette).map(([key, item]) => ({
        name: key,
        value: item,
      }))}
      renderItem={(item) => (
        <List.Item>
          <List.Item.Meta
            avatar={<ColorPicker value={item.value} />}
            title={item.name}
          />
        </List.Item>
      )}
    />
  ),
};
