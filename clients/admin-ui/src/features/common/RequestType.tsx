import { Box, Tag } from '@fidesui/react';
import React from 'react';

import { ActionType, Rule } from '../privacy-requests/types';

type RequestTypeProps = {
  rules: Rule[];
};

const RequestType = ({ rules }: RequestTypeProps) => {
  const actions = Array.from(
    new Set(
      rules
        .filter((d) => Object.values(ActionType).includes(d.action_type))
        .map((d) =>
          d.action_type === ActionType.ACCESS ? 'Download' : 'Delete'
        )
    )
  );
  const tags = actions.map((action_type) => (
    <Tag
      key={action_type}
      color='white'
      bg='primary.400'
      fontWeight='medium'
      fontSize='sm'
      mr={1}
      mb={4}
    >
      {action_type}
    </Tag>
  ));

  return <Box>{tags}</Box>;
};

export default RequestType;
