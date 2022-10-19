import React, { useEffect, useState, useCallback } from "react";
import type { NextPage } from "next";
import Head from "next/head";
import { Flex, Heading, Text, Stack, Image, Button } from "@fidesui/react";
import { useRouter } from "next/router";

import { Headers } from "headers-polyfill";
import {
  makeConsentItems,
  makeCookieKeyConsent,
} from "~/features/consent/helpers";
import { setConsentCookie } from "~/features/consent/cookie";
import { ApiUserConsents, ConsentItem } from "~/features/consent/types";
import ConsentItemCard from "../components/ConsentItemCard";

import consentConfig from "../config/config.json";
import { hostUrl } from "../constants";
import { addCommonHeaders } from "../common/CommonHeaders";
import { VerificationType } from "../components/modals/types";
import { useLocalStorage } from "../common/hooks";

const Consent: NextPage = () => {
  const content: any = [];
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();

  useEffect(() => {
    if (!consentRequestId) {
      router.push("/");
    }
  }, [consentRequestId, router]);

  const [consentItems, setConsentItems] = useState<ConsentItem[]>([]);

  useEffect(() => {
    const getUserConsents = async () => {
      const headers: Headers = new Headers();
      addCommonHeaders(headers, null);

      const configResponse = await fetch(`${hostUrl}/id-verification/config`, {
        headers,
      });
      const privacyCenterConfig = await configResponse.json();

      if (
        privacyCenterConfig.identity_verification_required &&
        !verificationCode
      ) {
        router.push("/");
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
        router.push("/");
      }

      const updatedConsentItems = makeConsentItems(
        data,
        consentConfig.consent.consentOptions
      );
      setConsentItems(updatedConsentItems);
      setConsentCookie(makeCookieKeyConsent(updatedConsentItems));
    };
    getUserConsents();
  }, [router, consentRequestId, verificationCode]);

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
      `${hostUrl}/${VerificationType.ConsentRequest}/${consentRequestId}/preferences`,
      {
        method: "PATCH",
        headers,
        body: JSON.stringify(body),
        credentials: "include",
      }
    );

    const data = (await response.json()) as ApiUserConsents;
    const updatedConsentItems = makeConsentItems(
      data,
      consentConfig.consent.consentOptions
    );
    setConsentCookie(makeCookieKeyConsent(updatedConsentItems));

    router.push("/");
    // TODO: display alert on successful patch
    // TODO: display error alert on failed patch
  }, [consentItems, consentRequestId, verificationCode, router]);

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
            src={consentConfig.logo_path}
            height="56px"
            width="304px"
            alt="Logo"
          />
        </Flex>
      </header>

      <main>
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
