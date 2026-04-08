import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { SidePanel } from "~/features/common/SidePanel";
import { PrivacyNoticesTable } from "~/features/privacy-notices/table/PrivacyNoticesTable";

const PrivacyNoticesPage = () => (
  <>
    <SidePanel>
      <SidePanel.Identity
        title="Privacy notices"
        description="Manage the privacy notices and mechanisms displayed to users based on their location and data usage."
      />
    </SidePanel>
    <FixedLayout title="Privacy notices">
      <PrivacyNoticesTable />
    </FixedLayout>
  </>
);
export default PrivacyNoticesPage;
