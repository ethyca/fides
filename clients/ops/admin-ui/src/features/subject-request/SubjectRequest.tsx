import React from "react";

import { PrivacyRequest } from "../privacy-requests/types";
import EventsAndLogs from "./events-and-logs/EventsAndLogs";
import RequestDetails from "./RequestDetails";
import SubjectIdentities from "./SubjectIdentities";

type SubjectRequestProps = {
  subjectRequest: PrivacyRequest;
};

const SubjectRequest = ({ subjectRequest }: SubjectRequestProps) => (
  <>
    <RequestDetails subjectRequest={subjectRequest} />
    <SubjectIdentities subjectRequest={subjectRequest} />
    <EventsAndLogs subjectRequest={subjectRequest} />
  </>
);

export default SubjectRequest;
