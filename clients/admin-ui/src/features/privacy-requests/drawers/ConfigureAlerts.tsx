/* eslint-disable @typescript-eslint/no-unused-vars */
import {
  Box,
  Button,
  ButtonGroup,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  FormControl,
  FormLabel,
  HStack,
  Input,
  MenuItem,
  Stack,
  Switch,
  Text,
  useDisclosure,
  VStack,
} from "@fidesui/react";
import { Form, Formik, FormikProps } from "formik";
import { ChangeEvent, useRef } from "react";
import * as Yup from "yup";
import { CustomSwitch } from "~/features/common/form/inputs";

type ConfigureAlertsProps = {};

// eslint-disable-next-line no-empty-pattern
const ConfigureAlerts: React.FC<ConfigureAlertsProps> = ({}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const firstField = useRef();

  const handleSubmit = async (values: any, _actions: any) => {
    onClose();
  };

  const handleToggle = (event: ChangeEvent<HTMLInputElement>) => {

  }
    

  return (
    <>
      <MenuItem
        onClick={onOpen}
        _focus={{ bg: "gray.100", color: "complimentary.500" }}
      >
        Configure alerts
      </MenuItem>
      <Formik
        enableReinitialize
        initialValues={{}}
        onSubmit={handleSubmit}
        validateOnBlur={false}
        validateOnChange={false}
        validationSchema={Yup.object().shape({})}
      >
        {/* @ts-ignore */}
        {(_props: FormikProps<Values>) => (
          <Drawer
            isOpen={isOpen}
            placement="right"
            // @ts-ignore
            initialFocusRef={firstField}
            onClose={onClose}
            size="lg"
          >
            <DrawerOverlay />
            <DrawerContent color="gray.700">
              <DrawerCloseButton />
              <DrawerHeader color="gray.900">
                <Text fontSize="2xl" fontWeight="normal" mb={4}>
                  Configure alerts and notifications
                </Text>
                <Box mt="26px">
                  <Text fontSize="md" fontWeight="normal">
                    Setup your alerts to send you a notification when there are
                    any processing failures. You can also setup a threshold for
                    connector failures for Fides to notify you after X amount of
                    failures have occurred.
                  </Text>
                </Box>
              </DrawerHeader>
              <DrawerBody mt="20px">
                <Form id="configure-alerts-form" noValidate>
                  <Text fontSize="md">Contact details</Text>
                  <VStack align="stretch" gap="29px" mt="14px">
                    <HStack>
                      <FormControl alignItems="baseline" display="inline-flex">
                        <FormLabel
                          fontSize="md"
                          htmlFor="email"
                          w="30%"
                        >
                          Email
                        </FormLabel>
                        <Input
                          autoComplete="off"
                          name="email"
                          placeholder="Please enter email"
                          ref={firstField}
                          size="sm"
                        />
                      </FormControl>
                    </HStack>
                    <HStack>
                      <FormControl display="flex" alignItems="center" mt="45px">
                        <FormLabel fontSize="md" mb="0">
                          Notify me immediately if there are any DSR processing
                          errors
                        </FormLabel>
                        <Switch
                          colorScheme="secondary"
                          onChange={handleToggle}
                        />
                      </FormControl>
                    </HStack>
                  </VStack>
                  <Text color="#757575" fontSize="sm" mt="11px">
                    If selected, then Fides will notify you by your chosen
                    method of communication every time the system encounters a
                    data subject request processing error. You can turn this off
                    anytime and setup a more suitable notification method below
                    if you wish.
                  </Text>
                </Form>
              </DrawerBody>
              <DrawerFooter justifyContent="flex-start">
                <ButtonGroup size="sm" spacing="8px" variant="outline">
                  <Button onClick={onClose} variant="outline">
                    Cancel
                  </Button>
                  <Button
                    bg="primary.800"
                    color="white"
                    form="configure-alerts-form"
                    // isLoading={isSubmitting}
                    loadingText="Submitting"
                    size="sm"
                    variant="solid"
                    type="submit"
                    _active={{ bg: "primary.500" }}
                    _hover={{ bg: "primary.400" }}
                  >
                    Save
                  </Button>
                </ButtonGroup>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
        )}
      </Formik>
    </>
  );
};

export default ConfigureAlerts;
