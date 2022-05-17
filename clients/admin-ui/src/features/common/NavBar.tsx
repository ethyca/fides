import React from 'react';
import {Flex, Button } from '@fidesui/react';
import { useSession } from "next-auth/react"
import NextLink from 'next/link'
import { useRouter } from "next/router";

import { ArrowDownLineIcon } from '../../features/common/Icon';

import Header from './Header';

const NavBar = () => {
  const { data: session } = useSession();
  const router = useRouter();
  const username: string | any = session?.username

  return (
  <>
    <Header username={username} />
    <Flex
      borderBottom="1px"
      borderTop="1px"
      px={9}
      py={1}
      borderColor="gray.100"
    >
      <NextLink href="/" passHref>
        <Button as="a" variant="ghost" mr={4} colorScheme={router.pathname === "/" ? "complimentary" : "ghost"}>
          Subject Requests
        </Button>
      </NextLink>

      <NextLink href="#" passHref>
        <Button as="a" variant="ghost" disabled mr={4}>
          Datastore Connections
        </Button>
      </NextLink>

      <NextLink href="/user-management" passHref>
        <Button as="a" variant="ghost" mr={4} colorScheme={router.pathname.startsWith("/user-management") ? "complimentary" : "ghost"}>
          User Management
        </Button>
      </NextLink>

      <NextLink href="#" passHref>
        <Button as="a" variant="ghost" disabled rightIcon={<ArrowDownLineIcon />}>
          More
        </Button>
      </NextLink>
    </Flex>
  </>
  )
}

export default NavBar;