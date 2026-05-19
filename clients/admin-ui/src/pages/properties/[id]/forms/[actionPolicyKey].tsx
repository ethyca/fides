import { Result } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetPropertyByIdQuery } from "~/features/properties/property.slice";

const FormBuilderRoute: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const { id, actionPolicyKey } = router.query as {
    id?: string;
    actionPolicyKey?: string;
  };
  const { data: property } = useGetPropertyByIdQuery(id ?? "", {
    skip: !id,
  });

  if (!flags.formBuilder) {
    return (
      <Layout title="Form builder">
        <Result
          status="error"
          title="Form builder is not enabled"
          subTitle="Turn on the form builder flag to preview this feature."
        />
      </Layout>
    );
  }

  return (
    <Layout title="Form builder">
      <PageHeader
        heading="Form builder"
        breadcrumbItems={[
          { title: "All properties", href: PROPERTIES_ROUTE },
          {
            title: property?.name ?? "Property",
            href: `${PROPERTIES_ROUTE}/${id}`,
          },
          { title: actionPolicyKey ?? "Form" },
        ]}
      />
      <Result
        status="info"
        title="Form builder coming soon"
        subTitle={`Form builder for action "${actionPolicyKey}" will be available in a future update.`}
      />
    </Layout>
  );
};

export default FormBuilderRoute;
