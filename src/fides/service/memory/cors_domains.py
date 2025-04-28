from abc import abstractmethod
from typing import Protocol

from fastapi import Request
from sqlalchemy.orm import Session

from fides.config.config_proxy import ConfigProxy


class CORSDomainsService(Protocol):
    @abstractmethod
    def update_cors_domains(self, request: Request) -> None: ...


class CORSDomainsInMemoryService(CORSDomainsService):
    def __init__(self, db: Session):
        self.db = db

    def update_cors_domains(self, request):
        ConfigProxy(self.db).load_current_cors_domains_into_middleware(request.app)


class CORSDomainsMessagePublisherService(CORSDomainsService):
    def update_cors_domains(self, request):
        raise NotImplementedError


class CORSDomainMessageReceiverService:
    def __init__(self, cors_domain_service: CORSDomainsInMemoryService):
        self.cors_domain_service = cors_domain_service

    # Handle or something like that, calls cors_domain_server.update_cors_domains
