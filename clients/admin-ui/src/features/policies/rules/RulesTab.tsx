import { Typography } from "fidesui";

const { Title, Paragraph } = Typography;

const RulesTab = () => {
  return (
    <>
      <Title level={5} data-testid="policy-rules-title">
        Policy rules
      </Title>
      <Paragraph
        type="secondary"
        className="w-2/3"
        data-testid="policy-rules-description"
      >
        Rules define what actions to take on data that matches specific data
        categories. Each rule specifies an action type (access, erasure, etc.),
        target data categories, and optionally a masking strategy or storage
        destination.
      </Paragraph>
    </>
  );
};

export default RulesTab;
