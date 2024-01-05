import { Box, Link, VStack } from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";

import logoImage from "~/../public/logo-white.svg";
import Image from "~/features/common/Image";

import { useNav } from "./hooks";
import { INDEX_ROUTE } from "./routes";

const FidesLogoHomeLink = () => (
  <NextLink href={INDEX_ROUTE} passHref>
    {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
    <Link display="flex">
      <Image src={logoImage} width={83} height={26} alt="Fides Logo" />
    </Link>
  </NextLink>
);

const MainSideNav = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });

  return (
    <Box p={4} minWidth="200px" backgroundColor="#191D27">
      <VStack as="nav" alignItems="start" color="white" height="100%">
        <Box pb={6}>
          <FidesLogoHomeLink />
        </Box>
        {nav.groups.map((group) => (
          // // The group links to its first child's path.
          // const { path } = group.children[0]!;

          // const isActive = group.title === nav.active?.title;

          <Box key={group.title}>{group.title}</Box>
        ))}
      </VStack>
    </Box>
  );
};

export default MainSideNav;
