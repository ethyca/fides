import React from "react";

import { PrivacyRequest } from "../privacy-requests/types";
import RequestDetails from "./RequestDetails";
import SubjectIdentities from "./SubjectIdentities";

type SubjectRequestProps = {
  subjectRequest: PrivacyRequest;
};

const SubjectRequest = ({ subjectRequest }: SubjectRequestProps) => (
  <>
    <RequestDetails subjectRequest={subjectRequest} />
    <SubjectIdentities subjectRequest={subjectRequest} />
  </>
);

export default SubjectRequest;
