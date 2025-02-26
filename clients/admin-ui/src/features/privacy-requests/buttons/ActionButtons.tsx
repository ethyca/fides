import { Flex } from "fidesui";

import { useAppSelector } from "~/app/hooks";
import ReprocessButton from "~/features/privacy-requests/buttons/ReprocessButton";
import ConfigureAlerts from "~/features/privacy-requests/drawers/ConfigureAlerts";
import { selectRetryRequests } from "~/features/privacy-requests/privacy-requests.slice";

const ActionButtons = () => {
  const { errorRequests } = useAppSelector(selectRetryRequests);

  return (
    <Flex gap={4}>
      {errorRequests?.length > 0 && <ReprocessButton />}
      <ConfigureAlerts />
    </Flex>
  );
};

export default ActionButtons;
