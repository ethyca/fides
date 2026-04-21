"use client";

/* eslint-disable @next/next/no-img-element */
import { Button, Flex } from "antd";
import { useMessage } from "fidesui";
import { useEffect, useState } from "react";

import { useSettings } from "~/features/common/settings.slice";
import { IDPProviderConfig } from "~/types/config";

import {
  IDP_ERROR_MESSAGES,
  IDP_SESSION_KEYS,
} from "~/features/idp-verification/constants";
import type { IDPAuthorizeResponse } from "~/features/idp-verification/types";

interface IDPLoginButtonsProps {
  providers: IDPProviderConfig[];
  basePath: string;
}

const IDPLoginButtons = ({ providers, basePath }: IDPLoginButtonsProps) => {
  const settings = useSettings();
  const messageApi = useMessage();
  const [loading, setLoading] = useState<string | null>(null);
  const [providerTypes, setProviderTypes] = useState<Record<string, string>>(
    {},
  );

  useEffect(() => {
    const fetchProviderTypes = async () => {
      try {
        const res = await fetch(
          `${settings.FIDES_API_URL}/plus/openid-provider/simple`,
        );
        if (!res.ok) {
          return;
        }
        const data: Array<{ identifier: string; provider: string }> =
          await res.json();
        const map: Record<string, string> = {};
        for (const item of data) {
          map[item.identifier] = item.provider;
        }
        setProviderTypes(map);
      } catch {
        // Icons are optional; fail silently
      }
    };
    fetchProviderTypes();
  }, [settings.FIDES_API_URL]);

  const handleIDPLogin = async (provider: IDPProviderConfig) => {
    setLoading(provider.identifier);

    try {
      sessionStorage.setItem(IDP_SESSION_KEYS.PROVIDER, provider.identifier);
      sessionStorage.setItem(IDP_SESSION_KEYS.BASE_PATH, basePath);

      const callbackBase = `${window.location.origin}${basePath === "/" ? "" : basePath}`;
      const res = await fetch(
        `${settings.FIDES_API_URL}/plus/openid-provider/${provider.identifier}/privacy-center/authorize?origin=${encodeURIComponent(callbackBase)}`,
      );
      if (!res.ok) {
        throw new Error(IDP_ERROR_MESSAGES.AUTHORIZE_FAILED);
      }
      const data: IDPAuthorizeResponse = await res.json();
      sessionStorage.setItem(IDP_SESSION_KEYS.STATE, data.state);

      window.location.href = data.authorization_url;
    } catch (error) {
      setLoading(null);
      messageApi.error(
        error instanceof Error
          ? error.message
          : IDP_ERROR_MESSAGES.AUTHORIZE_FAILED,
      );
    }
  };

  return (
    <Flex vertical gap="middle">
      {providers.map((provider) => {
        const providerType =
          provider.provider || providerTypes[provider.identifier];
        return (
          <Button
            key={provider.identifier}
            size="large"
            loading={loading === provider.identifier}
            onClick={() => handleIDPLogin(provider)}
            icon={
              providerType ? (
                <img
                  src={`/images/oauth-login/${providerType}.svg`}
                  alt={`${providerType} icon`}
                  width={20}
                  height={20}
                />
              ) : undefined
            }
            block
          >
            {provider.label}
          </Button>
        );
      })}
    </Flex>
  );
};

export default IDPLoginButtons;
