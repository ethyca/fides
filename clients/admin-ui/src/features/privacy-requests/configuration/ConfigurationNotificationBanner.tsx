import { Alert, Button } from "fidesui";
import { useRouter } from "next/router";

import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

const ConfigurationNotificationBanner = () => {
  const router = useRouter();

  const handleClick = () => {
    router.push(MESSAGING_PROVIDERS_ROUTE);
  };

  return (
    <Alert
      className="my-5"
      type="info"
      showIcon
      message="Configure your storage and messaging provider"
      description="Before Fides can process your privacy requests we need two simple steps to configure your storage and email client."
      action={<Button onClick={handleClick}>Configure</Button>}
    />
  );
};
export default ConfigurationNotificationBanner;
