import React, { useEffect, useState, useCallback } from "react";
import type { NextPage } from "next";
import Head from "next/head";
import {
  Flex,
  Heading,
  Text,
  Stack,
  Image,
  Button,
  useToast,
} from "@fidesui/react";
import { useRouter } from "next/router";
import {
  ConfigErrorToastOptions,
  ErrorToastOptions,
  SuccessToastOptions,
} from "~/common/toast-options";

import { Headers } from "headers-polyfill";
import {
  makeConsentItems,
  makeCookieKeyConsent,
} from "~/features/consent/helpers";
import { setConsentCookie } from "fides-consent";
import { ApiUserConsents, ConsentItem } from "~/features/consent/types";

import { hostUrl, config } from "~/constants";
import { addCommonHeaders } from "~/common/CommonHeaders";
import { VerificationType } from "~/components/modals/types";
import { useLocalStorage } from "~/common/hooks";
import { useAppSelector } from "~/app/hooks";
import { selectConfigConsentOptions } from "~/features/common/config.slice";
import ConsentItemCard from "~/components/ConsentItemCard";

const Consent: NextPage = () => {
  const content: any = [];
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();
  const toast = useToast();
  const [consentItems, setConsentItems] = useState<ConsentItem[]>([]);
  const consentOptions = useAppSelector(selectConfigConsentOptions);

  useEffect(() => {
    const getUserConsents = async () => {
      if (!consentRequestId) {
        router.push("/");
        return;
      }

      const headers: Headers = new Headers();
      addCommonHeaders(headers, null);

      const configResponse = await fetch(`${hostUrl}/id-verification/config`, {
        headers,
      });
      const privacyCenterConfig = await configResponse.json();
      if (!configResponse.ok) {
        toast({
          description: privacyCenterConfig.detail,
          ...ConfigErrorToastOptions,
        });
        return;
      }

      if (
        privacyCenterConfig.identity_verification_required &&
        !verificationCode
      ) {
        router.push("/");
        return;
      }

      const verifyUrl = privacyCenterConfig.identity_verification_required
        ? `${VerificationType.ConsentRequest}/${consentRequestId}/verify`
        : `${VerificationType.ConsentRequest}/${consentRequestId}/preferences`;

      const requestOptions: RequestInit = {
        method: privacyCenterConfig.identity_verification_required
          ? "POST"
          : "GET",
        headers,
      };
      if (privacyCenterConfig.identity_verification_required) {
        requestOptions.body = JSON.stringify({ code: verificationCode });
      }

      const response = await fetch(`${hostUrl}/${verifyUrl}`, requestOptions);
      const data = (await response.json()) as ApiUserConsents;
      if (!response.ok) {
        toast({
          title: "An error occurred while retrieving user consent preferences",
          description: (data as any).detail,
          ...ErrorToastOptions,
        });

        router.push("/");
        return;
      }

      const updatedConsentItems = makeConsentItems(data, consentOptions);
      setConsentItems(updatedConsentItems);
      setConsentCookie(makeCookieKeyConsent(updatedConsentItems));
    };
    getUserConsents();
  }, [router, consentRequestId, verificationCode, toast, consentOptions]);

  consentItems.forEach((option) => {
    content.push(
      <ConsentItemCard
        key={option.fidesDataUseKey}
        fidesDataUseKey={option.fidesDataUseKey}
        name={option.name}
        description={option.description}
        highlight={option.highlight}
        url={option.url}
        defaultValue={option.defaultValue}
        consentValue={option.consentValue}
        setConsentValue={(value) => {
          /* eslint-disable-next-line no-param-reassign */
          option.consentValue = value;
        }}
      />
    );
  });

  const saveUserConsentOptions = useCallback(async () => {
    const headers: Headers = new Headers();
    addCommonHeaders(headers, null);

    const body = {
      code: verificationCode,
      consent: consentItems.map((d) => ({
        data_use: d.fidesDataUseKey,
        data_use_description: d.description,
        opt_in: d.consentValue,
      })),
    };

    const response = await fetch(
      `${hostUrl}/${VerificationType.ConsentRequest}/${consentRequestId}/preferences/`,
      {
        method: "PATCH",
        headers,
        body: JSON.stringify(body),
        credentials: "include",
      }
    );

    const data = (await response.json()) as ApiUserConsents;
    if (!response.ok) {
      toast({
        title: "An error occurred while saving user consent preferences",
        description: (data as any).detail,
        ...ErrorToastOptions,
      });
      router.push("/");
    }
    const updatedConsentItems = makeConsentItems(data, consentOptions);
    setConsentCookie(makeCookieKeyConsent(updatedConsentItems));
    toast({
      title: "Your consent preferences have been saved",
      ...SuccessToastOptions,
    });

    router.push("/");
    // TODO: display alert on successful patch
    // TODO: display error alert on failed patch
  }, [
    verificationCode,
    consentItems,
    consentRequestId,
    toast,
    router,
    consentOptions,
  ]);

  return (
    <div>
      <Head>
        <title>Privacy Center</title>
        <meta name="description" content="Privacy Center" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header>
        <Flex
          bg="gray.100"
          minHeight={14}
          p={1}
          width="100%"
          justifyContent="center"
          alignItems="center"
        >
          <Image
            src={config.logo_path}
            height="56px"
            width="304px"
            alt="Logo"
          />
        </Flex>
      </header>

      <main data-testid="consent">
        <Stack align="center" py={["6", "16"]} px={5} spacing={8}>
          <Stack align="center" spacing={3}>
            <Heading
              fontSize={["3xl", "4xl"]}
              color="gray.600"
              fontWeight="semibold"
              textAlign="center"
            >
              Manage your consent
            </Heading>
            <Text
              fontSize={["small", "medium"]}
              fontWeight="medium"
              maxWidth={624}
              textAlign="center"
              color="gray.600"
            >
              When you use our services, you’re trusting us with your
              information. We understand this is a big responsibility and work
              hard to protect your information and put you in control.
            </Text>
          </Stack>
          <Flex m={-2} flexDirection="column">
            {content}
          </Flex>
          <Stack direction="row" justifyContent="flex-start" width="720px">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                router.push("/");
              }}
            >
              Cancel
            </Button>
            <Button
              bg="primary.800"
              _hover={{ bg: "primary.400" }}
              _active={{ bg: "primary.500" }}
              colorScheme="primary"
              size="sm"
              onClick={() => {
                saveUserConsentOptions();
              }}
              data-testid="save-btn"
            >
              Save
            </Button>
          </Stack>
        </Stack>
      </main>
    </div>
  );
};

export default Consent;
