import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  Link,
  ListItem,
  UnorderedList,
  VStack,
} from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";

import logoImage from "~/../public/logo-white.svg";
import Image from "~/features/common/Image";

import { useNav } from "./hooks";
import { ActiveNav, NavGroup, NavGroupChild } from "./nav-config";
import { INDEX_ROUTE } from "./routes";

const LINK_HOVER_BACKGROUND_COLOR = "#28303F";
const LINK_ACTIVE_BACKGROUND_COLOR = "#7745F0";
const LINK_COLOR = "#CBD5E0";

const FidesLogoHomeLink = () => (
  <Box px={2}>
    <NextLink href={INDEX_ROUTE} passHref>
      {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
      <Link display="flex">
        <Image src={logoImage} alt="Fides Logo" />
      </Link>
    </NextLink>
  </Box>
);

export const NavSideBarLink = ({
  childGroup,
  isActive,
}: {
  childGroup: NavGroupChild;
  isActive: boolean;
}) => {
  const { title, path } = childGroup;
  return (
    <ListItem listStyleType="none">
      <NextLink href={path} passHref>
        <Button
          as="a"
          height="34px"
          variant="ghost"
          fontWeight="normal"
          fontSize="sm"
          px={2}
          width="100%"
          justifyContent="start"
          color={LINK_COLOR}
          isActive={isActive}
          _hover={{
            backgroundColor: LINK_HOVER_BACKGROUND_COLOR,
          }}
          _active={{
            color: "white",
            backgroundColor: LINK_ACTIVE_BACKGROUND_COLOR,
          }}
          data-testid={`${title}-nav-link`}
        >
          {title}
        </Button>
      </NextLink>
    </ListItem>
  );
};

const NavGroupMenu = ({
  group,
  active,
}: {
  group: NavGroup;
  active: ActiveNav | undefined;
}) => (
  <AccordionItem border="none" data-testid={`${group.title}-nav-group`}>
    <h3>
      <AccordionButton px={2} py={3}>
        <Box
          fontSize="xs"
          fontWeight="bold"
          textTransform="uppercase"
          as="span"
          flex="1"
          textAlign="left"
        >
          {group.title}
        </Box>
        <AccordionIcon />
      </AccordionButton>
    </h3>
    <AccordionPanel fontSize="sm" p={0}>
      <UnorderedList m={0}>
        {group.children.map((child) => {
          const isActive = child.exact
            ? active?.path === child.path
            : !!active?.path?.startsWith(child.path);
          return (
            <NavSideBarLink
              isActive={isActive}
              key={child.path}
              childGroup={child}
            />
          );
        })}
      </UnorderedList>
    </AccordionPanel>
  </AccordionItem>
);

/** Inner component which we export for component testing */
export const UnconnectedMainSideNav = ({
  groups,
  active,
}: {
  groups: NavGroup[];
  active: ActiveNav | undefined;
}) => (
  <Box p={4} minWidth="200px" maxWidth="200px" backgroundColor="#191D27">
    <VStack as="nav" alignItems="start" color="white" height="100%">
      <Box pb={6}>
        <FidesLogoHomeLink />
      </Box>
      <Accordion
        allowMultiple
        width="100%"
        defaultIndex={[...Array(groups.length).keys()]}
        overflowY="auto"
      >
        {groups.map((group) => (
          <NavGroupMenu key={group.title} group={group} active={active} />
        ))}
      </Accordion>
    </VStack>
  </Box>
);

const MainSideNav = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });

  return <UnconnectedMainSideNav {...nav} />;
};

export default MainSideNav;
