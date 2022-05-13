import { Switch } from '@fidesui/react';
import React, { ChangeEvent } from 'react';
import { useDispatch } from 'react-redux';

import { setRevealPII } from './privacy-requests.slice';

const PIIToggle: React.FC = () => {
  const dispatch = useDispatch();
  const handleToggle = (event: ChangeEvent<HTMLInputElement>) =>
    dispatch(setRevealPII(event.target.checked));
  return <Switch colorScheme="secondary" onChange={handleToggle} />;
};

export default PIIToggle;
