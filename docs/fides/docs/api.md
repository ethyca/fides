# Fides Server

The Fides API server hosts endpoints that support the CLI functionality. Normally you interact with the server though the CLI, but enpoints are available for direct communication via JSON/YAML.


## Authentication
Requests are currently authenticated via a user id along with a JWT token generated from your user token. Please note that the current authentication implementation should be consider a "placeholder"  and future expansion is planned.

Headers:

|   key    |       value          |
|   :---      |       :---               |
| user-id| Integer value of your user id |
| Authorization  |  Bearer {JWT}  where the token is generated from the user-id and provided token  |
| Content-Type   |  "application/json" - for json ingestion |

## Endpoints

Further documentation can be found on the servers swagger endpoint at `SERVER_URL/swagger`

|   endpoint    |    method     |     description     |
| :---     |   :---:    |    :---    |
|  data-use |    |    |
|/v1/data-use/|post|Create a new instance of  DataUse|
|/v1/data-use/find/{key}|get| Find DataUse by unique key|
|/v1/data-use/taxonomy|get|Display parent-child arrangement of all DataUse values|
|/v1/data-use/{id}|delete|Delete DataUse by id|
|/v1/data-use/{id}/taxonomy|get|Tree structure of DataUse data for children of the given id|
|  data-qualifier|    |    |
|/v1/data-qualifier/|post|Create a new instance of  DataQualifier|
|/v1/data-qualifier/find/{key}|get| Find DataQualifier by unique key|
|/v1/data-qualifier/taxonomy|get|Display parent-child arrangement of all DataQualifier values|
|/v1/data-qualifier/{id}|delete|Delete DataQualifier by id|
|/v1/data-qualifier/{id}/taxonomy|get|Tree structure of DataQualifier data for children of the given id|
|  data-subject |    |    |
|/v1/data-subject/|post|Create a new instance of  DataSubject|
|/v1/data-subject/find/{key}|get| Find DataSubject by unique key|
|/v1/data-subject/taxonomy|get|Display parent-child arrangement of all DataSubject values|
|/v1/data-subject/{id}|delete|Delete DataSubject by id|
|/v1/data-subject/{id}/taxonomy|get|Tree structure of DataSubject data for children of the given id|
|  data-category |    |    |
|/v1/data-category/|post|Create a new instance of  DataCategory|
|/v1/data-category/find/{key}|get| Find DataCategory by unique key|
|/v1/data-category/taxonomy|get|Display parent-child arrangement of all DataCategory values|
|/v1/data-category/{id}|delete|Delete DataCategory by id|
|/v1/data-category/{id}/taxonomy|get|Tree structure of DataCategory data for children of the given id|
|  system   |     |     |
|/v1/system/|post|Create a new instance of  SystemObject|
|/v1/system/evaluate/dry-run|post|Evaluate the posted system as a 'dry-run' only.|
|/v1/system/evaluate/{fidesKey}|get|run and store evaluation on the specified system.|
|/v1/system/evaluate/{fidesKey}/last|get|Return the current approval state of the specified system.|
|/v1/system/find/{key}|get|Find SystemObject by unique key|
|/v1/system/validateForCreate|post|validateForCreate (pre-flight) a system and report on any errors|
|/v1/system/{id}|delete|Delete SystemObject by id|
|  organization  |     |     |
|/v1/organization/|post|Create a new instance of  Organization|
|/v1/organization/find/{key}|get|Find Organization by unique key|
|/v1/organization/{id}|delete|Delete Organization by id|
|  policy   |     |     |
|/v1/policy/|post|Create a new instance of  Policy|
|/v1/policy/find/{key}|get|Find Policy by unique key|
|/v1/policy/{id}|delete|Delete Policy by id|
| policy rule   |     |     |
|/v1/policy-rule/|post|Create a new instance of  PolicyRule|
|/v1/policy-rule/find/{key}|get|Find PolicyRule by unique key|
|/v1/policy-rule/{id}|delete|Delete PolicyRule by id|
|   dataset   |    |   |
|/v1/dataset/|post|Create a new instance of  Dataset|
|/v1/dataset/find/{key}|get|Find Dataset by unique key|
|/v1/dataset/{id}|delete|Delete Dataset by id|
|  dataset field   |     |     |
|/v1/dataset-field/|post|Create a new instance of  DatasetField|
|/v1/dataset-field/{id}|delete|Delete DatasetField by id|
|  registry   |     |    |
|/v1/registry/|post|Create a new instance of  Registry|
|/v1/registry/evaluate/dry-run|post|Evaluate the posted registry as a 'dry-run' only.|
|/v1/registry/evaluate/{fidesKey}|get|run and store evaluation on the specified system.|
|/v1/registry/evaluate/{fidesKey}/last|get|Return the current approval state of the specified registry.|
|/v1/registry/find/{key}|get|Find Registry by unique key|
|/v1/registry/{id}|delete|Delete Registry by id|
|  user   |     |     |
|/v1/user/|post|Create a new instance of  User|
|/v1/user/find/{key}|get|"Find User by unique key|
|/v1/user/{id}|delete|Delete User by id|
|  approval   |     |     |
|/v1/approval/|post|Create a new instance of  Approval|
|/v1/approval/{id}|delete|Delete Approval by id|
|  reports   |     |     |
|/v1/report/|get|find all operations for the calling organization| |
|/v1/report/registry/{id}|get|find all operations for the specified registry|
|/v1/report/system/{id}|get|find all operations for the specified system|
|  admin   |     |     |
|/v1/admin/organization/{id}|delete|delete all sub-objects in an organization; leaves the organization intact|
|  audit-log  |     |     |
|/v1/audit-log/|get|Shows all the AuditLogs|
|/v1/audit-log/{objectType}/{id}|get|Find audit log operations for a specified object|
