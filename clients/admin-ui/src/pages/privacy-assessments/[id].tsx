import {
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Result,
  Space,
  Spin,
  Tag,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  AssessmentDetail,
  useGetPrivacyAssessmentQuery,
} from "~/features/privacy-assessments";

const PrivacyAssessmentDetailPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const { id } = router.query;
  const assessmentId = id as string;

  const {
    data: assessment,
    isLoading,
    isError,
    refetch,
  } = useGetPrivacyAssessmentQuery(assessmentId, { skip: !assessmentId });

  if (!flags?.alphaDataProtectionAssessments) {
    return (
      <Layout title="Privacy assessment">
        <Result
          status="error"
          title="Feature not available"
          subTitle="This feature is currently behind a feature flag and is not enabled."
        />
      </Layout>
    );
  }

  if (isLoading) {
    return (
      <Layout title="Privacy assessment">
        <PageHeader heading="Privacy assessments" isSticky />
        <Flex align="center" justify="center" className="p-20">
          <Spin size="large" />
        </Flex>
      </Layout>
    );
  }

  if (isError || !assessment) {
    return (
      <Layout title="Privacy assessment">
        <PageHeader heading="Privacy assessments" isSticky />
        <Result
          status="error"
          title="Failed to load assessment"
          subTitle="There was an error loading this privacy assessment. Please try again."
          extra={
            <Space>
              <NextLink href={PRIVACY_ASSESSMENTS_ROUTE} passHref>
                <Button>Back to list</Button>
              </NextLink>
              <Button type="primary" onClick={() => refetch()}>
                Retry
              </Button>
            </Space>
          }
        />
      </Layout>
    );
  }

  return (
    <Layout title={`Privacy assessment - ${assessment.name}`}>
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          {
            title: (
              <Flex align="center" gap="small" wrap="wrap">
                <span>{assessment.name}</span>
                <Tag color={CUSTOM_TAG_COLOR.DEFAULT}>
                  {assessment.assessment_type.toUpperCase()}
                </Tag>
              </Flex>
            ),
          },
        ]}
        isSticky
      />
      <AssessmentDetail assessment={assessment} refetch={refetch} />
    </Layout>
  );
};

export default PrivacyAssessmentDetailPage;
