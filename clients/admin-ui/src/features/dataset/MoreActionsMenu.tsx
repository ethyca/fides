import {
  Button,
  Menu,
  MenuButton,
  MenuDivider,
  MenuGroup,
  MenuItem,
  MenuList,
} from "@fidesui/react";
import NextLink from "next/link";
import { ReactNode } from "react";

import More from "~/features/common/Icon/More";

const ActionItem = ({
  children,
  isDisabled,
  onClick,
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
  >
    {children}
  </MenuItem>
);

interface Props {
  onModifyCollection: () => void;
}
const MoreActionsMenu = ({ onModifyCollection }: Props) => (
  <Menu size="sm">
    <MenuButton as={Button} variant="outline">
      <More />
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
        <ActionItem onClick={onModifyCollection}>Modify collection</ActionItem>
      </MenuGroup>
      <MenuGroup
        title="Datasets"
        color="gray.500"
        textTransform="uppercase"
        mx={3}
      >
        <MenuDivider />
        <ActionItem>
          <NextLink href="/dataset">Select new dataset</NextLink>
        </ActionItem>
        <ActionItem isDisabled>Classify this dataset</ActionItem>
        <ActionItem isDisabled>Modify dataset</ActionItem>
      </MenuGroup>
    </MenuList>
  </Menu>
);

export default MoreActionsMenu;
