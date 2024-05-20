import { Box } from "fidesui";

import IntegrationBox  from "~/features/integrations/IntegrationBox";
import NoIntegrations  from "~/features/integrations/NoIntegrations";


const IntegrationsTabs: NextPage = ({data}) => {
    const renderIntegration = (item) =>
      <IntegrationBox key={item.key} integration={item}/>

    const renderNoIntegrations = () =>
      !data.total && (<NoIntegrations/>)

    return (
      <Box marginTop="24px">
        {data.items.map(renderIntegration)}
        {renderNoIntegrations()}
      </Box>
    );
  };

  export default IntegrationsTabs;
