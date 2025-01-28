const { GppModel } = require('@iabgpp/cmpapi');

/** CMP ID assigned to us by the IAB */
const ETHYCA_CMP_ID = 407;

const testCallCmpApi = () => {
    // const cmpApi = new CmpApi(ETHYCA_CMP_ID, 1);
    console.log("TEST");
    const model = new GppModel();
    console.log("model", model);

}

module.exports = {
    testCallCmpApi
};
