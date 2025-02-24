export class Command {
    callback;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    parameter;
    success = true;
    cmpApiContext;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    constructor(cmpApiContext, callback, parameter) {
        this.cmpApiContext = cmpApiContext;
        Object.assign(this, {
            callback,
            parameter,
        });
    }
    execute() {
        try {
            return this.respond();
        }
        catch (error) {
            this.invokeCallback(null);
            return null;
        }
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    invokeCallback(response) {
        const success = response !== null;
        if (this.callback) {
            this.callback(response, success);
        }
    }
}
