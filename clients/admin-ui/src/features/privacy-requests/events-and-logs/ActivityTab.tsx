import { AntButton as Button, AntFlex as Flex } from "fidesui";
import { useState } from "react";

import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { PrivacyRequestEntity } from "../types";
import ActivityTimeline from "./ActivityTimeline";
import { CommentInput } from "./CommentInput";

type ActivityTabProps = {
  subjectRequest: PrivacyRequestEntity;
};

const ActivityTab = ({ subjectRequest }: ActivityTabProps) => {
  const [showCommentInput, setShowCommentInput] = useState(false);

  return (
    <div className="w-full">
      <ActivityTimeline subjectRequest={subjectRequest} />

      {showCommentInput ? (
        <CommentInput
          privacyRequestId={subjectRequest.id}
          onCancel={() => setShowCommentInput(false)}
        />
      ) : (
        <Restrict scopes={[ScopeRegistryEnum.COMMENT_CREATE]}>
          <Flex justify="flex-start" className="mt-2">
            <Button
              type="default"
              onClick={() => setShowCommentInput(true)}
              className="flex items-center"
              data-testid="add-comment-button"
            >
              Add comment <span className="ml-1">+</span>
            </Button>
          </Flex>
        </Restrict>
      )}
    </div>
  );
};

export default ActivityTab;
