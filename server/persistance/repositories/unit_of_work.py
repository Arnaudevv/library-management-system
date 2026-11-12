from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class AbstractUnitOfWork(ABC):
    """Contract for a unit of work: one transaction per `with` block."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Rollback on error, commit otherwise.
        if exc_type:
            self.rollback()
        else:
            self.commit()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """Unit of work backed by a SQLAlchemy session."""

    def __init__(self, session: Session):
        self.session = session

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.session.close()  # always release the connection

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


class UnitOfWorkFactory:
    """Creates the engine once and builds a new unit of work per request."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=True,
            expire_on_commit=False,
        )

    def create(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory())