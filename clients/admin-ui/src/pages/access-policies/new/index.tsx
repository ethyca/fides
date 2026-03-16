import { Button } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const NewAccessPolicyPage: NextPage = () => {
  return (
    <Layout title="New access policy">
      <PageHeader
        heading="New access policy"
        breadcrumbItems={[
          { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
          { title: "New policy" },
        ]}
        isSticky
        rightContent={
          <NextLink href={ACCESS_POLICIES_ROUTE} passHref>
            <Button>Cancel</Button>
          </NextLink>
        }
      />
    </Layout>
  );
};

export default NewAccessPolicyPage;
