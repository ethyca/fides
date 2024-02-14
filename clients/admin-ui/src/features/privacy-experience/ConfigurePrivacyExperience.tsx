import {
  Button,
  ButtonGroup,
  Flex,
  IconButton,
  NotAllowedIcon,
  Spacer,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import NewPrivacyExperienceForm from "~/features/privacy-experience/NewPrivacyExperienceForm";
import {
  ComponentType,
  ExperienceConfigCreate,
  SupportedLanguage,
} from "~/types/api";
import * as Yup from "yup";

const defaultInitialValues: ExperienceConfigCreate = {
  disabled: false,
  allow_language_selection: false,
  regions: [],
  translations: [
    {
      language: SupportedLanguage.EN,
      is_default: true,
      description: "",
      title: "",
    },
  ],
  component: ComponentType.MODAL,
};

const validationSchema = Yup.object().shape({
  component: Yup.string().required().label("Experience type"),
});

const ConfigurePrivacyExperience = () => {
  const handleSubmit = (values: ExperienceConfigCreate) => {
    console.log(values);
  };

  return (
    <Formik
      initialValues={defaultInitialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form style={{ height: "100vh" }}>
          <Flex w="full" minH="full" direction="row">
            <Flex
              direction="column"
              minH="full"
              w="25%"
              borderRight="1px solid #DEE5EE"
            >
              <Flex direction="column" h="full" overflow="scroll" px={4}>
                <BackButton backPath={PRIVACY_EXPERIENCE_ROUTE} mt={4} />
                <NewPrivacyExperienceForm />
              </Flex>
              <Spacer />
              <ButtonGroup size="sm" borderTop="1px solid #DEE5EE" p={4}>
                <Button variant="outline">Cancel</Button>
                <Button
                  type="submit"
                  colorScheme="primary"
                  isDisabled={isSubmitting || !dirty || !isValid}
                  isLoading={isSubmitting}
                >
                  Save
                </Button>
              </ButtonGroup>
            </Flex>
            <Flex direction="column" w="75%" bgColor="gray.50">
              <Flex
                direction="row"
                p={4}
                align="center"
                bgColor="white"
                borderBottom="1px solid #DEE5EE"
              >
                <Text fontSize="md" fontWeight="semibold">
                  PREVIEW
                </Text>
                <Spacer />
                <ButtonGroup size="sm" variant="outline" isAttached>
                  <IconButton
                    // TODO: replace with "mobile" icon
                    icon={<NotAllowedIcon />}
                    aria-label={"View mobile preview"}
                  />
                  <IconButton
                    // TODO: replace with "desktop" icon
                    icon={<NotAllowedIcon />}
                    aria-label={"View desktop preview"}
                  />
                </ButtonGroup>
              </Flex>
            </Flex>
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default ConfigurePrivacyExperience;
