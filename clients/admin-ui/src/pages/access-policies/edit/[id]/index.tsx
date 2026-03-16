import { Button } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const EditAccessPolicyPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;

  return (
    <Layout title="Edit access policy">
      <PageHeader
        heading="Edit access policy"
        breadcrumbItems={[
          { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
          { title: (id as string) ?? "" },
        ]}
        isSticky
        rightContent={
          <NextLink href={ACCESS_POLICIES_ROUTE} passHref>
            <Button>Back to list</Button>
          </NextLink>
        }
      />
    </Layout>
  );
};

export default EditAccessPolicyPage;
