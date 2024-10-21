import { DatasetLifecycleSystem } from "~/features/dataset-lifecycle/systems/useSpoofGetSystemsQuery";
import { SUPPORTED_INTEGRATIONS } from "~/features/integrations/add-integration/allIntegrationTypes";

const systemHasHeliosIntegration = (system: DatasetLifecycleSystem) => {
  return (
    !!system.integration?.connection_type &&
    SUPPORTED_INTEGRATIONS.includes(system.integration.connection_type)
  );
};

export default systemHasHeliosIntegration;
