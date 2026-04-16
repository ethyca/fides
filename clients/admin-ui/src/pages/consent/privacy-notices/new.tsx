import { Typography } from "fidesui";

import Layout from "~/features/common/Layout";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { PrivacyNoticeForm } from "~/features/privacy-notices/PrivacyNoticeForm";

const { Paragraph } = Typography;

const NewPrivacyNoticePage = () => (
  <Layout title="New privacy notice">
    <PageHeader
      heading="Privacy notices"
      breadcrumbItems={[
        { title: "All privacy notices", href: PRIVACY_NOTICES_ROUTE },
        { title: "New privacy notice" },
      ]}
    />
    <div className="w-full lg:w-[70%]">
      <Paragraph className="mb-8">
        Configure your privacy notice including consent mechanism, associated
        data uses and the locations in which this should be displayed to users.
      </Paragraph>
      <div data-testid="new-privacy-notice-page">
        <PrivacyNoticeForm />
      </div>
    </div>
  </Layout>
);

export default NewPrivacyNoticePage;
