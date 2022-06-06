import { Divider, Flex, Heading, Text } from '@fidesui/react';
import React from 'react';

import PII from '../common/PII';
import PIIToggle from '../common/PIIToggle';
import { PrivacyRequest } from '../privacy-requests/types';

type SubjectIdentitiesProps = {
  subjectRequest: PrivacyRequest;
};

const SubjectIdentities = ({ subjectRequest }: SubjectIdentitiesProps) => {
  const { identity } = subjectRequest;

  return (
    <>
      <Flex direction='row' justifyContent='space-between'>
        <Heading fontSize='lg' fontWeight='semibold' mb={4}>
          Subject indentities
        </Heading>
        <Flex flexShrink={0} alignItems='flex-start'>
          <PIIToggle />
          <Text
            fontSize='xs'
            ml={2}
            size='sm'
            color='gray.600'
            fontWeight='500'
          >
            Reveal PII
          </Text>
        </Flex>
      </Flex>
      <Divider />

      <Flex alignItems='center'>
        <Text
          mt={4}
          mb={4}
          mr={2}
          fontSize='sm'
          color='gray.900'
          fontWeight='500'
        >
          Email:
        </Text>
        <Text color='gray.600' fontWeight='500' fontSize='sm'>
          <PII data={identity.email ? identity.email : ''} />
        </Text>
      </Flex>
      <Flex alignItems='flex-start'>
        <Text mb={4} mr={2} fontSize='sm' color='gray.900' fontWeight='500'>
          Mobile:
        </Text>
        <Text color='gray.600' fontWeight='500' fontSize='sm'>
          <PII data={identity.phone_number ? identity.phone_number : ''} />
        </Text>
      </Flex>
    </>
  );
};

export default SubjectIdentities;
