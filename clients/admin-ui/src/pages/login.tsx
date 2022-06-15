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
} from "@fidesui/react";
import { Formik } from "formik";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { login, selectToken, useLoginMutation } from "../features/auth";
import Head from "../features/common/Head";
import Image from "../features/common/Image";

const useLogin = () => {
  const [loginRequest, { isLoading }] = useLoginMutation();
  const token = useSelector(selectToken);
  const toast = useToast();
  const router = useRouter();
  const dispatch = useDispatch();

  const initialValues = {
    email: "",
    password: "",
  };

  const onSubmit = async (values: typeof initialValues) => {
    const credentials = {
      username: values.email,
      password: values.password,
    };
    try {
      const user = await loginRequest(credentials).unwrap();
      dispatch(login(user));
    } catch (error) {
      // eslint-disable-next-line no-console
      console.log(error);
      toast({
        status: "error",
        description:
          "Login failed. Please check your credentials and try again.",
      });
    }
  };

  const validate = (values: typeof initialValues) => {
    const errors: {
      email?: string;
      password?: string;
    } = {};

    if (!values.email) {
      errors.email = "Required";
    }

    if (!values.password) {
      errors.password = "Required";
    }

    return errors;
  };

  if (token) {
    router.push("/");
  }

  return {
    initialValues,
    isLoading,
    onSubmit,
    validate,
  };
};

const Login: NextPage = () => {
  const { isLoading, ...formikProps } = useLogin();
  return (
    <Formik {...formikProps}>
      {({
        errors,
        handleBlur,
        handleChange,
        handleSubmit,
        touched,
        values,
      }) => (
        <div>
          <Head />

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
              <Box display={["none", "none", "block"]}>
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
                  display={["none", "none", "block"]}
                >
                  Sign into your account
                </Heading>
                <Box
                  bg="white"
                  py={12}
                  px={[0, 0, 40]}
                  width={["100%", "100%", 640]}
                  borderRadius={4}
                  position={["absolute", "absolute", "inherit"]}
                  top={0}
                  bottom={0}
                  left={0}
                  right={0}
                  boxShadow="base"
                >
                  <Stack align="center" justify="center" spacing={8}>
                    <Stack display={["block", "block", "none"]} spacing={12}>
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
                      maxW={["xs", "xs", "100%"]}
                      width="100%"
                    >
                      <Stack spacing={6}>
                        <FormControl
                          isInvalid={touched.email && Boolean(errors.email)}
                        >
                          <FormLabel htmlFor="email" fontWeight="medium">
                            Username
                          </FormLabel>
                          <Input
                            id="email"
                            name="email"
                            aria-label="email"
                            focusBorderColor="primary.500"
                            placeholder="username"
                            onChange={handleChange}
                            onBlur={handleBlur}
                            value={values.email}
                            isInvalid={touched.email && Boolean(errors.email)}
                          />
                          <FormErrorMessage>{errors.email}</FormErrorMessage>
                        </FormControl>

                        <FormControl
                          isInvalid={
                            touched.password && Boolean(errors.password)
                          }
                        >
                          <FormLabel htmlFor="password" fontWeight="medium">
                            Password
                          </FormLabel>
                          <Input
                            id="password"
                            name="password"
                            focusBorderColor="primary.500"
                            type="password"
                            aria-label="password"
                            value={values.password}
                            onChange={handleChange}
                            onBlur={handleBlur}
                            isInvalid={
                              touched.password && Boolean(errors.password)
                            }
                          />
                          <FormErrorMessage>{errors.password}</FormErrorMessage>
                        </FormControl>

                        <Button
                          type="submit"
                          bg="primary.800"
                          _hover={{ bg: "primary.400" }}
                          _active={{ bg: "primary.500" }}
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
      )}
    </Formik>
  );
};

export default Login;
