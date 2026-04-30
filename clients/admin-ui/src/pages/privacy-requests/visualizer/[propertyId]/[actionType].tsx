import { useRouter } from "next/router";
import { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { TraversalVisualizerPage } from "~/features/dsr-traversal-visualizer";
import { ActionType } from "~/features/dsr-traversal-visualizer/types";

const VALID_ACTIONS: ActionType[] = ["access", "erasure"];

const TraversalRoute: NextPage = () => {
  const router = useRouter();
  const propertyId = String(router.query.propertyId ?? "");
  const actionType = (router.query.actionType as ActionType) ?? "access";
  if (!VALID_ACTIONS.includes(actionType)) {
    return null;
  }
  return (
    <Layout title="Traversal Preview">
      {propertyId ? (
        <TraversalVisualizerPage
          propertyId={propertyId}
          actionType={actionType}
        />
      ) : null}
    </Layout>
  );
};

export default TraversalRoute;
