import {
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
  selectAllPrivacyNotices,
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
} from "~/features/privacy-notices/privacy-notices.slice";
import {
  ComponentType,
  ExperienceConfigCreate,
  ExperienceTranslation,
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
    <Flex direction="column" h="full" overflowY="scroll" px={4}>
      <Flex direction="column" gap={4} w="full" pb={4}>
        {children}
      </Flex>
    </Flex>
    {buttonPanel}
  </Flex>
);

export const PrivacyExperienceForm = ({
  onSelectTranslation,
}: {
  onSelectTranslation: (t: ExperienceTranslation) => void;
}) => {
  const router = useRouter();

  const [editingStyle, setEditingStyle] = useState<boolean>(false);
  const { values, setFieldValue, dirty, isValid, isSubmitting } =
    useFormikContext<ExperienceConfigCreate>();
  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });
  const allPrivacyNotices = useAppSelector(selectAllPrivacyNotices);

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
        variant="stacked"
      />
      <CustomSelect
        name="component"
        id="component"
        options={componentTypeOptions}
        label="Experience Type"
        variant="stacked"
        isDisabled={!!values.component}
        isRequired
      />
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
            label="Modal is dismissable"
            variant="stacked"
          />
        </Box>
      </Collapse>
      <Divider />
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
      />
      <Divider />
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
      />
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
        createNewValue={(opt) => ({
          language: opt.value as SupportedLanguage,
          is_default: false,
        })}
        onRowClick={onSelectTranslation}
        selectOnAdd
        draggable
      />
      {/* <CustomSwitch
        name="auto_detect_language"
        id="auto_detect_language"
        label="Auto detect language"
        variant="stacked"
      /> */}
    </PrivacyExperienceConfigColumnLayout>
  );
};
export default PrivacyExperienceForm;
