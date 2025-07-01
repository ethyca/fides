import { AntButton as Button, AntFlex as Flex, AntText as Text } from "fidesui";

import { useFinalizePrivacyRequest } from "./hooks/useFinalizePrivacyRequest";

type FinalizePrivacyRequestProps = {
  id: string;
};

const FinalizePrivacyRequest = ({ id }: FinalizePrivacyRequestProps) => {
  const { handleFinalize, isLoading } = useFinalizePrivacyRequest();

  const handleFinalizeClick = () => {
    handleFinalize(id);
  };

  return (
    <Flex vertical>
      <Text>
        Finalize the DSR once you&#39;ve reviewed and have completed any manual
        erasures outside of Fides
      </Text>
      <Button type="primary" onClick={handleFinalizeClick} loading={isLoading}>
        Finalize DSR
      </Button>
    </Flex>
  );
};

export default FinalizePrivacyRequest;
