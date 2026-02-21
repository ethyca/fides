import { Typography } from "fidesui";

const { Title, Paragraph } = Typography;

const PolicyConditionsTab = () => {
  return (
    <>
      <Title level={5} data-testid="policy-conditions-title">
        Policy conditions
      </Title>
      <Paragraph
        type="secondary"
        className="w-2/3"
        data-testid="policy-conditions-description"
      >
        Configure conditions that control when this policy applies to privacy
        requests. If no conditions are set, the policy will apply to all
        matching requests.
      </Paragraph>
      <Paragraph strong data-testid="policy-conditions-note">
        All conditions must be met for the policy to apply.
      </Paragraph>
    </>
  );
};

export default PolicyConditionsTab;
