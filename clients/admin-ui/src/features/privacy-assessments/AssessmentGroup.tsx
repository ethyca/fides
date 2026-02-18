import {
  Col,
  Divider,
  Flex,
  IconBadge,
  Icons,
  Row,
  Text,
  Typography,
} from "fidesui";
import { useRouter } from "next/router";

import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";

import { AssessmentCard } from "./AssessmentCard";
import { PrivacyAssessmentResponse } from "./types";

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
      <Flex justify="space-between" align="flex-end">
        <Flex gap="middle" align="center">
          <IconBadge size={40}>
            <Icons.Document />
          </IconBadge>
          <div>
            <Title level={4} className="!m-0">
              {title}
            </Title>
            <Text type="secondary">
              Template ID: {templateId} • {assessments.length} active
              assessments
            </Text>
          </div>
        </Flex>
      </Flex>
      <Divider className="mb-4" />

      <Row gutter={[16, 16]}>
        {assessments.map((assessment) => (
          <Col key={assessment.id} span={6}>
            <AssessmentCard
              assessment={assessment}
              onClick={() =>
                router.push(`${PRIVACY_ASSESSMENTS_ROUTE}/${assessment.id}`)
              }
            />
          </Col>
        ))}
      </Row>
    </div>
  );
};
