import {
  Box,
  Button,
  chakra,
  Flex,
  Heading,
  Stack,
  useToast,
} from "@fidesui/react";
import Head from "common/Head";
import Image from "common/Image";
import { Formik } from "formik";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { ParsedUrlQuery } from "querystring";
import { useDispatch, useSelector } from "react-redux";
import * as Yup from "yup";

import {
  login,
  selectToken,
  useAcceptInviteMutation,
  useLoginMutation,
} from "~/features/auth";
import { CustomTextInput } from "~/features/common/form/inputs";
import { passwordValidation } from "~/features/common/form/validation";

const parseQueryParam = (query: ParsedUrlQuery) => {
  const {
    username: rawUsername,
    invite_code: rawInviteCode,
    redirect: rawRedirect,
  } = query;
  const redirectDecoded =
    typeof rawRedirect === "string"
      ? decodeURIComponent(rawRedirect)
      : undefined;
  return {
    username: typeof rawUsername === "string" ? rawUsername : undefined,
    inviteCode: typeof rawInviteCode === "string" ? rawInviteCode : undefined,
    // Make sure we don't keep redirecting to the login page!
    redirect: redirectDecoded === "/login" ? undefined : redirectDecoded,
  };
};

const useLogin = () => {
  const [loginRequest] = useLoginMutation();
  const [acceptInviteRequest] = useAcceptInviteMutation();
  const token = useSelector(selectToken);
  const toast = useToast();
  const router = useRouter();
  const dispatch = useDispatch();
  const { username, inviteCode, redirect } = parseQueryParam(router.query);

  const initialValues = {
    username: username ?? "",
    password: "",
  };

  const isFromInvite = inviteCode !== undefined;

  const onSubmit = async (values: typeof initialValues) => {
    const credentials = {
      username: values.username,
      password: values.password,
    };

    try {
      let user;
      if (isFromInvite) {
        user = await acceptInviteRequest({
          ...credentials,
          inviteCode,
        }).unwrap();
      } else {
        user = await loginRequest(credentials).unwrap();
      }
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

  const validationSchema = Yup.object().shape({
    username: Yup.string().required().label("Username"),
    password: isFromInvite
      ? passwordValidation.label("Password")
      : Yup.string().required().label("Password"),
  });

  if (token) {
    const destination = redirect ?? "/";
    router.push(destination);
  }

  return {
    isFromInvite,
    inviteCode,
    initialValues,
    onSubmit,
    validationSchema,
  };
};

const Login: NextPage = () => {
  const { isFromInvite, inviteCode, ...formikProps } = useLogin();

  return (
    <Formik {...formikProps} enableReinitialize>
      {({ handleSubmit, isValid, isSubmitting }) => (
        <div>
          <Head />

          <main data-testid="Login">
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
                  Sign in to your account
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
                        Sign in to your account
                      </Heading>
                    </Stack>
                    <chakra.form
                      onSubmit={handleSubmit}
                      maxW={["xs", "xs", "100%"]}
                      width="100%"
                    >
                      <Stack spacing={6}>
                        <CustomTextInput
                          name="username"
                          label="Username"
                          variant="stacked"
                          size="md"
                          disabled={isFromInvite}
                        />
                        <CustomTextInput
                          name="password"
                          label={isFromInvite ? "Set new password" : "Password"}
                          type="password"
                          variant="stacked"
                          size="md"
                        />
                        <Button
                          type="submit"
                          bg="primary.800"
                          _hover={{ bg: "primary.400" }}
                          _active={{ bg: "primary.500" }}
                          disabled={!isValid}
                          colorScheme="primary"
                          data-testid="sign-in-btn"
                          isLoading={isSubmitting}
                        >
                          {isFromInvite ? "Setup user" : "Sign in"}
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
