import { ExperienceConfigCreate } from "~/types/api";

interface ExperienceConfigFormValues extends ExperienceConfigCreate {
  css?: string;
}

export default ExperienceConfigFormValues;
