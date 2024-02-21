import {
  Button,
  ButtonGroup,
  Flex,
  IconButton,
  Spacer,
  Text,
  useToast,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useState } from "react";
import * as Yup from "yup";

import { getErrorMessage } from "~/features/common/helpers";
import { DesktopIcon } from "~/features/common/Icon/DesktopIcon";
import { MobileIcon } from "~/features/common/Icon/MobileIcon";
import BackButton, {
  BackButtonNonLink,
} from "~/features/common/nav/v2/BackButton";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  defaultInitialValues,
  transformConfigResponseToCreate,
} from "~/features/privacy-experience/form/helpers";
import {
  usePatchExperienceConfigMutation,
  usePostExperienceConfigMutation,
} from "~/features/privacy-experience/privacy-experience.slice";
import PrivacyExperienceForm from "~/features/privacy-experience/PrivacyExperienceForm";
import {
  ExperienceConfigCreate,
  ExperienceConfigResponse,
  ExperienceTranslation,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const validationSchema = Yup.object().shape({
  component: Yup.string().required().label("Experience type"),
  // translations: Yup.array().of(
  //   Yup.object().shape({
  //     title: Yup.string().required().label("Title"),
  //     description: Yup.string().required().label("Description"),
  //     is_default: Yup.boolean(),
  //   })
  // ),
});

const ConfigurePrivacyExperience = ({
  passedInExperience,
}: {
  passedInExperience?: ExperienceConfigResponse;
}) => {
  const [postExperienceConfigMutation] = usePostExperienceConfigMutation();
  const [patchExperienceConfigMutation] = usePatchExperienceConfigMutation();

  const toast = useToast();

  const router = useRouter();

  const handleSubmit = async (values: ExperienceConfigCreate) => {
    const valuesToSubmit = {
      ...values,
      allow_language_selection:
        values.translations && values.translations.length > 1,
    };

    let result;
    if (!passedInExperience) {
      result = await postExperienceConfigMutation(valuesToSubmit);
    } else {
      const { component, ...payload } = valuesToSubmit;
      result = await patchExperienceConfigMutation({
        ...payload,
        id: passedInExperience.id,
      });
    }

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Privacy experience successfully ${
            passedInExperience ? "updated" : "created"
          }`
        )
      );
      router.push(PRIVACY_EXPERIENCE_ROUTE);
    }
  };

  const initialValues = passedInExperience
    ? transformConfigResponseToCreate(passedInExperience)
    : defaultInitialValues;

  const [translationToEdit, setTranslationToEdit] = useState<
    ExperienceTranslation | undefined
  >(undefined);

  // const [isEditingStyle, setIsEditingStyle] = useState<boolean>(false);

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={validationSchema}
    >
      {({ dirty, isValid, isSubmitting }) => (
        <Form style={{ height: "100vh" }}>
          <Flex
            w="full"
            minH="full"
            direction="row"
            data-testid="privacy-experience-detail-page"
          >
            <Flex
              direction="column"
              minH="full"
              w="25%"
              borderRight="1px solid #DEE5EE"
            >
              <Flex direction="column" h="full" overflow="scroll" px={4}>
                {translationToEdit ? (
                  <BackButtonNonLink
                    onClick={() => setTranslationToEdit(undefined)}
                    mt={4}
                  />
                ) : (
                  <BackButton backPath={PRIVACY_EXPERIENCE_ROUTE} mt={4} />
                )}
                <PrivacyExperienceForm
                  translation={translationToEdit}
                  onSelectTranslation={(translation) =>
                    setTranslationToEdit(translation)
                  }
                />
              </Flex>
              <Spacer />
              <ButtonGroup size="sm" borderTop="1px solid #DEE5EE" p={4}>
                <Button
                  variant="outline"
                  onClick={
                    translationToEdit
                      ? () => setTranslationToEdit(undefined)
                      : () => router.push(PRIVACY_EXPERIENCE_ROUTE)
                  }
                >
                  Cancel
                </Button>
                {translationToEdit ? (
                  <Button
                    colorScheme="primary"
                    data-testid="save-btn"
                    onClick={() => setTranslationToEdit(undefined)}
                  >
                    Save
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    colorScheme="primary"
                    data-testid="save-btn"
                    isDisabled={isSubmitting || !dirty || !isValid}
                    isLoading={isSubmitting}
                  >
                    Save
                  </Button>
                )}
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
                    icon={<MobileIcon />}
                    aria-label="View mobile preview"
                  />
                  <IconButton
                    icon={<DesktopIcon />}
                    aria-label="View desktop preview"
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
