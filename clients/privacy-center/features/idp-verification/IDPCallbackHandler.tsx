"use client";

import { Flex, Spin, Typography } from "antd";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";

import { useSettings } from "~/features/common/settings.slice";

import {
  IDP_ERROR_MESSAGES,
  IDP_SESSION_KEYS,
} from "~/features/idp-verification/constants";
import type {
  IDPCallbackResponse,
  IDPVerifiedRequestPayload,
} from "~/features/idp-verification/types";

const { Text } = Typography;

const IDPCallbackHandler = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const settings = useSettings();
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) {
      return;
    }
    hasRun.current = true;

    const processCallback = async () => {
      const code = searchParams?.get("code");
      const state = searchParams?.get("state");
      const actionKey = sessionStorage.getItem(IDP_SESSION_KEYS.ACTION_KEY);
      const provider = sessionStorage.getItem(IDP_SESSION_KEYS.PROVIDER);
      const formDataStr = sessionStorage.getItem(IDP_SESSION_KEYS.FORM_DATA);
      const basePath =
        sessionStorage.getItem(IDP_SESSION_KEYS.BASE_PATH) || "";

      if (!code || !state || !provider || !actionKey || !formDataStr) {
        router.push("/");
        return;
      }

      const formData = JSON.parse(formDataStr);
      const callbackBase = `${window.location.origin}${basePath === "/" ? "" : basePath}`;
      const pathPrefix = basePath === "/" ? "" : basePath;

      try {
        const callbackRes = await fetch(
          `${settings.FIDES_API_URL}/plus/openid-provider/${provider}/privacy-center/callback?origin=${encodeURIComponent(callbackBase)}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, state }),
          },
        );
        if (!callbackRes.ok) {
          throw new Error(IDP_ERROR_MESSAGES.CALLBACK_FAILED);
        }
        const { verification_token }: IDPCallbackResponse =
          await callbackRes.json();

        const payload: IDPVerifiedRequestPayload = {
          verification_token,
          policy_key: formData.policy_key,
          property_id: formData.property_id,
          custom_privacy_request_fields:
            formData.custom_privacy_request_fields,
        };
        const requestRes = await fetch(
          `${settings.FIDES_API_URL}/plus/privacy-request/idp-verified`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
        );
        if (!requestRes.ok) {
          throw new Error(IDP_ERROR_MESSAGES.REQUEST_FAILED);
        }

        Object.values(IDP_SESSION_KEYS).forEach((key) =>
          sessionStorage.removeItem(key),
        );
        router.push(
          `${pathPrefix}/privacy-request/${actionKey}/success`,
        );
      } catch {
        Object.values(IDP_SESSION_KEYS).forEach((key) =>
          sessionStorage.removeItem(key),
        );
        router.push(
          `${pathPrefix}/privacy-request/${actionKey}?error=idp_failed`,
        );
      }
    };

    processCallback();
  }, [searchParams, router, settings]);

  return (
    <Flex
      vertical
      align="center"
      justify="center"
      gap="large"
      style={{ minHeight: "50vh" }}
    >
      <Spin size="large" />
      <Text type="secondary">Verifying your identity...</Text>
    </Flex>
  );
};

export default IDPCallbackHandler;
