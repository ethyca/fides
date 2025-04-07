import {
  AntFlex as Flex,
  AntSpace as Space,
  Skeleton,
  Text,
  useToast,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

import DocsLink from "~/features/common/DocsLink";
import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import { useGetPurposesQuery } from "~/features/common/purpose.slice";
import SettingsBox from "~/features/consent-settings/SettingsBox";
import {
  FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS,
  PUBLISHER_RESTRICTIONS_DOCS_URL,
} from "~/features/consent-settings/tcf/constants";
import { PurposeRestrictionsTable } from "~/features/consent-settings/tcf/PurposeRestrictionsTable";
import { useGetTCFConfigurationQuery } from "~/features/consent-settings/tcf/tcf-config.slice";

const ConsentConfigurationPage: NextPage = () => {
  const router = useRouter();
  const configurationId = decodeURIComponent(
    router.query.configuration_id as string,
  );
  const purposeId = decodeURIComponent(router.query.purpose_id as string);
  const toast = useToast();

  const { data: purposes, isLoading: isPurposesLoading } =
    useGetPurposesQuery();
  const { data: configuration } = useGetTCFConfigurationQuery(configurationId);

  const purpose = useMemo(() => {
    return purposes?.purposes[purposeId];
  }, [purposes, purposeId]);

  useEffect(() => {
    if (
      purposeId &&
      FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(
        parseInt(purposeId, 10),
      )
    ) {
      toast({
        status: "error",
        title: `Purpose ${purposeId} is not flexible`,
        description: "Please select a different purpose.",
      });
      router.replace("/settings/consent");
    }
  }, [purposeId, toast, router]);

  return (
    <FixedLayout title="Consent Configuration">
      <PageHeader
        heading="Consent Configuration"
        breadcrumbItems={[
          { title: "Consent settings", href: "/settings/consent" },
          {
            title: configuration?.name || "Configuration",
          },
          {
            title: `TCF purpose ${purposeId}`,
          },
        ]}
      />
      <Space direction="vertical" size="middle">
        <Space direction="vertical" size="middle">
          <SettingsBox
            title={`TCF purpose ${purposeId}${
              purpose?.name ? `: ${purpose?.name}` : ""
            }`}
          >
            {isPurposesLoading ? (
              <Flex vertical className="gap-1.5">
                <Skeleton height="16px" width="100%" />
                <Skeleton height="16px" width="100%" />
                <Skeleton height="16px" width="30%" />
              </Flex>
            ) : (
              !!purpose && <Text fontSize="sm">{purpose?.description}</Text>
            )}
          </SettingsBox>
          <SettingsBox title={configuration?.name || "Configuration"}>
            <Space direction="vertical" className="gap-3">
              <Text fontSize="sm">
                Add restrictions to control how vendors process data for
                specific purposes. For each restriction, choose a restriction
                type. Then, decide whether the restriction applies to all
                vendors, specific vendors, or only to a limited set of allowed
                vendors. You can add multiple restrictions&mdash;they&apos;ll
                appear in the table below.{" "}
                <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                  Learn more about publisher restrictions
                </DocsLink>{" "}
                in our docs.
              </Text>
            </Space>
          </SettingsBox>
        </Space>
        <PurposeRestrictionsTable />
      </Space>
    </FixedLayout>
  );
};

export default ConsentConfigurationPage;
