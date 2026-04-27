import Head from "common/Head";
import Image from "common/Image";
import {
  Button,
  Card,
  Divider,
  Flex,
  Form,
  Input,
  Spin,
  Typography,
  useMessage,
  usePrefersReducedMotion,
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
  useResetPasswordWithTokenMutation,
  useValidateInviteQuery,
  useValidateResetTokenQuery,
} from "~/features/auth";
import { passwordRules as strongPasswordRules } from "~/features/common/form/validation";
import { getErrorMessage } from "~/features/common/helpers";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { useGetAllOpenIDProvidersSimpleQuery } from "~/features/openid-authentication/openprovider.slice";
import { RTKErrorResult } from "~/types/errors/api";

const parseQueryParam = (query: ParsedUrlQuery) => {
  const validPathRegex = /^\/[\w/-]*$/;
  const {
    username: rawUsername,
    invite_code: rawInviteCode,
    reset_token: rawResetToken,
    redirect: rawRedirect,
  } = query;
  const redirectDecoded =
    typeof rawRedirect === "string"
      ? decodeURIComponent(rawRedirect)
      : undefined;
  return {
    username: typeof rawUsername === "string" ? rawUsername : undefined,
    inviteCode: typeof rawInviteCode === "string" ? rawInviteCode : undefined,
    resetToken: typeof rawResetToken === "string" ? rawResetToken : undefined,
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
  const [resetPasswordRequest] = useResetPasswordWithTokenMutation();
  const [showAnimation, setShowAnimation] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  // If the user prefers no motion, don't show the animation
  const reduceMotion = usePrefersReducedMotion();
  const token = useSelector(selectToken);
  const message = useMessage();
  const router = useRouter();
  const dispatch = useDispatch();
  const { username, inviteCode, resetToken, redirect } = parseQueryParam(
    router.query,
  );

  const initialValues: LoginFormValues = {
    username: username ?? "",
    password: "",
  };

  const isFromInvite = inviteCode !== undefined;
  const isResetPassword = resetToken !== undefined;

  const {
    data: inviteValidation,
    isLoading: isValidatingInvite,
    isError: inviteValidationErrored,
  } = useValidateInviteQuery(
    { username: username ?? "", inviteCode: inviteCode ?? "" },
    { skip: !isFromInvite || !username },
  );
  const {
    data: resetTokenValidation,
    isLoading: isValidatingResetToken,
    isError: resetTokenValidationErrored,
  } = useValidateResetTokenQuery(
    { username: username ?? "", token: resetToken ?? "" },
    { skip: !isResetPassword || !username },
  );

  // An invite link with no username in the query string is inherently invalid;
  // same for a reset link. Treat missing-username as an invalid token.
  const missingUsername = (isFromInvite || isResetPassword) && !username;

  let tokenValidation;
  let validationErrored = false;
  if (isFromInvite) {
    tokenValidation = inviteValidation;
    validationErrored = inviteValidationErrored;
  } else if (isResetPassword) {
    tokenValidation = resetTokenValidation;
    validationErrored = resetTokenValidationErrored;
  }

  const isValidatingToken =
    (isFromInvite && isValidatingInvite) ||
    (isResetPassword && isValidatingResetToken);

  // Treat a network/server error from the validation endpoint as an invalid
  // token. Failing closed avoids showing the password form for a token whose
  // status we couldn't confirm.
  const tokenIsInvalid =
    missingUsername ||
    validationErrored ||
    (tokenValidation !== undefined && !tokenValidation.valid);
  const tokenInvalidReason = missingUsername
    ? "invalid"
    : (tokenValidation?.reason ?? null);

  const usernameRules = useMemo(
    () => [{ required: true, message: "Username is required" }],
    [],
  );

  const loginPasswordRules = useMemo(
    () =>
      isFromInvite || isResetPassword
        ? strongPasswordRules
        : [{ required: true, message: "Password is required" }],
    [isFromInvite, isResetPassword],
  );

  const handleSubmit = async (values: LoginFormValues) => {
    const credentials = {
      username: values.username,
      password: values.password,
    };

    setIsSubmitting(true);
    try {
      let user;
      if (isResetPassword) {
        user = await resetPasswordRequest({
          username: username!,
          token: resetToken!,
          new_password: values.password,
        }).unwrap();
      } else if (isFromInvite) {
        user = await acceptInviteRequest({
          ...credentials,
          inviteCode: inviteCode!,
        }).unwrap();
      } else {
        user = await loginRequest(credentials).unwrap();
      }
      setShowAnimation(true);
      dispatch(login(user));
    } catch (error) {
      setShowAnimation(false);
      // eslint-disable-next-line no-console
      console.error(error);
      let errorMsg: string;
      if (isFromInvite) {
        // Invite and reset-password flows may surface backend error detail
        // (e.g. expired/invalid token) since it is actionable to the user.
        errorMsg = getErrorMessage(
          error as RTKErrorResult["error"],
          "Setup failed. Please try the invite link again.",
        );
      } else if (isResetPassword) {
        errorMsg = getErrorMessage(
          error as RTKErrorResult["error"],
          "Password reset failed. The link may have expired. Please request a new one.",
        );
      } else {
        // Always show a generic message for standard login failures to avoid
        // leaking backend details (SSO config, authorization state, etc.)
        errorMsg = "Login failed. Please check your credentials and try again.";
      }
      message.error(errorMsg);
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
    isResetPassword,
    showAnimation,
    initialValues,
    handleSubmit,
    isSubmitting,
    usernameRules,
    passwordRules: loginPasswordRules,
    username,
    isValidatingToken,
    tokenIsInvalid,
    tokenInvalidReason,
  };
};

type InvalidTokenMessageProps = {
  isFromInvite: boolean;
  reason: "expired" | "invalid" | null;
};

const InvalidTokenMessage = ({
  isFromInvite,
  reason,
}: InvalidTokenMessageProps) => {
  const isExpired = reason === "expired";
  const title = isExpired
    ? "This link has expired"
    : "This link is no longer valid";

  let body: string;
  if (isFromInvite) {
    body = isExpired
      ? "Please ask your administrator to send you a new invite."
      : "This invite link is invalid or has already been used. Please ask your administrator to send you a new invite.";
  } else {
    body = isExpired
      ? "Password reset links expire for your security. Please request a new one."
      : "This password reset link is invalid or has already been used. Please request a new one.";
  }

  return (
    <Flex
      vertical
      align="center"
      gap="middle"
      data-testid="invalid-token-message"
    >
      <Typography.Title level={4} className="text-center">
        {title}
      </Typography.Title>
      <Typography.Text className="text-center">{body}</Typography.Text>
      {!isFromInvite && (
        <RouterLink href="/forgot-password">
          <Button type="primary" data-testid="request-new-link-btn">
            Request a new link
          </Button>
        </RouterLink>
      )}
      {isFromInvite && (
        <RouterLink href="/login">
          <Button type="primary" data-testid="return-to-login-btn">
            Return to sign in
          </Button>
        </RouterLink>
      )}
    </Flex>
  );
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
    isResetPassword,
    showAnimation,
    initialValues,
    handleSubmit,
    isSubmitting,
    passwordRules: loginPasswordRules,
    usernameRules,
    username,
    isValidatingToken,
    tokenIsInvalid,
    tokenInvalidReason,
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

  let submitButtonText = "Sign in";
  if (isFromInvite) {
    submitButtonText = "Setup user";
  } else if (isResetPassword) {
    submitButtonText = "Reset password";
  }

  // Determine if we should show username/password inputs
  // Show them if there was an error fetching auth methods or username/password auth is enabled
  const showUsernamePasswordInputs =
    authMethodsError || authMethods?.username_password;

  // Determine if we should show SSO login buttons
  const showSSOButtons = authMethods?.sso;

  if (authMethodsLoading || providersLoading) {
    return null;
  }

  // For invite/reset flows, validate the token before rendering the form so the
  // user doesn't fill out a password for an expired or already-used link.
  const isTokenFlow = isFromInvite || isResetPassword;
  const showTokenLoading = isTokenFlow && isValidatingToken;
  const showInvalidToken = isTokenFlow && !isValidatingToken && tokenIsInvalid;

  let pageTitle: string;
  if (showInvalidToken) {
    pageTitle = isFromInvite ? "Invite link" : "Password reset";
  } else if (isResetPassword) {
    pageTitle = "Set a new password";
  } else {
    pageTitle = "Sign in to your account";
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
            <Typography.Title level={1}>{pageTitle}</Typography.Title>
            <Card className="static w-[640px] px-32 py-12">
              {showTokenLoading && (
                <Flex
                  align="center"
                  justify="center"
                  className="w-full py-8"
                  data-testid="token-validating"
                >
                  <Spin size="large" />
                </Flex>
              )}
              {showInvalidToken && (
                <InvalidTokenMessage
                  isFromInvite={isFromInvite}
                  reason={tokenInvalidReason}
                />
              )}
              {!showTokenLoading && !showInvalidToken && (
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
                      if (isResetPassword) {
                        setCanSubmit(!!allValues.password);
                      } else {
                        setCanSubmit(
                          !!allValues.username && !!allValues.password,
                        );
                      }
                    }}
                    className="w-full"
                  >
                    <Flex vertical>
                      {showUsernamePasswordInputs && (
                        <>
                          {!isResetPassword && (
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
                          )}
                          <Form.Item
                            name="password"
                            label={
                              isFromInvite || isResetPassword
                                ? "Set new password"
                                : "Password"
                            }
                            rules={loginPasswordRules}
                          >
                            <Input.Password
                              size="large"
                              autoComplete={
                                isFromInvite || isResetPassword
                                  ? "new-password"
                                  : "current-password"
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
                          {!isFromInvite && !isResetPassword && (
                            <Flex justify="center" className="mt-4">
                              <RouterLink href="/forgot-password">
                                <Button
                                  type="link"
                                  data-testid="forgot-password-btn"
                                >
                                  Forgot password?
                                </Button>
                              </RouterLink>
                            </Flex>
                          )}
                        </>
                      )}
                      {showUsernamePasswordInputs &&
                        showSSOButtons &&
                        openidProviders &&
                        !isResetPassword && <Divider>or</Divider>}
                      {showSSOButtons &&
                        openidProviders &&
                        !isResetPassword && (
                          <OAuthLoginButtons
                            openidProviders={openidProviders}
                          />
                        )}
                    </Flex>
                  </Form>
                </Flex>
              )}
            </Card>
          </Flex>
        </Flex>
      </main>
    </Flex>
  );
};

export default Login;
