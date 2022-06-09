import { Button, Flex } from '@fidesui/react';
import NextLink from 'next/link';
import { useRouter } from 'next/router';
import React from 'react';

import Header from './Header';
import { ArrowDownLineIcon } from './Icon';

const NavBar = () => {
  const router = useRouter();

  return (
    <>
      <Header />
      <Flex
        borderBottom='1px'
        borderTop='1px'
        px={9}
        py={1}
        borderColor='gray.100'
      >
        <NextLink href='/' passHref>
          <Button
            as='a'
            variant='ghost'
            mr={4}
            colorScheme={
              router && router.pathname === '/' ? 'complimentary' : 'ghost'
            }
          >
            Subject Requests
          </Button>
        </NextLink>

        <NextLink href='#' passHref>
          <Button as='a' variant='ghost' disabled mr={4}>
            Datastore Connections
          </Button>
        </NextLink>

        <NextLink href='/user-management' passHref>
          <Button
            as='a'
            variant='ghost'
            mr={4}
            colorScheme={
              router && router.pathname.startsWith('/user-management')
                ? 'complimentary'
                : 'ghost'
            }
          >
            User Management
          </Button>
        </NextLink>

        <NextLink href='#' passHref>
          <Button
            as='a'
            variant='ghost'
            disabled
            rightIcon={<ArrowDownLineIcon />}
          >
            More
          </Button>
        </NextLink>
      </Flex>
    </>
  );
};

export default NavBar;
