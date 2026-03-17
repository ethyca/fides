import type { DropdownProps } from "antd/lib";
import { Dropdown as AntDropdown } from "antd/lib";

const CustomDropdownBase = ({
  trigger = ["click"],
  ...props
}: DropdownProps) => <AntDropdown trigger={trigger} {...props} />;

export const CustomDropdown = Object.assign(CustomDropdownBase, {
  Button: AntDropdown.Button,
});
