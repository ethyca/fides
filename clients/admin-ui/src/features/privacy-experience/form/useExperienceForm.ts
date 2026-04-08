import { Form, FormInstance } from "fidesui";
import { useMemo } from "react";

import {
  defaultInitialValues,
  transformConfigResponseToCreate,
} from "~/features/privacy-experience/form/helpers";
import { ExperienceConfigCreate, ExperienceConfigResponse } from "~/types/api";

export const useExperienceForm = (
  passedInExperience?: ExperienceConfigResponse,
) => {
  const [form] = Form.useForm<ExperienceConfigCreate>();

  const initialValues = useMemo(
    () =>
      passedInExperience
        ? {
            ...defaultInitialValues,
            ...transformConfigResponseToCreate(passedInExperience),
          }
        : defaultInitialValues,
    [passedInExperience],
  );

  return {
    form,
    initialValues: initialValues as ExperienceConfigCreate,
  };
};

export type ExperienceFormInstance = FormInstance<ExperienceConfigCreate>;
