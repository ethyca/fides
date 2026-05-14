import Head from "common/Head";
import Image from "common/Image";
import { Button, Card, Flex, Spin, Typography } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  login,
  selectToken,
  useVerifyEmailWithTokenMutation,
} from "~/features/auth";
import { RouterLink } from "~/features/common/nav/RouterLink";

type VerifyState = "pending" | "success" | "error" | "missing-params";

const parseQuery = (query: Record<string, string | string[] | undefined>) => {
  const { username: rawUsername, token: rawToken } = query;
  return {
    username: typeof rawUsername === "string" ? rawUsername : undefined,
    token: typeof rawToken === "string" ? rawToken : undefined,
  };
};

const VerifyEmail: NextPage = () => {
  const router = useRouter();
  const dispatch = useDispatch();
  const token = useSelector(selectToken);
  const [verifyEmailWithToken] = useVerifyEmailWithTokenMutation();
  const [state, setState] = useState<VerifyState>("pending");

  useEffect(() => {
    if (!router.isReady) {
      return;
    }
    const { username, token: verificationToken } = parseQuery(router.query);
    if (!username || !verificationToken) {
      setState("missing-params");
      return;
    }
    // Fire the verification once on mount. We intentionally don't depend on
    // verifyEmailWithToken in the deps array — RTK Query hook tuples are
    // stable references in practice and we only want this to run once.
    let cancelled = false;
    (async () => {
      try {
        const result = await verifyEmailWithToken({
          username,
          token: verificationToken,
        }).unwrap();
        if (cancelled) {
          return;
        }
        dispatch(login(result));
        setState("success");
      } catch {
        if (cancelled) {
          return;
        }
        setState("error");
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router.isReady, router.query.username, router.query.token]);

  useEffect(() => {
    if (state === "success" && token) {
      router.replace("/");
    }
  }, [state, token, router]);

  let titleText = "Verifying your email…";
  if (state === "success") {
    titleText = "Email verified";
  } else if (state === "error") {
    titleText = "Verification failed";
  } else if (state === "missing-params") {
    titleText = "Invalid verification link";
  }

  return (
    <Flex className="w-full" justify="center">
      <Head />

      <main data-testid="VerifyEmail">
        <Flex
          vertical
          gap={64}
          align="center"
          justify="center"
          className="px-6 py-12"
        >
          <Image
            src="/logo.svg"
            alt="Fides logo"
            width={205}
            height={46}
            loading="eager"
          />
          <Flex vertical align="center" gap="large">
            <Typography.Title level={1}>{titleText}</Typography.Title>
            <Card className="static w-[640px] px-32 py-12">
              <Flex align="center" justify="center">
                {state === "pending" && (
                  <Flex vertical gap={16} align="center" className="w-full">
                    <Spin size="large" data-testid="verifying-spinner" />
                    <Typography.Text className="text-center">
                      Please wait while we verify your email address.
                    </Typography.Text>
                  </Flex>
                )}
                {state === "success" && (
                  <Flex vertical gap={16} align="center" className="w-full">
                    <Typography.Text className="text-center">
                      Your email has been verified. Redirecting you to the
                      dashboard…
                    </Typography.Text>
                  </Flex>
                )}
                {(state === "error" || state === "missing-params") && (
                  <Flex vertical gap={16} align="center" className="w-full">
                    <Typography.Text
                      className="text-center"
                      data-testid="verify-email-error"
                    >
                      {state === "missing-params"
                        ? "This verification link is missing required information."
                        : "This verification link is invalid or has expired. Please sign in and request a new one."}
                    </Typography.Text>
                    <RouterLink href="/login">
                      <Button type="link" data-testid="back-to-login-btn">
                        Back to sign in
                      </Button>
                    </RouterLink>
                  </Flex>
                )}
              </Flex>
            </Card>
          </Flex>
        </Flex>
      </main>
    </Flex>
  );
};

export default VerifyEmail;
