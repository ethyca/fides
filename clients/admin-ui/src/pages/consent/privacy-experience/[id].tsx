import { Center, Spinner, Text } from "@fidesui/react";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import ConfigurePrivacyExperience from "~/features/privacy-experience/ConfigurePrivacyExperience";
import { useGetExperienceConfigByIdQuery } from "~/features/privacy-experience/privacy-experience.slice";

const PrivacyExperienceDetailPage = () => {
  const router = useRouter();

  let experienceId = "";
  if (router.query.id) {
    experienceId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  const { data, isLoading } = useGetExperienceConfigByIdQuery(experienceId);

  if (isLoading) {
    return (
      <Layout title="Privacy experience">
        <Center>
          <Spinner />
        </Center>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout title="Privacy experience">
        <Text>No privacy experience with id {experienceId} found.</Text>
      </Layout>
    );
  }

  return (
    <Layout title={`Privacy experience ${data.component}`} padded={false}>
      <ConfigurePrivacyExperience passedInExperience={data} />
    </Layout>
  );
};

export default PrivacyExperienceDetailPage;
