import {
  ArrowDownLineIcon,
  Box,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuProps,
} from "fidesui";

import ConfigureAlerts from "../drawers/ConfigureAlerts";

type MoreButtonProps = {
  menuProps?: MenuProps;
};

const MoreButton = ({ menuProps }: MoreButtonProps) => (
  <Box>
    <Menu {...menuProps}>
      <MenuButton
        as={Button}
        fontWeight="normal"
        rightIcon={<ArrowDownLineIcon />}
        size="xs"
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
