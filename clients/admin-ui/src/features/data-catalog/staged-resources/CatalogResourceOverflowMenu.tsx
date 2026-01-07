import {
  Button,
  ChakraMenu as Menu,
  ChakraMenuButton as MenuButton,
  ChakraMenuItem as MenuItem,
  ChakraMenuList as MenuList,
  MoreIcon,
} from "fidesui";

const CatalogResourceOverflowMenu = ({
  onHideClick,
  onDetailClick,
}: {
  onHideClick?: () => void;
  onDetailClick?: () => void;
}) => (
  <Menu>
    <MenuButton
      as={Button}
      size="small"
      // @ts-expect-error - Ant type, not Chakra type because of `as` prop
      type="text"
      icon={<MoreIcon transform="rotate(90deg)" />}
      className="w-6 gap-0"
      data-testid="actions-menu"
    />
    <MenuList>
      {onDetailClick && (
        <MenuItem onClick={onDetailClick} data-testid="view-resource-details">
          View details
        </MenuItem>
      )}
      {onHideClick && (
        <MenuItem onClick={onHideClick} data-testid="hide-resource">
          Hide
        </MenuItem>
      )}
    </MenuList>
  </Menu>
);

export default CatalogResourceOverflowMenu;
