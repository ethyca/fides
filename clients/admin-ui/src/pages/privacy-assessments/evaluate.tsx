import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { EvaluateAssessmentForm } from "~/features/privacy-assessments";

const EvaluateAssessmentPage: NextPage = () => (
  <Layout title="Evaluate assessments">
    <PageHeader
      heading="Evaluate assessments"
      breadcrumbItems={[
        { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
        { title: "Evaluate" },
      ]}
      isSticky
    />
    <div className="py-6">
      <div className="max-w-3xl">
        <EvaluateAssessmentForm />
      </div>
    </div>
  </Layout>
);

export default EvaluateAssessmentPage;
