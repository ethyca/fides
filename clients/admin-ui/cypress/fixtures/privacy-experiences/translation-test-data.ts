import { ComponentType, ExperienceTranslationCreate } from "~/types/api";
import { SupportedLanguage } from "~/types/api";

interface TestCase {
  component: string;
  translations: ExperienceTranslationCreate[];
}

export const translationTestCases: TestCase[] = [
  {
    component: "Privacy center",
    translations: [
      {
        language: SupportedLanguage.EN_GB,
        title: "Privacy Center UK",
        description: "Manage your privacy preferences in UK English",
        accept_button_label: "Accept UK",
        reject_button_label: "Reject UK",
        save_button_label: "Save UK",
      },
      {
        language: SupportedLanguage.FR_CA,
        title: "Centre de confidentialité CA",
        description:
          "Gérez vos préférences de confidentialité en français canadien",
        accept_button_label: "Accepter CA",
        reject_button_label: "Rejeter CA",
        save_button_label: "Enregistrer CA",
      },
    ],
  },
  {
    component: "Modal",
    translations: [
      {
        language: SupportedLanguage.EN_GB,
        title: "Privacy Modal UK",
        description: "Manage your privacy preferences in UK English",
        accept_button_label: "Accept UK",
        reject_button_label: "Reject UK",
        save_button_label: "Save UK",
        acknowledge_button_label: "OK UK",
      },
      {
        language: SupportedLanguage.FR_CA,
        title: "Modal de confidentialité CA",
        description:
          "Gérez vos préférences de confidentialité en français canadien",
        accept_button_label: "Accepter CA",
        reject_button_label: "Rejeter CA",
        save_button_label: "Enregistrer CA",
        acknowledge_button_label: "OK CA",
      },
    ],
  },
  {
    component: "Banner and modal",
    translations: [
      {
        language: SupportedLanguage.EN_GB,
        title: "Privacy Banner and Modal UK",
        description: "Manage your privacy preferences in UK English",
        accept_button_label: "Accept UK",
        reject_button_label: "Reject UK",
        save_button_label: "Save UK",
        acknowledge_button_label: "OK UK",
        privacy_preferences_link_label: "Privacy Preferences UK",
      },
      {
        language: SupportedLanguage.FR_CA,
        title: "Bannière et modal de confidentialité CA",
        description:
          "Gérez vos préférences de confidentialité en français canadien",
        accept_button_label: "Accepter CA",
        reject_button_label: "Rejeter CA",
        save_button_label: "Enregistrer CA",
        acknowledge_button_label: "OK CA",
        privacy_preferences_link_label: "Préférences de confidentialité CA",
      },
    ],
  },
];
