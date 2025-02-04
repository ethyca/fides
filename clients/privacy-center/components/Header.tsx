"use client";

import { Flex } from "@chakra-ui/layout";

import Logo from "./Logo";

interface HeaderProps {
  logoPath: string;
  logoUrl: string;
}

const Header = ({ logoPath, logoUrl }: HeaderProps) => {
  return (
    <header>
      <Flex
        bg="gray.75"
        minHeight={14}
        p={1}
        width="100%"
        justifyContent="center"
        alignItems="center"
      >
        <Logo src={logoPath ?? ""} href={logoUrl ?? ""} />
      </Flex>
    </header>
  );
};
export default Header;
