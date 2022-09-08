from fideslib.db.base_class import Base
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import backref, relationship

from fidesops.ops.models.connectionconfig import ConnectionConfig


class AccessManualWebhook(Base):
    """Describes a manual datasource that will be used for access requests.

    These data sources are not treated as part of the traversal.  Data uploaded
    for an AccessManualWebhook is passed on as-is to the end user and is
    not consumed as part of the graph.
    """

    connection_config_id = Column(
        String, ForeignKey(ConnectionConfig.id_field_path), unique=True, nullable=False
    )
    connection_config = relationship(
        ConnectionConfig, backref=backref("access_manual_webhook", uselist=False)
    )

    fields = Column(MutableList.as_mutable(JSONB), nullable=False)
