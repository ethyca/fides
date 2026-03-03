export const frameworks = [
  {
    id: "gdpr",
    label: "GDPR",
    description: "General Data Protection Regulation (EU)",
  },
  {
    id: "ccpa",
    label: "CCPA / CPRA",
    description: "California Consumer Privacy Act",
  },
  {
    id: "hipaa",
    label: "HIPAA",
    description: "Health Insurance Portability Act",
  },
  {
    id: "nist",
    label: "NIST AI RMF",
    description: "AI Risk Management Framework",
  },
  {
    id: "eu-ai",
    label: "EU AI Act",
    description: "Artificial Intelligence Act",
  },
  {
    id: "iso",
    label: "ISO 42001",
    description: "AI Management System Standard",
  },
];

export const dpoOptions = [
  { id: "jd", name: "Jane Doe", role: "Data Protection Officer" },
  { id: "sj", name: "Sarah Johnson", role: "Privacy Lead" },
  { id: "mp", name: "Michael Park", role: "Compliance Manager" },
  { id: "al", name: "Anna Lee", role: "Legal Counsel" },
];

export const mockAssessments = {
  gdpr: {
    templateId: "GDPR-DPIA-2024",
    title: "GDPR Data Protection Impact Assessment",
    assessments: [
      {
        id: "1",
        name: "Customer Insight AI Module",
        status: "updated",
        statusTime: "2h ago",
        riskLevel: "High",
        completeness: 75,
        owner: "SJ",
      },
      {
        id: "2",
        name: "Employee Monitoring Tool",
        status: "outdated",
        riskLevel: "Med",
        completeness: 40,
        owner: "MP",
      },
      {
        id: "3",
        name: "Marketing Analytics Platform",
        status: "completed",
        statusTime: "Jan 15, 2024",
        riskLevel: "Low",
        completeness: 100,
        owner: "AL",
      },
      {
        id: "4",
        name: "Customer Support Chat System",
        status: "updated",
        statusTime: "3h ago",
        riskLevel: "Med",
        completeness: 65,
        owner: "SJ",
      },
      {
        id: "5",
        name: "HR Payroll Processing",
        status: "outdated",
        riskLevel: "High",
        completeness: 30,
        owner: "MP",
      },
      {
        id: "6",
        name: "E-commerce Recommendation Engine",
        status: "completed",
        statusTime: "Jan 12, 2024",
        riskLevel: "Med",
        completeness: 100,
        owner: "AL",
      },
    ],
  },
  ccpa: {
    templateId: "CCPA-PIA-2024",
    title: "CCPA Privacy Impact Assessment",
    assessments: [
      {
        id: "7",
        name: "Consumer Data Collection System",
        status: "updated",
        statusTime: "1h ago",
        riskLevel: "High",
        completeness: 70,
        owner: "SJ",
      },
      {
        id: "8",
        name: "Third-Party Data Sharing Platform",
        status: "outdated",
        riskLevel: "Med",
        completeness: 45,
        owner: "MP",
      },
      {
        id: "9",
        name: "Opt-Out Request Handler",
        status: "completed",
        statusTime: "Jan 10, 2024",
        riskLevel: "Low",
        completeness: 100,
        owner: "AL",
      },
      {
        id: "10",
        name: "Data Broker Integration",
        status: "outdated",
        riskLevel: "High",
        completeness: 25,
        owner: "SJ",
      },
    ],
  },
};

export const mockSystemNames = [
  "Customer Insight AI Module",
  "Employee Monitoring Tool",
  "Marketing Analytics Platform",
  "Customer Support Chat System",
  "HR Payroll Processing",
  "E-commerce Recommendation Engine",
  "Consumer Data Collection System",
  "Third-Party Data Sharing Platform",
  "Opt-Out Request Handler",
  "Data Broker Integration",
];
