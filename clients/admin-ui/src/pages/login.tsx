import Head from "common/Head";
import Image from "common/Image";
import {
  Button,
  Card,
  Divider,
  Flex,
  Form,
  Input,
  Typography,
  useMessage,
} from "fidesui";
import { motion } from "motion/react";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { ParsedUrlQuery } from "querystring";
import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  login,
  selectToken,
  useAcceptInviteMutation,
  useGetAuthenticationMethodsQuery,
  useLoginMutation,
} from "~/features/auth";
import { usePrefersReducedMotion } from "~/features/common/hooks";
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
    <Flex justify="center" align="center" className="absolute">
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
    </Flex>
  );
};

interface LoginFormValues {
  username: string;
  password: string;
}

const useLogin = () => {
  const [form] = Form.useForm<LoginFormValues>();
  const [loginRequest] = useLoginMutation();
  const [acceptInviteRequest] = useAcceptInviteMutation();
  const [showAnimation, setShowAnimation] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // If the user prefers no motion, don't show the animation
  const reduceMotion = usePrefersReducedMotion();
  const token = useSelector(selectToken);
  const message = useMessage();
  const router = useRouter();
  const dispatch = useDispatch();
  const { username, inviteCode, redirect } = parseQueryParam(router.query);

  const initialValues: LoginFormValues = {
    username: username ?? "",
    password: "",
  };

  const isFromInvite = inviteCode !== undefined;

  const usernameRules = useMemo(
    () => [{ required: true, message: "Username is required" }],
    [],
  );

  const passwordRules = useMemo(
    () =>
      isFromInvite
        ? [
            { required: true, message: "Password is required" },
            {
              min: 8,
              message: "Password must have at least eight characters.",
            },
            {
              pattern: /[0-9]/,
              message: "Password must have at least one number.",
            },
            {
              pattern: /[A-Z]/,
              message: "Password must have at least one capital letter.",
            },
            {
              pattern: /[a-z]/,
              message: "Password must have at least one lowercase letter.",
            },
            {
              pattern: /[\W_]/,
              message: "Password must have at least one symbol.",
            },
          ]
        : [{ required: true, message: "Password is required" }],
    [isFromInvite],
  );

  const handleSubmit = async (values: LoginFormValues) => {
    const credentials = {
      username: values.username,
      password: values.password,
    };

    setIsSubmitting(true);
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
      setShowAnimation(false);
      // eslint-disable-next-line no-console
      console.log(error);
      message.error(
        "Login failed. Please check your credentials and try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

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
    form,
    isFromInvite,
    showAnimation,
    initialValues,
    handleSubmit,
    isSubmitting,
    usernameRules,
    passwordRules,
    username,
  };
};

type OAuthLoginButtonsProps = {
  openidProviders: Array<{
    identifier: string;
    provider: string;
    name: string;
  }>;
};

const OAuthLoginButtons = ({ openidProviders }: OAuthLoginButtonsProps) => {
  if (!openidProviders?.length) {
    return null;
  }

  return (
    <Flex vertical gap={16} className="w-full">
      {openidProviders.map((provider) => (
        <Button
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
        </Button>
      ))}
    </Flex>
  );
};

const Login: NextPage = () => {
  const {
    form,
    isFromInvite,
    showAnimation,
    initialValues,
    handleSubmit,
    isSubmitting,
    usernameRules,
    passwordRules,
    username,
  } = useLogin();
  const [canSubmit, setCanSubmit] = useState(false);
  const {
    data: authMethods,
    isLoading: authMethodsLoading,
    error: authMethodsError,
  } = useGetAuthenticationMethodsQuery(undefined, {
    refetchOnMountOrArgChange: true,
  });
  const { data: openidProviders, isLoading: providersLoading } =
    useGetAllOpenIDProvidersSimpleQuery(undefined, {
      refetchOnMountOrArgChange: true,
    });

  const submitButtonText = isFromInvite ? "Setup user" : "Sign in";

  // Determine if we should show username/password inputs
  // Show them if there was an error fetching auth methods or username/password auth is enabled
  const showUsernamePasswordInputs =
    authMethodsError || authMethods?.username_password;

  // Determine if we should show SSO login buttons
  const showSSOButtons = authMethods?.sso;

  if (authMethodsLoading || providersLoading) {
    return null;
  }

  return (
    <Flex className="w-full" justify="center">
      <Head />

      <main data-testid="Login">
        <Flex
          vertical
          gap={64}
          align="center"
          justify="center"
          className="px-6 py-12"
        >
          <Image src="/logo.svg" alt="Fides logo" width={205} height={46} />
          <Flex vertical align="center" gap="large">
            <Typography.Title level={1}>
              Sign in to your account
            </Typography.Title>
            <Card className="static w-[640px] px-32 py-12">
              <Flex align="center" justify="center">
                <Form
                  form={form}
                  layout="vertical"
                  key={username ?? "login"}
                  initialValues={initialValues}
                  onFinish={handleSubmit}
                  onValuesChange={(
                    _: Partial<LoginFormValues>,
                    allValues: LoginFormValues,
                  ) => {
                    setCanSubmit(!!allValues.username && !!allValues.password);
                  }}
                  className="w-full"
                >
                  <Flex vertical>
                    {showUsernamePasswordInputs && (
                      <>
                        <Form.Item
                          name="username"
                          label="Username"
                          rules={usernameRules}
                        >
                          <Input
                            size="large"
                            disabled={isFromInvite}
                            data-testid="input-username"
                            autoComplete="username"
                          />
                        </Form.Item>
                        <Form.Item
                          name="password"
                          label={isFromInvite ? "Set new password" : "Password"}
                          rules={passwordRules}
                        >
                          <Input.Password
                            size="large"
                            autoComplete={
                              isFromInvite ? "new-password" : "current-password"
                            }
                            data-testid="input-password"
                          />
                        </Form.Item>
                        <Flex justify="center" align="center">
                          <motion.div
                            className="h-8 w-full"
                            animate={
                              showAnimation
                                ? { width: ["100%", "32px"] }
                                : { width: ["32px", "100%"] }
                            }
                          >
                            <Button
                              htmlType="submit"
                              type="primary"
                              disabled={!canSubmit}
                              data-testid="sign-in-btn"
                              loading={isSubmitting}
                              className="w-full"
                            >
                              {showAnimation ? "" : submitButtonText}
                            </Button>
                          </motion.div>
                          {showAnimation ? <Animation /> : null}
                        </Flex>
                      </>
                    )}
                    {showUsernamePasswordInputs &&
                      showSSOButtons &&
                      openidProviders && <Divider>or</Divider>}
                    {showSSOButtons && openidProviders && (
                      <OAuthLoginButtons openidProviders={openidProviders} />
                    )}
                  </Flex>
                </Form>
              </Flex>
            </Card>
          </Flex>
        </Flex>
      </main>
    </Flex>
  );
};

export default Login;
