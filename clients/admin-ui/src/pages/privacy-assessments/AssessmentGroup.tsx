import { Flex, Icons, Text, Typography } from "fidesui";
import { useRouter } from "next/router";

import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import { PrivacyAssessmentResponse } from "~/features/privacy-assessments";

import { AssessmentCard } from "./AssessmentCard";

const { Title } = Typography;

interface AssessmentGroupProps {
  templateId: string;
  title: string;
  assessments: PrivacyAssessmentResponse[];
}

export const AssessmentGroup = ({
  templateId,
  title,
  assessments,
}: AssessmentGroupProps) => {
  const router = useRouter();

  return (
    <div>
      <Flex
        justify="space-between"
        align="flex-end"
        className="mb-4 border-b border-gray-200 pb-2"
      >
        <Flex gap="middle" align="center">
          <div className="flex size-10 items-center justify-center rounded border border-gray-200">
            <Icons.Document />
          </div>
          <div>
            <Title level={4} className="!m-0">
              {title}
            </Title>
            <Text type="secondary" className="text-sm">
              Template ID: {templateId} • {assessments.length} active
              assessments
            </Text>
          </div>
        </Flex>
      </Flex>

      <Flex gap="middle" wrap="wrap">
        {assessments.map((assessment) => (
          <AssessmentCard
            key={assessment.id}
            assessment={assessment}
            onClick={() =>
              router.push(`${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`)
            }
          />
        ))}
      </Flex>
    </div>
  );
};
