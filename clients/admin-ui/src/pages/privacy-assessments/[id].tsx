import {
  Button,
  Result,
  Space,
  Spin,
  Text,
  useMessage,
  useModal,
} from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import {
  AssessmentDetail,
  useDeletePrivacyAssessmentMutation,
  useDownloadAssessmentReportMutation,
  useGetPrivacyAssessmentQuery,
} from "~/features/privacy-assessments";
import { RTKErrorResult } from "~/types/errors/api";

const PrivacyAssessmentDetailPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const message = useMessage();
  const modalApi = useModal();
  const { id } = router.query;
  const assessmentId = id as string;

  const {
    data: assessment,
    isLoading,
    isError,
    refetch,
  } = useGetPrivacyAssessmentQuery(assessmentId, { skip: !assessmentId });

  const [deleteAssessment, { isLoading: isDeleting }] =
    useDeletePrivacyAssessmentMutation();

  const [downloadReport, { isLoading: isDownloading }] =
    useDownloadAssessmentReportMutation();

  const handleDownloadReport = async () => {
    try {
      await downloadReport(assessmentId).unwrap();
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Failed to download report. Please try again.",
        ),
      );
    }
  };

  const isComplete =
    !!assessment &&
    (assessment.question_groups ?? [])
      .flatMap((g) => g.questions)
      .every((q) => q.answer_text.trim().length > 0);

  const handleDelete = () => {
    modalApi.confirm({
      title: "Delete assessment",
      content: (
        <Space direction="vertical" size="medium" className="w-full">
          <Text>Are you sure you want to delete this assessment?</Text>
          <Text type="secondary">
            This action cannot be undone. All assessment data, including any
            responses and documentation, will be permanently removed.
          </Text>
        </Space>
      ),
      okText: "Delete",
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        try {
          await deleteAssessment(assessment!.id).unwrap();
          message.success("Assessment deleted.");
          router.push(PRIVACY_ASSESSMENTS_ROUTE);
        } catch (error) {
          message.error(
            getErrorMessage(
              error as RTKErrorResult["error"],
              "Failed to delete assessment. Please try again.",
            ),
          );
        }
      },
    });
  };

  if (!flags?.privacyAssessments) {
    return (
      <>
        <SidePanel>
          <SidePanel.Identity title="Privacy assessments" />
        </SidePanel>
        <Layout title="Privacy assessment">
          <Result
            status="error"
            title="Feature not available"
            subTitle="This feature is currently behind a feature flag and is not enabled."
          />
        </Layout>
      </>
    );
  }

  if (isLoading) {
    return (
      <>
        <SidePanel>
          <SidePanel.Identity title="Privacy assessments" />
        </SidePanel>
        <Layout title="Privacy assessment">
          <Spin size="large" />
        </Layout>
      </>
    );
  }

  if (isError || !assessment) {
    return (
      <>
        <SidePanel>
          <SidePanel.Identity title="Privacy assessments" />
        </SidePanel>
        <Layout title="Privacy assessment">
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
      </>
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Privacy assessments"
          breadcrumbItems={[
            { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
            { title: assessment.name },
          ]}
        />
      </SidePanel>
      <Layout title={`Privacy assessment - ${assessment.name}`}>
        <AssessmentDetail assessment={assessment} />
      </Layout>
    </>
  );
};

export default PrivacyAssessmentDetailPage;
