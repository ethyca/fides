import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { SidePanel } from "~/features/common/SidePanel";
import { PrivacyExperiencesTable } from "~/features/privacy-experience/PrivacyExperiencesTable";

const PrivacyExperiencePage = () => (
  <>
    <SidePanel>
      <SidePanel.Identity
        title="Privacy experience"
        description="Based on your privacy notices, Fides has created banner and modal privacy experience configurations. Edit each to adjust notices, locations, and text shown to users."
      />
    </SidePanel>
    <FixedLayout title="Privacy experiences">
      <PrivacyExperiencesTable />
    </FixedLayout>
  </>
);
export default PrivacyExperiencePage;
