import Head from "common/Head";
import Image from "common/Image";
import {
  AntButton,
  Box,
  Center,
  chakra,
  Flex,
  Heading,
  Stack,
  usePrefersReducedMotion,
  useToast,
} from "fidesui";
import { Formik } from "formik";
// Framer is bundled as part of chakra. TODO: had trouble with package.json's when
// trying to make framer a first level dev dependency
// eslint-disable-next-line import/no-extraneous-dependencies
import { motion } from "framer-motion";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { ParsedUrlQuery } from "querystring";
import { useEffect, useState } from "react";
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
import { useGetAllOpenIDProvidersSimpleQuery } from "~/features/openid-authentication/openprovider.slice";

const parseQueryParam = (query: ParsedUrlQuery) => {
  const validPathRegex = /^\/[\w/-]*$/;
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
    redirect:
      redirectDecoded && validPathRegex.test(redirectDecoded)
        ? redirectDecoded
        : undefined,
  };
};

const Animation = () => {
  const primary800 = "rgba(17, 20, 57, 1)";
  const icon = {
    hidden: {
      opacity: 0,
      pathLength: 0,
      fill: "rgba(255, 255, 255, 0)",
    },
    visible: {
      opacity: 1,
      pathLength: 1,
      fill: primary800,
    },
  };
  return (
    <Center position="absolute">
      <motion.svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 64 64"
        // eslint-disable-next-line tailwindcss/no-custom-classname
        className="item"
        width={46}
        height={46}
        style={{
          stroke: primary800,
          strokeWidth: 1,
        }}
      >
        <motion.path
          d="M0 0H0V64H64V0Z"
          variants={icon}
          initial="hidden"
          animate="visible"
          transition={{
            default: { duration: 2, ease: "easeInOut" },
            fill: { duration: 2, ease: [1, 0, 0.8, 1] },
          }}
        />
      </motion.svg>
    </Center>
  );
};

const useLogin = () => {
  const [loginRequest] = useLoginMutation();
  const [acceptInviteRequest] = useAcceptInviteMutation();
  const [showAnimation, setShowAnimation] = useState(false);
  // If the user prefers no motion, don't show the animation
  const reduceMotion = usePrefersReducedMotion();
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
      setShowAnimation(true);
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

  useEffect(() => {
    if (token) {
      const destination = redirect ?? "/";
      if (showAnimation && !reduceMotion) {
        const timer = setTimeout(() => {
          router.push(destination).then(() => {
            setShowAnimation(false);
          });
        }, 2000);
        return () => {
          clearTimeout(timer);
        };
      }
      router.push(destination);
    }
    return () => {};
  }, [token, router, redirect, showAnimation, reduceMotion]);

  return {
    isFromInvite,
    showAnimation,
    inviteCode,
    initialValues,
    onSubmit,
    validationSchema,
  };
};

const OAuthLoginButtons = () => {
  const { data: openidProviders } = useGetAllOpenIDProvidersSimpleQuery();

  return (
    <Center>
      <Stack spacing={4} width="100%">
        {openidProviders?.map((provider) => (
          <AntButton
            key={provider.identifier}
            href={`/api/v1/plus/openid-provider/${provider.identifier}/authorize`}
            icon={
              <Image
                src={`/images/oauth-login/${provider.provider}.svg`}
                alt={`${provider.provider} icon`}
                width={20}
                height={20}
              />
            }
            className="w-full"
          >
            Sign in with {provider.name}
          </AntButton>
        ))}
      </Stack>
    </Center>
  );
};

const Login: NextPage = () => {
  const { isFromInvite, showAnimation, inviteCode, ...formikProps } =
    useLogin();

  const submitButtonText = isFromInvite ? "Setup user" : "Sign in";

  return (
    <Formik {...formikProps} enableReinitialize>
      {({ handleSubmit, isValid, isSubmitting, dirty }) => (
        <Flex width="100%" justifyContent="center">
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
                  width={156}
                  height={48}
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
                          width={156}
                          height={48}
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
                          autoComplete={
                            isFromInvite ? "new-password" : "current-password"
                          }
                          type="password"
                          variant="stacked"
                          size="md"
                        />
                        <Center>
                          <motion.div
                            className="w-full"
                            animate={
                              showAnimation
                                ? {
                                    width: ["100%", "10%"],
                                    borderRadius: ["5%", "0%"],
                                  }
                                : undefined
                            }
                          >
                            <AntButton
                              htmlType="submit"
                              type="primary"
                              disabled={!isValid || !dirty}
                              data-testid="sign-in-btn"
                              loading={isSubmitting}
                              className="w-full"
                            >
                              {showAnimation ? "" : submitButtonText}
                            </AntButton>
                          </motion.div>
                          {showAnimation ? <Animation /> : null}
                        </Center>
                        <OAuthLoginButtons />
                      </Stack>
                    </chakra.form>
                  </Stack>
                </Box>
              </Stack>
            </Stack>
          </main>
        </Flex>
      )}
    </Formik>
  );
};

export default Login;
