package devtools.persist.db

import devtools.domain._
import devtools.domain.definition.{IdType, OrganizationId, VersionStamp}
import devtools.domain.policy.{Policy, PolicyRule}
import org.slf4j.{Logger, LoggerFactory}
import slick.jdbc.MySQLProfile.api._

import java.sql.Timestamp
abstract class BaseTable[E <: IdType[E, PK], PK](tag: Tag, tableName: String) extends Table[E](tag, tableName) {
  def id: slick.lifted.Rep[PK]
}

abstract class BaseAutoIncTable[E <: IdType[E, Long]](tag: Tag, tableName: String)
  extends BaseTable[E, Long](tag, tableName) {
  def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
}

trait OrganizationIdTable[E <: IdType[E, Long] with OrganizationId] { self: BaseAutoIncTable[E] =>
  val organizationId: Rep[Long] = column[Long]("organization_id")
}
trait VersionStampTable[E <: IdType[E, Long] with VersionStamp] { self: BaseAutoIncTable[E] =>
  val versionStamp: Rep[Option[Long]] = column[Option[Long]]("version_stamp")
}

object Tables {

  val logger: Logger = LoggerFactory.getLogger(getClass)

  class ApprovalQuery(tag: Tag)
    extends BaseAutoIncTable[Approval](tag, "APPROVAL") with OrganizationIdTable[Approval]
    with VersionStampTable[Approval] {
    val systemId: Rep[Option[Long]]          = column[Option[Long]]("system_id")
    val registryId: Rep[Option[Long]]        = column[Option[Long]]("registry_id")
    val userId: Rep[Long]                    = column[Long]("user_id")
    val submitTag: Rep[Option[String]]       = column[Option[String]]("submit_tag")
    val submitMessage: Rep[Option[String]]   = column[Option[String]]("submit_message")
    val action: Rep[String]                  = column[String]("action")
    val status: Rep[String]                  = column[String]("status")
    val details: Rep[Option[String]]         = column[Option[String]]("details")
    val creationTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("creation_time", O.AutoInc)
    def * =
      (
        id,
        organizationId,
        systemId,
        registryId,
        userId,
        versionStamp,
        submitTag,
        submitMessage,
        action,
        status,
        details,
        creationTime
      ) <> (Approval.fromInsertable, Approval.toInsertable)
  }

  class AuditLogQuery(tag: Tag)
    extends BaseAutoIncTable[AuditLog](tag, "AUDIT_LOG") with OrganizationIdTable[AuditLog]
    with VersionStampTable[AuditLog] {
    val objectId: Rep[Long]                  = column[Long]("object_id")
    val userId: Rep[Long]                    = column[Long]("user_id")
    val action: Rep[String]                  = column[String]("action")
    val typeName: Rep[String]                = column[String]("type_name")
    val fromValue: Rep[Option[String]]       = column[Option[String]]("from_value")
    val toValue: Rep[Option[String]]         = column[Option[String]]("to_value")
    val change: Rep[Option[String]]          = column[Option[String]]("change")
    val creationTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("creation_time", O.AutoInc)

    def * =
      (
        id,
        objectId,
        organizationId,
        versionStamp,
        userId,
        action,
        typeName,
        fromValue,
        toValue,
        change,
        creationTime
      ) <> (AuditLog.fromInsertable, AuditLog.toInsertable)

  }

  class OrganizationQuery(tag: Tag)
    extends BaseAutoIncTable[Organization](tag, "ORGANIZATION") with VersionStampTable[Organization] {
    val fidesKey: Rep[String]                  = column[String]("fides_key")
    val name: Rep[Option[String]]              = column[Option[String]]("name")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)

    def * =
      (
        id,
        fidesKey,
        versionStamp,
        name,
        description,
        creationTime,
        lastUpdateTime
      ) <> (Organization.fromInsertable, Organization.toInsertable)
  }

  class SystemQuery(tag: Tag)
    extends BaseAutoIncTable[SystemObject](tag, "SYSTEM_OBJECT") with OrganizationIdTable[SystemObject]
    with VersionStampTable[SystemObject] {
    val registryId: Rep[Option[Long]]          = column[Option[Long]]("registry_id")
    val fidesKey: Rep[String]                  = column[String]("fides_key")
    val metadata: Rep[Option[String]]          = column[Option[String]]("metadata")
    val name: Rep[Option[String]]              = column[Option[String]]("name")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val systemType: Rep[Option[String]]        = column[Option[String]]("system_type")
    val privacyDeclarations: Rep[String]       = column[String]("privacy_declarations")
    val systemDependencies: Rep[String]        = column[String]("system_dependencies")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)
    def * =
      (
        id,
        organizationId,
        registryId,
        fidesKey,
        versionStamp,
        metadata,
        name,
        description,
        systemType,
        privacyDeclarations,
        systemDependencies,
        creationTime,
        lastUpdateTime
      ) <> (SystemObject.fromInsertable, SystemObject.toInsertable)
  }
  /*
   * Dataset types
   */
  /** Table description of table DATASET. Objects of this class serve as prototypes for rows in queries. */
  class DatasetQuery(tag: Tag)
    extends BaseAutoIncTable[Dataset](tag, "DATASET") with OrganizationIdTable[Dataset]
    with VersionStampTable[Dataset] {
    val fidesKey: Rep[String]                  = column[String]("fides_key")
    val metadata: Rep[Option[String]]          = column[Option[String]]("metadata")
    val name: Rep[Option[String]]              = column[Option[String]]("name")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val location: Rep[Option[String]]          = column[Option[String]]("location")
    val datasetType: Rep[Option[String]]       = column[Option[String]]("dataset_type")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("creation_time", O.AutoInc)

    def * =
      (
        id,
        organizationId,
        fidesKey,
        versionStamp,
        metadata,
        name,
        description,
        location,
        datasetType,
        creationTime,
        lastUpdateTime
      ) <> (Dataset.fromInsertable, Dataset.toInsertable)
  }

  class DatasetFieldQuery(tag: Tag) extends BaseAutoIncTable[DatasetField](tag, "DATASET_FIELD") {

    val datasetId: Rep[Long]                   = column[Long]("dataset_id")
    val name: Rep[String]                      = column[String]("name")
    val path: Rep[Option[String]]                      = column[Option[String]]("path")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val dataCategories: Rep[Option[String]]    = column[Option[String]]("data_categories")
    val dataQualifier: Rep[Option[String]]     = column[Option[String]]("data_qualifier")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)
    def * =
      (
        id,
        datasetId,
        name,
        path,
        description,
        dataCategories,
        dataQualifier,
        creationTime,
        lastUpdateTime
      ) <> (DatasetField.fromInsertable, DatasetField.toInsertable)

  }

  /*
   * Taxonomy types
   */
  class DataCategoryQuery(tag: Tag)
    extends BaseAutoIncTable[DataCategory](tag, "DATA_CATEGORY") with OrganizationIdTable[DataCategory] {
    val parentId: Rep[Option[Long]]      = column[Option[Long]]("parent_id")
    val fidesKey: Rep[String]            = column[String]("fides_key")
    val name: Rep[Option[String]]        = column[Option[String]]("name")
    val clause: Rep[Option[String]]      = column[Option[String]]("clause")
    val description: Rep[Option[String]] = column[Option[String]]("description")
    def * =
      (
        id,
        parentId,
        organizationId,
        fidesKey,
        name,
        clause,
        description
      ) <> (DataCategory.fromInsertable, DataCategory.toInsertable)
  }

  class DataUseQuery(tag: Tag) extends BaseAutoIncTable[DataUse](tag, "DATA_USE") with OrganizationIdTable[DataUse] {
    val parentId: Rep[Option[Long]]      = column[Option[Long]]("parent_id")
    val fidesKey: Rep[String]            = column[String]("fides_key")
    val name: Rep[Option[String]]        = column[Option[String]]("name")
    val clause: Rep[Option[String]]      = column[Option[String]]("clause")
    val description: Rep[Option[String]] = column[Option[String]]("description")
    def * =
      (
        id,
        parentId,
        organizationId,
        fidesKey,
        name,
        clause,
        description
      ) <> (DataUse.fromInsertable, DataUse.toInsertable)
  }
  class DataQualifierQuery(tag: Tag)
    extends BaseAutoIncTable[DataQualifier](tag, "DATA_QUALIFIER") with OrganizationIdTable[DataQualifier] {
    val parentId: Rep[Option[Long]]      = column[Option[Long]]("parent_id")
    val fidesKey: Rep[String]            = column[String]("fides_key")
    val name: Rep[Option[String]]        = column[Option[String]]("name")
    val clause: Rep[Option[String]]      = column[Option[String]]("clause")
    val description: Rep[Option[String]] = column[Option[String]]("description")
    def * =
      (
        id,
        parentId,
        organizationId,
        fidesKey,
        name,
        clause,
        description
      ) <> (DataQualifier.fromInsertable, DataQualifier.toInsertable)
  }
  class DataSubjectQuery(tag: Tag)
    extends BaseAutoIncTable[DataSubject](tag, "DATA_SUBJECT") with OrganizationIdTable[DataSubject] {
    val parentId: Rep[Option[Long]]      = column[Option[Long]]("parent_id")
    val fidesKey: Rep[String]            = column[String]("fides_key")
    val name: Rep[Option[String]]        = column[Option[String]]("name")
    val description: Rep[Option[String]] = column[Option[String]]("description")
    def * =
      (
        id,
        parentId,
        organizationId,
        fidesKey,
        name,
        description
      ) <> (DataSubject.fromInsertable, DataSubject.toInsertable)
  }
  class RegistryQuery(tag: Tag)
    extends BaseAutoIncTable[Registry](tag, "REGISTRY") with OrganizationIdTable[Registry]
    with VersionStampTable[Registry] {
    val fidesKey: Rep[String]                  = column[String]("fides_key")
    val metadata: Rep[Option[String]]          = column[Option[String]]("metadata")
    val name: Rep[Option[String]]              = column[Option[String]]("name")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)

    def * =
      (
        id,
        organizationId,
        fidesKey,
        versionStamp,
        metadata,
        name,
        description,
        creationTime,
        lastUpdateTime
      ) <> (Registry.fromInsertable, Registry.toInsertable)

  }

  class PolicyQuery(tag: Tag)
    extends BaseAutoIncTable[Policy](tag, "POLICY") with OrganizationIdTable[Policy] with VersionStampTable[Policy] {
    val fidesKey: Rep[String]                  = column[String]("fides_key")
    val name: Rep[Option[String]]              = column[Option[String]]("name")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)
    def * =
      (
        id,
        organizationId,
        fidesKey,
        versionStamp,
        name,
        description,
        creationTime,
        lastUpdateTime
      ) <> (Policy.fromInsertable, Policy.toInsertable)
  }

  class PolicyRuleQuery(tag: Tag)
    extends BaseAutoIncTable[PolicyRule](tag, "POLICY_RULE") with OrganizationIdTable[PolicyRule] {
    val policyId: Rep[Long]                    = column[Long]("policy_id")
    val fidesKey: Rep[String]                  = column[String]("fides_key")
    val name: Rep[Option[String]]              = column[Option[String]]("name")
    val description: Rep[Option[String]]       = column[Option[String]]("description")
    val dataCategories: Rep[String]            = column[String]("data_categories")
    val dataUses: Rep[String]                  = column[String]("data_uses")
    val dataSubjectCategories: Rep[String]     = column[String]("data_subject_categories")
    val dataQualifier: Rep[Option[String]]     = column[Option[String]]("data_qualifier")
    val action: Rep[String]                    = column[String]("action")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)

    def * =
      (
        id,
        organizationId,
        policyId,
        fidesKey,
        name,
        description,
        dataCategories,
        dataUses,
        dataSubjectCategories,
        dataQualifier,
        action,
        creationTime,
        lastUpdateTime
      ) <> (PolicyRule.fromInsertable, PolicyRule.toInsertable)
  }

  class UserQuery(tag: Tag) extends BaseAutoIncTable[User](tag, "USER") with OrganizationIdTable[User] {
    val userName: Rep[String]                  = column[String]("user_name")
    val firstName: Rep[Option[String]]         = column[Option[String]]("first_name")
    val lastName: Rep[Option[String]]          = column[Option[String]]("last_name")
    val role: Rep[String]                      = column[String]("role")
    val apiKey: Rep[String]                    = column[String]("api_key")
    val creationTime: Rep[Option[Timestamp]]   = column[Option[Timestamp]]("creation_time", O.AutoInc)
    val lastUpdateTime: Rep[Option[Timestamp]] = column[Option[Timestamp]]("last_update_time", O.AutoInc)
    def * =
      (
        id,
        organizationId,
        userName,
        firstName,
        lastName,
        role,
        apiKey,
        creationTime,
        lastUpdateTime
      ) <> (User.fromInsertable, User.toInsertable)

  }

}
