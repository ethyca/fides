package devtools.validation

import devtools.controller.RequestContext
import devtools.domain.{OneToMany, Registry, SystemObject}
import devtools.persist.dao.DAOs
import devtools.persist.db.Queries.systemQuery
import slick.jdbc.MySQLProfile.api._

import scala.concurrent.{ExecutionContext, Future}

class RegistryValidator(val daos: DAOs)(implicit val executionContext: ExecutionContext)
  extends Validator[Registry, Long] with ValidateByOrganization {

  /** Validations:
    *
    * - require that referenced organization exists.
    *
    * - require that any included system ids exist, if they are posted as declared system ids.
    */
  def requireSystemIdsExists(
    organizationId: Long,
    declaredSystemIds: OneToMany[Long, SystemObject],
    errors: MessageCollector
  ): Future[MessageCollector] = {
    declaredSystemIds match {
      case Some(Left(ids)) if ids.nonEmpty => {
        val foundIds: Future[Seq[Long]] = daos.systemDAO.runAction(
          systemQuery.filter(sys => (sys.organizationId === organizationId) && (sys.id inSet ids)).map(_.id).result
        )

        foundIds.foreach(fids => {
          val diff = fids.toSet.diff(ids.toSet)
          if (diff.nonEmpty) {
            errors.addError(s"""the referenced system ids ${diff.mkString(",")} were not found.""")
          }
        })
      }
      case _ =>
    }

    Future.successful(errors)
  }

  /** Perform any validations on the input object and collect any errors found. */

  def validateForCreate(r: Registry, ctx: RequestContext): Future[Unit] =
    requireOrganizationIdExists(r.organizationId, new MessageCollector)
      .flatMap(e => requireSystemIdsExists(r.organizationId, r.systems, e))
      .flatMap(_.asFuture())

}
