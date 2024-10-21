import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import ProjectsTable from "~/features/dataset-lifecycle/projects/ProjectsTable";

const E2EDatasetProjectView = () => {
  return (
    <Layout title="E2E datasets">
      <PageHeader
        breadcrumbs={[{ title: "E2E datasets" }, { title: "Some system" }]}
      />
      <ProjectsTable />
    </Layout>
  );
};

export default E2EDatasetProjectView;
