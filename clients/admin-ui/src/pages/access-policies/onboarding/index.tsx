import { Button } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";

const AccessPoliciesOnboardingPage: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Get started with access policies" />
      </SidePanel>
      <Layout title="Access policies">
        <div className="p-6">
          <NextLink href={ACCESS_POLICIES_ROUTE} passHref>
            <Button type="primary">Continue</Button>
          </NextLink>
        </div>
      </Layout>
    </>
  );
};

export default AccessPoliciesOnboardingPage;
