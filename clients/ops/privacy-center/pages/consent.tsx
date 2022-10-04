import React, { useEffect, useState, useCallback } from "react";
import type { NextPage } from "next";
import Head from "next/head";
import { Flex, Heading, Text, Stack, Image, Button } from "@fidesui/react";
import { useRouter } from "next/router";

import { Headers } from "headers-polyfill";
import ConsentItemCard from "../components/ConsentItemCard";

import config from "../config/config.json";
import { hostUrl } from "../constants";
import { addCommonHeaders } from "../common/CommonHeaders";
import { VerificationType } from "../components/modals/types";
import { useLocalStorage } from "../common/hooks";
import { ConsentItem } from "../types";

type ApiUserConsent = {
  data_use: string;
  data_use_description?: string;
  opt_in: boolean;
};

type ApiUserConcents = {
  consent: ApiUserConsent[];
};

const Consent: NextPage = () => {
  const content: any = [];
  const [consentRequestId] = useLocalStorage("consentRequestId", "");
  const [verificationCode] = useLocalStorage("verificationCode", "");
  const router = useRouter();

  useEffect(() => {
    if (!consentRequestId || !verificationCode) {
      router.push("/");
    }
  }, [consentRequestId, verificationCode, router]);

  const [consentItems, setConsentItems] = useState<ConsentItem[]>([]);

  useEffect(() => {
    const getUserConsents = async () => {
      const headers: Headers = new Headers();
      addCommonHeaders(headers, null);

      const response = await fetch(
        `${hostUrl}/${VerificationType.ConsentRequest}/${consentRequestId}/verify`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ code: verificationCode }),
        }
      );
      const data = (await response.json()) as ApiUserConcents;
      if (!response.ok) {
        router.push("/");
      }
      if (data.consent) {
        const newConsentItems: ConsentItem[] = [];
        const userConsentMap: { [key: string]: ApiUserConsent } = {};
        data.consent.forEach((option) => {
          const key = option.data_use as string;
          userConsentMap[key] = option;
        });
        config.consent.consentOptions.forEach((d) => {
          if (d.fidesDataUseKey in userConsentMap) {
            const currentConsent = userConsentMap[d.fidesDataUseKey];

            newConsentItems.push({
              consentValue: currentConsent.opt_in,
              defaultValue: d.default ? d.default : false,
              description: currentConsent.data_use_description
                ? currentConsent.data_use_description
                : "",
              fidesDataUseKey: currentConsent.data_use,
              highlight: d.highlight,
              name: d.name,
              url: d.url,
            });
          } else {
            newConsentItems.push({
              fidesDataUseKey: d.fidesDataUseKey,
              name: d.name,
              description: d.description,
              highlight: d.highlight,
              url: d.url,
              defaultValue: d.default ? d.default : false,
            });
          }
        });

        setConsentItems(newConsentItems);
      } else {
        const temp = config.consent.consentOptions.map((option) => ({
          fidesDataUseKey: option.fidesDataUseKey,
          name: option.name,
          description: option.description,
          highlight: option.highlight,
          url: option.url,
          defaultValue: option.default ? option.default : false,
        }));
        setConsentItems(temp);
      }
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
      }
    );
    (await response.json()) as ApiUserConcents;
    // TODO: display alert on successful patch
    // TODO: display error alert on failed patch
  }, [consentItems, consentRequestId, verificationCode]);

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
