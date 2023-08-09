export type EmailContents = {
  subject: string;
  body: string;
};

export type EmailTemplates = {
  [key: string]: EmailContents;
};
