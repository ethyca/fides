import { ListItem, UnorderedList } from "@fidesui/react";
import React, { ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

export const NavList = ({ children }: Props) => (
  <UnorderedList
    borderLeftWidth="1px"
    borderLeftStyle="solid"
    borderLeftColor="gray.300"
    paddingLeft={3}
  >
    {children
      ? React.Children.map(children, (child) => (
          <ListItem listStyleType="none" paddingY={0.5}>
            {child}
          </ListItem>
        ))
      : null}
  </UnorderedList>
);

export default NavList;
