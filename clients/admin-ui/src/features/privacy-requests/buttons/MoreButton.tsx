import {
  ArrowDownLineIcon,
  Box,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuProps,
} from "@fidesui/react";

import ConfigureAlerts from "../drawers/ConfigureAlerts";

type MoreButtonProps = {
  menuProps?: MenuProps;
};

const MoreButton: React.FC<MoreButtonProps> = ({
  menuProps,
}: MoreButtonProps) => (
  <Box>
    <Menu {...menuProps}>
      <MenuButton
        as={Button}
        fontWeight="normal"
        rightIcon={<ArrowDownLineIcon />}
        size="sm"
        variant="outline"
        _active={{
          bg: "none",
        }}
        _hover={{
          bg: "none",
        }}
      >
        More
      </MenuButton>
      <MenuList fontSize="sm">
        {/* MenuItems are not rendered unless Menu is open */}
        <ConfigureAlerts />
      </MenuList>
    </Menu>
  </Box>
);

export default MoreButton;
