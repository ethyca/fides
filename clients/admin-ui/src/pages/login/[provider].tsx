import {
  ChakraCenter as Center,
  ChakraSpinner as Spinner,
  useChakraToast as useToast,
} from "fidesui";
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
  const toast = useToast();

  useEffect(() => {
    if (!router.query || !router.query.provider || !router.query.code) {
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
        toast({
          status: "error",
          description: "An error occurred while logging in.",
        });
        // eslint-disable-next-line no-console
        console.error(error);
        router.push("/login");
      });
  }, [router, toast, dispatch, router.query, loginRequest]);

  return (
    <Center h="100%" w="100%">
      <Spinner color="primary" size="xl" />
    </Center>
  );
};

export default LoginWithOIDC;
