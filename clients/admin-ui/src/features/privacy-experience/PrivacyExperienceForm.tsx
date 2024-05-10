import {
  ArrowForwardIcon,
  Box,
  Button,
  ButtonGroup,
  Collapse,
  Divider,
  Flex,
  Heading,
  Text,
} from "@fidesui/react";
import { useFormikContext } from "formik";
import { useRouter } from "next/router";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomSelect,
  CustomSwitch,
  CustomTextInput,
} from "~/features/common/form/inputs";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/v2/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectLocationsRegulations,
  useGetLocationsRegulationsQuery,
} from "~/features/locations/locations.slice";
import { getSelectedRegionIds } from "~/features/privacy-experience/form/helpers";
import { selectAllLanguages } from "~/features/privacy-experience/language.slice";
import {
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import {
  selectAllProperties,
  selectPage as selectPropertyPage,
  selectPageSize as selectPropertyPageSize,
  useGetAllPropertiesQuery,
} from "~/features/properties/property.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
  LimitedPrivacyNoticeResponseSchema,
  SupportedLanguage,
} from "~/types/api";

const componentTypeOptions = [
  {
    label: "Banner and modal",
    value: ComponentType.BANNER_AND_MODAL,
  },
  {
    label: "Modal",
    value: ComponentType.MODAL,
  },
  {
    label: "Privacy center",
    value: ComponentType.PRIVACY_CENTER,
  },
];

export const PrivacyExperienceConfigColumnLayout = ({
  buttonPanel,
  children,
}: {
  buttonPanel: React.ReactNode;
  children: React.ReactNode;
}) => (
  <Flex direction="column" minH="full" w="25%" borderRight="1px solid #DEE5EE">
    <Flex direction="column" h="full" overflowY="auto" px={4}>
      <Flex direction="column" gap={4} w="full" pb={4}>
        {children}
      </Flex>
    </Flex>
    {buttonPanel}
  </Flex>
);

export const PrivacyExperienceForm = ({
  allPrivacyNotices,
  translationsEnabled,
  onSelectTranslation,
  onCreateTranslation,
}: {
  allPrivacyNotices: LimitedPrivacyNoticeResponseSchema[];
  translationsEnabled?: boolean;
  onSelectTranslation: (t: ExperienceTranslation) => void;
  onCreateTranslation: (lang: SupportedLanguage) => ExperienceTranslation;
}) => {
  const router = useRouter();

  const [editingStyle, setEditingStyle] = useState<boolean>(false);
  const { values, setFieldValue, dirty, isValid, isSubmitting } =
    useFormikContext<ExperienceConfigCreate>();
  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });

  const getPrivacyNoticeName = (id: string) => {
    const notice = allPrivacyNotices.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  useGetLocationsRegulationsQuery();
  const locationsRegulations = useAppSelector(selectLocationsRegulations);

  const allSelectedRegions = [
    ...getSelectedRegionIds(locationsRegulations.locations),
    ...getSelectedRegionIds(locationsRegulations.location_groups),
  ];

  const allLanguages = useAppSelector(selectAllLanguages);

  const getTranslationDisplayName = (t: ExperienceTranslation) => {
    const language = allLanguages.find((lang) => lang.id === t.language);
    const name = language ? language.name : t.language;
    return `${name}${t.is_default ? " (Default)" : ""}`;
  };

  const propertyPage = useAppSelector(selectPropertyPage);
  const propertyPageSize = useAppSelector(selectPropertyPageSize);
  useGetAllPropertiesQuery({ page: propertyPage, size: propertyPageSize });
  const allProperties = useAppSelector(selectAllProperties);

  if (editingStyle) {
    return (
      <>
        <Button onClick={() => setEditingStyle(false)}>
          Back to main form
        </Button>
        <Text>Editing experience style coming soon™</Text>
      </>
    );
  }

  const buttonPanel = (
    <ButtonGroup size="sm" borderTop="1px solid #DEE5EE" p={4}>
      <Button
        variant="outline"
        onClick={() => router.push(PRIVACY_EXPERIENCE_ROUTE)}
      >
        Cancel
      </Button>
      <Button
        type="submit"
        colorScheme="primary"
        data-testid="save-btn"
        isDisabled={isSubmitting || !dirty || !isValid}
        isLoading={isSubmitting}
      >
        Save
      </Button>
    </ButtonGroup>
  );

  return (
    <PrivacyExperienceConfigColumnLayout buttonPanel={buttonPanel}>
      <BackButton backPath={PRIVACY_EXPERIENCE_ROUTE} mt={4} />
      <Heading fontSize="md" fontWeight="semibold">
        Configure experience
      </Heading>
      <CustomTextInput
        name="name"
        id="name"
        label="Name (internal admin use only)"
        isRequired
        variant="stacked"
      />
      {values.component !== ComponentType.TCF_OVERLAY ? (
        <CustomSelect
          name="component"
          id="component"
          options={componentTypeOptions}
          label="Experience Type"
          variant="stacked"
          isDisabled={!!values.component}
          isRequired
        />
      ) : null}
      <Collapse
        in={
          values.component && values.component !== ComponentType.PRIVACY_CENTER
        }
        animateOpacity
      >
        <Box p="1px">
          <CustomSwitch
            name="dismissable"
            id="dismissable"
            label="Allow user to dismiss"
            variant="stacked"
          />
        </Box>
      </Collapse>
      <ScrollableList
        label="Associated properties"
        addButtonLabel="Add property"
        idField="id"
        nameField="name"
        allItems={allProperties.map((property) => ({
          id: property.id,
          name: property.name,
        }))}
        values={values.properties ?? []}
        setValues={(newValues) => setFieldValue("properties", newValues)}
        draggable
        maxHeight={100}
        baseTestId="property"
      />
      <Divider />
      {values.component !== ComponentType.TCF_OVERLAY ? (
        <>
          <Heading fontSize="md" fontWeight="semibold">
            Privacy notices
          </Heading>
          <ScrollableList
            addButtonLabel="Add privacy notice"
            allItems={allPrivacyNotices.map((n) => n.id)}
            values={values.privacy_notice_ids ?? []}
            setValues={(newValues) =>
              setFieldValue("privacy_notice_ids", newValues)
            }
            getItemLabel={getPrivacyNoticeName}
            draggable
            baseTestId="privacy-notice"
          />
          <Divider />
        </>
      ) : null}
      <Text as="h2" fontWeight="600">
        Locations & Languages
      </Text>
      <ScrollableList
        label="Locations for this experience"
        addButtonLabel="Add location"
        allItems={allSelectedRegions}
        values={values.regions ?? []}
        setValues={(newValues) => setFieldValue("regions", newValues)}
        getItemLabel={(item) => PRIVACY_NOTICE_REGION_RECORD[item]}
        draggable
        baseTestId="location"
      />
      {translationsEnabled ? (
        <>
          <ScrollableList
            label="Languages for this experience"
            addButtonLabel="Add language"
            values={values.translations ?? []}
            setValues={(newValues) => setFieldValue("translations", newValues)}
            idField="language"
            canDeleteItem={(item) => !item.is_default}
            allItems={allLanguages
              .slice()
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((lang) => ({
                language: lang.id as SupportedLanguage,
                is_default: false,
              }))}
            getItemLabel={getTranslationDisplayName}
            createNewValue={(opt) =>
              onCreateTranslation(opt.value as SupportedLanguage)
            }
            onRowClick={onSelectTranslation}
            selectOnAdd
            draggable
            baseTestId="language"
          />
          <CustomSwitch
            name="auto_detect_language"
            id="auto_detect_language"
            label="Auto detect language"
            variant="stacked"
          />
        </>
      ) : (
        <Button
          variant="outline"
          size="sm"
          rightIcon={<ArrowForwardIcon />}
          onClick={() => onSelectTranslation(values.translations![0])}
          data-testid="edit-experience-btn"
        >
          Edit experience text
        </Button>
      )}
    </PrivacyExperienceConfigColumnLayout>
  );
};
export default PrivacyExperienceForm;
