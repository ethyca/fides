import { Badge } from '@fidesui/react';
import { ComponentProps } from 'react';

import { PrivacyRequestStatus } from './types';

export const statusPropMap: {
  [key in PrivacyRequestStatus]: ComponentProps<typeof Badge>;
} = {
  approved: {
    bg: 'yellow.500',
    label: 'Approved',
  },
  complete: {
    bg: 'green.500',
    label: 'Completed',
  },
  denied: {
    bg: 'red.500',
    label: 'Denied',
  },
  error: {
    bg: 'red.800',
    label: 'Error',
  },
  in_processing: {
    bg: 'orange.500',
    label: 'In Progress',
  },
  paused: {
    bg: 'gray.400',
    label: 'Paused',
  },
  pending: {
    bg: 'blue.400',
    label: 'New',
  },
};

interface RequestBadgeProps {
  status: keyof typeof statusPropMap;
}

const RequestBadge: React.FC<RequestBadgeProps> = ({ status }) => (
  <Badge
    color="white"
    bg={statusPropMap[status].bg}
    width={107}
    lineHeight="18px"
    textAlign="center"
  >
    {statusPropMap[status].label}
  </Badge>
);

export default RequestBadge;
