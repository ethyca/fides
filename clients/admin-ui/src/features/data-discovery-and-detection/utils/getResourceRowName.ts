import { StagedResource } from "~/types/api";

const getResourceRowName = (row: StagedResource) => row.urn;

export default getResourceRowName;
