import { Segmented } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetExperienceConfigByIdQuery } from "~/features/privacy-experience/privacy-experience.slice";
import TcfHashHistoryTable from "~/features/tcf-hash-history/TcfHashHistoryTable";
import TcfHashHistoryTimeline from "~/features/tcf-hash-history/TcfHashHistoryTimeline";
import TcfHashHistoryTimeList from "~/features/tcf-hash-history/TcfHashHistoryTimeList";

type Variant = "timeline" | "list" | "table";

const TcfVersionHistoryPage: NextPage = () => {
  const router = useRouter();
  const experienceConfigId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : (router.query.id ?? "");

  const { data } = useGetExperienceConfigByIdQuery(experienceConfigId, {
    skip: !experienceConfigId,
  });

  const [variant, setVariant] = useState<Variant>("timeline");

  return (
    <Layout title="TCF version history">
      <PageHeader
        heading={data?.name ?? "TCF version history"}
        breadcrumbItems={[
          { title: "Privacy experiences", href: PRIVACY_EXPERIENCE_ROUTE },
          {
            title: data?.name,
            href: `${PRIVACY_EXPERIENCE_ROUTE}/${experienceConfigId}`,
          },
          { title: "TCF version history" },
        ]}
        rightContent={
          <Segmented<string>
            options={["timeline", "list", "table"]}
            onChange={(value) => {
              setVariant(value as Variant);
            }}
          />
        }
      />

      {experienceConfigId && variant === "timeline" && (
        <TcfHashHistoryTimeline experienceConfigId={experienceConfigId} />
      )}
      {experienceConfigId && variant === "list" && (
        <TcfHashHistoryTimeList experienceConfigId={experienceConfigId} />
      )}
      {experienceConfigId && variant === "table" && (
        <TcfHashHistoryTable experienceConfigId={experienceConfigId} />
      )}
    </Layout>
  );
};

export default TcfVersionHistoryPage;
