import {
  Button,
  chakra,
  Checkbox,
  Divider,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Heading,
  Input,
  Stack,
  Text,
  useToast,
} from '@fidesui/react';
import { useFormik } from 'formik';
import type { NextPage } from 'next';
import NextLink from 'next/link';
import { useRouter } from 'next/router';
import React from 'react';

import { USER_PRIVILEGES } from '../../constants';
import { isErrorWithDetail, isErrorWithDetailArray } from '../common/helpers';
import {
  useCreateUserMutation,
  useUpdateUserPermissionsMutation,
} from './user-management.slice';

const useUserForm = () => {
  const [createUser] = useCreateUserMutation();
  const [updateUserPermissions] = useUpdateUserPermissionsMutation();
  const router = useRouter();
  const toast = useToast();

  const formik = useFormik({
    initialValues: {
      username: '',
      first_name: '',
      last_name: '',
      password: '',
      scopes: [],
    },
    onSubmit: async (values) => {
      const userBody = {
        username: values.username,
        first_name: values.first_name,
        last_name: values.last_name,
        password: values.password,
      };

      const createUserResult = await createUser(userBody);

      if ('error' in createUserResult) {
        let errorMsg = 'An unexpected error occurred. Please try again.';
        if (isErrorWithDetail(createUserResult.error)) {
          errorMsg = createUserResult.error.data.detail;
        } else if (isErrorWithDetailArray(createUserResult.error)) {
          const { error } = createUserResult;
          errorMsg = error.data.detail[0].msg;
        }
        toast({
          status: 'error',
          description: errorMsg,
        });
        return;
      }

      const { data } = createUserResult;

      const userWithPrivileges = {
        id: data ? data.id : null,
        scopes: [...values.scopes, 'privacy-request:read'],
      };

      const updateUserPermissionsResult = await updateUserPermissions(
        userWithPrivileges as { id: string }
      );

      if (!('error' in updateUserPermissionsResult)) {
        router.push('/user-management');
      }
    },
    validate: (values) => {
      const errors: {
        username?: string;
        first_name?: string;
        last_name?: string;
        password?: string;
      } = {};

      if (!values.username) {
        errors.username = 'Username is required';
      }

      if (!values.password) {
        errors.password = 'Password is required';
      }

      if (values.password.length < 8) {
        errors.password = 'Password must have at least eight characters.';
      }

      if (!/[0-9]/.test(values.password)) {
        errors.password = 'Password must have at least one number.';
      }

      if (!/[A-Z]/.test(values.password)) {
        errors.password = 'Password must have at least one capital letter.';
      }

      if (!/[a-z]/.test(values.password)) {
        errors.password = 'Password must have at least one lowercase letter.';
      }

      if (!/[\W]/.test(values.password)) {
        errors.password = 'Password must have at least one symbol.';
      }

      return errors;
    },
  });

  return {
    ...formik,
  };
};

const UserForm: NextPage = () => {
  const { errors, handleBlur, handleChange, handleSubmit, touched, values } =
    useUserForm();

  return (
    <div>
      <main>
        <Heading mb={4} fontSize='xl' colorScheme='primary'>
          Profile
        </Heading>
        <Divider mb={7} />
        <chakra.form
          onSubmit={handleSubmit}
          maxW={['xs', 'xs', '100%']}
          width="100%"
        >
          <Stack mb={8} spacing={6}>
            <FormControl
              id='username'
              isInvalid={touched.username && Boolean(errors.username)}
            >
              <FormLabel htmlFor='username' fontWeight='medium'>
                Username
              </FormLabel>
              <Input
                id='username'
                maxWidth='40%'
                name='username'
                focusBorderColor='primary.500'
                placeholder='Enter new username'
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.username}
                isInvalid={touched.username && Boolean(errors.username)}
              />
              <FormErrorMessage>{errors.username}</FormErrorMessage>
            </FormControl>

            <FormControl id='first_name'>
              <FormLabel htmlFor='first_name' fontWeight='medium'>
                First Name
              </FormLabel>
              <Input
                id='first_name'
                maxWidth='40%'
                name='first_name'
                focusBorderColor='primary.500'
                placeholder='Enter first name of user'
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.first_name}
              />
            </FormControl>

            <FormControl id='last_name'>
              <FormLabel htmlFor='last_name' fontWeight='medium'>
                Last Name
              </FormLabel>
              <Input
                id='last_name'
                maxWidth='40%'
                name='last_name'
                focusBorderColor='primary.500'
                placeholder='Enter last name of user'
                onChange={handleChange}
                onBlur={handleBlur}
                value={values.last_name}
              />
            </FormControl>
            <FormControl
              id='password'
              isInvalid={touched.password && Boolean(errors.password)}
            >
              <FormLabel htmlFor='password' fontWeight='medium'>
                Password
              </FormLabel>
              <Input
                id='password'
                maxWidth='40%'
                name='password'
                focusBorderColor='primary.500'
                placeholder='********'
                type='password'
                value={values.password}
                onChange={handleChange}
                onBlur={handleBlur}
                isInvalid={touched.password && Boolean(errors.password)}
              />
              <FormErrorMessage>{errors.password}</FormErrorMessage>
            </FormControl>
            <Divider mb={7} mt={7} />
            <Heading fontSize='xl' colorScheme='primary'>
              Privileges
            </Heading>
            <Text>Select privileges to assign to this user</Text>
            <Divider mb={2} mt={2} />

            <Stack spacing={[1, 5]} direction="column">
              {USER_PRIVILEGES.map((policy) => (
                <Checkbox
                  colorScheme="purple"
                  defaultChecked={policy.scope === 'privacy-request:read'}
                  key={`${policy.privilege}`}
                  onChange={handleChange}
                  id={`scopes-${policy.privilege}`}
                  name='scopes'
                  // @ts-ignore
                  isChecked={values.scopes[policy.privilege]}
                  value={
                    policy.scope === 'privacy-request:read'
                      ? undefined
                      : policy.scope
                  }
                  isDisabled={policy.scope === 'privacy-request:read'}
                  isReadOnly={policy.scope === 'privacy-request:read'}
                >
                  {policy.privilege}
                </Checkbox>
              ))}
            </Stack>
          </Stack>

          <NextLink href='/user-management' passHref>
            <Button variant='outline' mr={3} size='sm'>
              Cancel
            </Button>
          </NextLink>
          <Button
            type="submit"
            bg="primary.800"
            _hover={{ bg: 'primary.400' }}
            _active={{ bg: 'primary.500' }}
            colorScheme="primary"
            // disabled={!(isValid && dirty)}
            size='sm'
          >
            Save
          </Button>
        </chakra.form>
      </main>
    </div>
  );
};

export default UserForm;
