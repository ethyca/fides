import {
  Avatar,
  Col,
  Divider,
  Flex,
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
  dataUseName: string | null;
  systemCount: number;
  assessments: PrivacyAssessmentResponse[];
}

export const AssessmentGroup = ({
  dataUseName,
  systemCount,
  assessments,
}: AssessmentGroupProps) => {
  const router = useRouter();

  const displayName = dataUseName || "Uncategorized";

  return (
    <div>
      <Flex justify="space-between" align="flex-end">
        <Flex gap="medium" align="center">
          <Avatar
            shape="square"
            variant="outlined"
            size={40}
            icon={<Icons.Policy />}
          />
          <div>
<<<<<<< ENG-3287-assessment-grouping-by-processing-activity
            <Title level={4} className="!m-0">
              {displayName}
=======
            <Title level={2} className="!m-0">
              {title}
>>>>>>> main
            </Title>
            <Text type="secondary">
              {systemCount} {systemCount === 1 ? "system" : "systems"} •{" "}
              {assessments.length} active assessments
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
