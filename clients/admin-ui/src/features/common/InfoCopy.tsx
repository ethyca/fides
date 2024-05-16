import { Heading, Text } from "fidesui";

import { InfoBlock } from "~/features/integrations/BigqueryCopy";

const InfoCopy = ({ info }: { info: InfoBlock[] }) => (
  <>
    {info.map((item) => (
      <>
        <Heading fontSize="md" mt={8} mb={1}>
          {item.title}
        </Heading>
        {item.description.map((p) => (
          <Text fontSize="sm" key={p}>
            {p}
          </Text>
        ))}
      </>
    ))}
  </>
);

export default InfoCopy;
