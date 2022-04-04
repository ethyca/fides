import React, { useEffect, useState } from 'react';
import type { NextPage } from 'next';
import Head from 'next/head';
import {
  Flex,
  Heading,
  Text,
  Stack,
  Box,
  Alert,
  AlertIcon,
  AlertDescription,
  CloseButton,
} from '@fidesui/react';
import Image from 'next/image';

import { useRequestModal, RequestModal } from '../components/RequestModal';
import type { AlertState } from '../types/AlertState';

import config from '../config/config.json';

const Home: NextPage = () => {
  const [alert, setAlert] = useState<AlertState | null>(null);
  const { isOpen, onClose, onOpen, openAction } = useRequestModal();

  useEffect(() => {
    if(alert?.status) {
      const closeAlertTimer = setTimeout(() => setAlert(null), 8000);
      return () => clearTimeout(closeAlertTimer)
    }
  }, [alert])
  
  return (
    <div>
      <Head>
        <title>Privacy Center</title>
        <meta name="description" content="Privacy Center" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header>
        <Flex
          bg="gray.100"
          minHeight={14}
          p={1}
          width="100%"
          justifyContent="center"
          alignItems="center"
        >
          {alert ? (
            <Alert
              status={alert.status}
              minHeight={14}
              maxWidth="5xl"
              zIndex={1}
              position="absolute"
            >
              <AlertIcon />
              <AlertDescription>{alert.description}</AlertDescription>
              <CloseButton
                position="absolute"
                right="8px"
                onClick={() => setAlert(null)}
              />
            </Alert>
          ) : null}
          <Image src="/logo.svg" height="56px" width="304px" alt="Logo" />
        </Flex>
      </header>

      <main>
        <Stack align="center" py={['6', '16']} px={5} spacing={8}>
          <Stack align="center" spacing={3}>
            <Heading
              fontSize={['3xl', '4xl']}
              color="gray.600"
              fontWeight="semibold"
              textAlign="center"
            >
              {config.title}
            </Heading>
            <Text
              fontSize={['small', 'medium']}
              fontWeight="medium"
              maxWidth={624}
              textAlign="center"
              color="gray.600"
            >
              {config.description}
            </Text>
          </Stack>
          <Flex m={-2} flexDirection={['column', 'column', 'row']}>
            {config.actions.map((action) => (
              <Box
                as="button"
                key={action.title}
                bg="white"
                py={8}
                px={6}
                borderRadius={4}
                boxShadow="base"
                maxWidth={['100%', '100%', '100%', 304]}
                transition="box-shadow 50ms"
                cursor="pointer"
                userSelect="none"
                m={2}
                _hover={{
                  boxShadow: 'complimentary-2xl',
                }}
                _focus={{
                  outline: 'none',
                  boxShadow: 'complimentary-2xl',
                }}
                onClick={() => onOpen(action.policy_key)}
              >
                <Stack spacing={7}>
                  <Image
                    src={action.icon_path}
                    alt={action.description}
                    width={54}
                    height={54}
                  />
                  <Stack spacing={1} textAlign="center">
                    <Heading
                      fontSize="large"
                      fontWeight="semibold"
                      lineHeight="28px"
                      color="gray.600"
                    >
                      {action.title}
                    </Heading>
                    <Text fontSize="xs" color="gray.600">
                      {action.description}
                    </Text>
                  </Stack>
                </Stack>
              </Box>
            ))}
          </Flex>
        </Stack>
        <RequestModal
          isOpen={isOpen}
          onClose={onClose}
          openAction={openAction}
          setAlert={setAlert}
        />
      </main>
    </div>
  );
};

export default Home;
