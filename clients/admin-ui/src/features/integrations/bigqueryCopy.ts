export type InfoBlock = {
  title: string;
  description: string[];
};

const BIGQUERY_COPY: InfoBlock[] = [
  {
    title: "Overview",
    description: [
      "View and continuously discover personal data risks and compliance requirements in accordance with industry standards.",
    ],
  },
  {
    title: "Step 1: Create Service Account Key",
    description: [
      "To configure data discovery , you'll need a Service Account configured with the proper permission sets and an associated Service Account Key.",
      "This setup guide will walk you through the steps you'll need to take via your Google Cloud Console.",
    ],
  },
  {
    title: "Step 2: Configure Secrets",
    description: [
      "Now that you have created a Service Account and Service Account Key in Google Cloud Platform (GCP) in the prior step, it's now time to set up a connection via the Fides UI.",
    ],
  },
];

export default BIGQUERY_COPY;
