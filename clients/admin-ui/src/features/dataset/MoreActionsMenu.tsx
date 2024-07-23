import {
  Button,
  Menu,
  MenuButton,
  MenuDivider,
  MenuGroup,
  MenuItem,
  MenuList,
  MoreIcon,
} from "fidesui";
import NextLink from "next/link";
import { ReactNode } from "react";

const ActionItem = ({
  children,
  isDisabled,
  onClick,
  ...props
}: {
  children: ReactNode;
  isDisabled?: boolean;
  onClick?: () => void;
}) => (
  <MenuItem
    isDisabled={isDisabled}
    _hover={{ backgroundColor: "gray.100" }}
    fontSize="sm"
    onClick={onClick}
    {...props}
  >
    {children}
  </MenuItem>
);

interface Props {
  onModifyCollection: () => void;
  onModifyDataset: () => void;
}
const MoreActionsMenu = ({ onModifyCollection, onModifyDataset }: Props) => (
  <Menu size="sm">
    <MenuButton as={Button} variant="outline" data-testid="more-actions-btn">
      <MoreIcon />
    </MenuButton>
    <MenuList>
      <MenuGroup
        title="Collections"
        color="gray.500"
        textTransform="uppercase"
        mx={3}
      >
        <MenuDivider />
        <ActionItem isDisabled>Add a collection</ActionItem>
        <ActionItem
          onClick={onModifyCollection}
          data-testid="modify-collection"
        >
          Modify collection
        </ActionItem>
      </MenuGroup>
      <MenuGroup
        title="Datasets"
        color="gray.500"
        textTransform="uppercase"
        mx={3}
      >
        <MenuDivider />
        <MenuItem
          as={NextLink}
          href="/dataset"
          _hover={{ backgroundColor: "gray.100" }}
          fontSize="sm"
        >
          Select new dataset
        </MenuItem>
        <ActionItem isDisabled>Classify this dataset</ActionItem>
        <ActionItem onClick={onModifyDataset} data-testid="modify-dataset">
          Modify dataset
        </ActionItem>
      </MenuGroup>
    </MenuList>
  </Menu>
);

export default MoreActionsMenu;
