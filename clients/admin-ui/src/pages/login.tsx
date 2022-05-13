import {
  Box,
  Button,
  chakra,
  Flex,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  Stack,
  useToast,
} from '@fidesui/react';
import { useFormik } from 'formik';
import type { NextPage } from 'next';
import Head from 'next/head';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { signIn } from 'next-auth/react';
import React, { useState } from 'react';

const useLogin = () => {
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const router = useRouter();
  const formik = useFormik({
    initialValues: {
      email: '',
      password: '',
    },
    onSubmit: async (values) => {
      setIsLoading(true);
      const response = await signIn<'credentials'>('credentials', {
        ...values,
        callbackUrl: `${window.location.origin}`,
        redirect: false,
      });
      setIsLoading(false);
      if (response && response.ok) {
        router.push('/');
        toast.closeAll();
      } else {
        toast({
          status: 'error',
          description:
            'Login failed. Please check your credentials and try again.',
        });
      }
    },
    validate: (values) => {
      const errors: {
        email?: string;
        password?: string;
      } = {};

      if (!values.email) {
        errors.email = 'Required';
      }
      /* Disable email validation while client-level authentication is required
       *
       * else if (
       *   !/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(values.email)
       * ) {
       *   errors.email = 'Invalid email address';
       * }
       */

      if (!values.password) {
        errors.password = 'Required';
      }

      return errors;
    },
  });

  return { ...formik, isLoading };
};

const Login: NextPage = () => {
  const {
    errors,
    handleBlur,
    handleChange,
    handleSubmit,
    isLoading,
    touched,
    values,
  } = useLogin();
  return (
    <div>
      <Head>
        <title>FidesUI App</title>
        <meta name="description" content="Generated from FidesUI template" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <Stack
          spacing={16}
          mx="auto"
          maxW="lg"
          py={12}
          px={6}
          align="center"
          minH="100vh"
          justify="center"
        >
          <Box display={['none', 'none', 'block']}>
            <Image
              src="/logo.svg"
              alt="FidesUI logo"
              width="156px"
              height="48px"
            />
          </Box>
          <Stack align="center" spacing={[0, 0, 6]}>
            <Heading
              fontSize="4xl"
              colorScheme="primary"
              display={['none', 'none', 'block']}
            >
              Sign into your account
            </Heading>
            <Box
              bg="white"
              py={12}
              px={[0, 0, 40]}
              width={['100%', '100%', 640]}
              borderRadius={4}
              position={['absolute', 'absolute', 'inherit']}
              top={0}
              bottom={0}
              left={0}
              right={0}
              boxShadow="base"
            >
              <Stack align="center" justify="center" spacing={8}>
                <Stack display={['block', 'block', 'none']} spacing={12}>
                  <Flex justifyContent="center">
                    <Image
                      src="/logo.svg"
                      alt="FidesUI logo"
                      width="156px"
                      height="48px"
                    />
                  </Flex>
                  <Heading fontSize="3xl" colorScheme="primary">
                    Sign into your account
                  </Heading>
                </Stack>
                <chakra.form
                  onSubmit={handleSubmit}
                  maxW={['xs', 'xs', '100%']}
                  width="100%"
                >
                  <Stack spacing={6}>
                    <FormControl
                      id="email"
                      isInvalid={touched.email && Boolean(errors.email)}
                    >
                      <FormLabel htmlFor="email" fontWeight="medium">
                        Email address
                      </FormLabel>
                      <Input
                        id="email"
                        name="email"
                        focusBorderColor="primary.500"
                        placeholder="you@yourdomain.com"
                        onChange={handleChange}
                        onBlur={handleBlur}
                        value={values.email}
                        isInvalid={touched.email && Boolean(errors.email)}
                      />
                      <FormErrorMessage>{errors.email}</FormErrorMessage>
                    </FormControl>

                    <FormControl
                      id="password"
                      isInvalid={touched.password && Boolean(errors.password)}
                    >
                      <FormLabel htmlFor="password" fontWeight="medium">
                        Password
                      </FormLabel>
                      <Input
                        focusBorderColor="primary.500"
                        type="password"
                        value={values.password}
                        onChange={handleChange}
                        onBlur={handleBlur}
                        isInvalid={touched.password && Boolean(errors.password)}
                      />
                      <FormErrorMessage>{errors.password}</FormErrorMessage>
                    </FormControl>

                    <Button
                      type="submit"
                      bg="primary.800"
                      _hover={{ bg: 'primary.400' }}
                      _active={{ bg: 'primary.500' }}
                      disabled={!values.email || !values.password}
                      isLoading={isLoading}
                      colorScheme="primary"
                    >
                      Sign in
                    </Button>
                  </Stack>
                </chakra.form>
              </Stack>
            </Box>
          </Stack>
        </Stack>
      </main>
    </div>
  );
};

export default Login;
