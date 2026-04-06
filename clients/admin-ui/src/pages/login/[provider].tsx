import { Spin, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";
import { useDispatch } from "react-redux";

import { login, useLoginWithOIDCMutation } from "~/features/auth";
import { LoginWithOIDCRequest } from "~/features/auth/types";

const LoginWithOIDC: NextPage = () => {
  const router = useRouter();
  const dispatch = useDispatch();
  const [loginRequest] = useLoginWithOIDCMutation();
  const message = useMessage();

  useEffect(() => {
    if (
      !router.query ||
      !router.query.provider ||
      !router.query.code ||
      !router.query.state
    ) {
      return;
    }

    const data: LoginWithOIDCRequest = {
      provider: router.query.provider as string,
      code: router.query.code as string,
      state: router.query.state as string,
    };

    loginRequest(data)
      .unwrap()
      .then((response) => {
        dispatch(login(response));
        router.push("/");
      })
      .catch((error) => {
        message.error("An error occurred while logging in.");
        // eslint-disable-next-line no-console
        console.error(error);
        router.push("/login");
      });
  }, [router, message, dispatch, router.query, loginRequest]);

  return <Spin size="large" />;
};

export default LoginWithOIDC;
