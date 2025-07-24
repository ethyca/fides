export const CONSENT_CATEGORIES = [
  "essential",
  "functional.service.improve",
  "personalize",
  "analytics",
  "marketing.advertising.first_party.targeted",
  "marketing.advertising.third_party.targeted",
];

const isConsentCategory = (category: string): boolean => {
  return CONSENT_CATEGORIES.includes(category);
};

export default isConsentCategory;
