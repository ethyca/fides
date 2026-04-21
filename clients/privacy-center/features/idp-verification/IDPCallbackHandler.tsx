"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";

import { useSettings } from "~/features/common/settings.slice";

import {
  IDP_ERROR_MESSAGES,
  IDP_SESSION_KEYS,
} from "~/features/idp-verification/constants";
import type { IDPCallbackResponse } from "~/features/idp-verification/types";

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
      const provider = sessionStorage.getItem(IDP_SESSION_KEYS.PROVIDER);
      const basePath =
        sessionStorage.getItem(IDP_SESSION_KEYS.BASE_PATH) || "";
      const pathPrefix = basePath === "/" ? "" : basePath;

      if (!code || !state || !provider) {
        router.push("/");
        return;
      }

      const callbackBase = `${window.location.origin}${pathPrefix}`;

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
        const {
          email,
          first_name,
          last_name,
          verification_token,
        }: IDPCallbackResponse = await callbackRes.json();

        sessionStorage.setItem(IDP_SESSION_KEYS.EMAIL, email);
        if (first_name) {
          sessionStorage.setItem(IDP_SESSION_KEYS.FIRST_NAME, first_name);
        }
        if (last_name) {
          sessionStorage.setItem(IDP_SESSION_KEYS.LAST_NAME, last_name);
        }
        sessionStorage.setItem(
          IDP_SESSION_KEYS.VERIFICATION_TOKEN,
          verification_token,
        );
        sessionStorage.removeItem(IDP_SESSION_KEYS.STATE);

        router.push(`${pathPrefix}/` || "/");
      } catch {
        sessionStorage.removeItem(IDP_SESSION_KEYS.STATE);
        router.push(`${pathPrefix}/?error=idp_failed`);
      }
    };

    processCallback();
  }, [searchParams, router, settings]);

  return null;
};

export default IDPCallbackHandler;
