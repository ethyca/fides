import type { NextPage } from "next";

import PoliciesContainer from "~/features/access-policies/PoliciesContainer";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";

const AccessPoliciesPage: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Access policies"
          description="Access policies define when data processing is permitted or denied. Policies are evaluated in priority order and can be grouped into controls for organization and reporting."
        />
      </SidePanel>
      <Layout title="Access policies">
        <PoliciesContainer />
      </Layout>
    </>
  );
};

export default AccessPoliciesPage;
