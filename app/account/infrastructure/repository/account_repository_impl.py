"""Account repository implementation using SQLAlchemy."""

from typing import Optional

from sqlalchemy.orm import Session as DBSession
from app.config.database.session import get_db_session

from app.account.domain.entity.account import Account
from app.account.domain.entity.account_enums import (
    AccountPlan,
    AccountRole,
    AccountStatus, Gender, Mbti,
)
from app.account.application.port.account_repository_port import AccountRepositoryPort
from app.account.infrastructure.orm.account_model import AccountModel


class AccountRepositoryImpl(AccountRepositoryPort):
    """SQLAlchemy implementation of AccountRepositoryPort.

    This adapter implements the application port using SQLAlchemy for persistence.
    """

    def __init__(self, db_session: Optional[DBSession] = None):
        """Initialize with a database session.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._session: DBSession = db_session or get_db_session()

    def find_by_id(self, account_id: int) -> Optional[Account]:
        """Find an account by its ID."""
        try:
            model = (
                self._session.query(AccountModel)
                .filter(AccountModel.id == account_id)
                .first()
            )
            return self._to_entity(model) if model else None
        finally:
            self._session.close()

    def find_by_email(self, email: str) -> Optional[Account]:
        """Find an account by email address."""
        try:
            model = (
                self._session.query(AccountModel)
                .filter(AccountModel.email == email)
                .first()
            )
            return self._to_entity(model) if model else None
        finally:
            self._session.close()

    def save(self, account: Account) -> Account:
        """Save an account (create or update)."""
        try:
            if account.is_new():
                # Create new account
                model = self._to_model(account)
                self._session.add(model)
                self._session.commit()
                self._session.refresh(model)
                return self._to_entity(model)
            else:
                # Update existing account
                model = (
                    self._session.query(AccountModel)
                    .filter(AccountModel.id == account.id)
                    .first()
                )
                if model:
                    model.email = account.email
                    model.nickname = account.nickname
                    model.terms_agreed = account.terms_agreed
                    model.terms_agreed_at = account.terms_agreed_at
                    # Update new fields
                    model.role = account.role.value if isinstance(account.role, AccountRole) else account.role
                    model.plan = account.plan.value if isinstance(account.plan, AccountPlan) else account.plan
                    model.plan_started_at = account.plan_started_at
                    model.plan_ends_at = account.plan_ends_at
                    model.billing_customer_id = account.billing_customer_id
                    model.status = account.status.value if isinstance(account.status, AccountStatus) else account.status

                    # 추가 : mbti /gender
                    model.mbti = account.mbti.value if account.mbti else None
                    model.gender = account.gender.value if account.gender else None

                    self._session.commit()
                    self._session.refresh(model)
                    return self._to_entity(model)
                else:
                    # Account not found, create new
                    return self.save(Account(
                        email=account.email,
                        nickname=account.nickname,
                        terms_agreed=account.terms_agreed,
                        terms_agreed_at=account.terms_agreed_at,
                        mbti=account.mbti,
                        gender=account.gender,
                    ))
        finally:
            self._session.close()

    def exists_by_email(self, email: str) -> bool:
        """Check if an account exists with the given email."""
        try:
            return (
                self._session.query(AccountModel)
                .filter(AccountModel.email == email)
                .first()
                is not None
            )
        finally:
            self._session.close()

    @staticmethod
    def _to_entity(model: AccountModel) -> Account:
        """Convert SQLAlchemy model to domain entity."""
        return Account(
            id=model.id,
            email=model.email,
            nickname=model.nickname,
            terms_agreed=model.terms_agreed,
            terms_agreed_at=model.terms_agreed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            role=AccountRole.from_string(model.role) if model.role else AccountRole.USER,
            plan=AccountPlan.from_string(model.plan) if model.plan else AccountPlan.FREE,
            plan_started_at=model.plan_started_at,
            plan_ends_at=model.plan_ends_at,
            billing_customer_id=model.billing_customer_id,
            gender=Gender.from_string(model.gender) if model.gender else None,
            mbti=Mbti.from_string(model.mbti) if model.mbti else None,
            status=AccountStatus.from_string(model.status) if model.status else AccountStatus.ACTIVE,
        )

    @staticmethod
    def _to_model(entity: Account) -> AccountModel:
        """Convert domain entity to SQLAlchemy model."""
        return AccountModel(
            id=entity.id,
            email=entity.email,
            nickname=entity.nickname,
            terms_agreed=entity.terms_agreed,
            terms_agreed_at=entity.terms_agreed_at,
            role=entity.role.value if isinstance(entity.role, AccountRole) else entity.role,
            plan=entity.plan.value if isinstance(entity.plan, AccountPlan) else entity.plan,
            plan_started_at=entity.plan_started_at,
            plan_ends_at=entity.plan_ends_at,
            billing_customer_id=entity.billing_customer_id,
            gender=entity.gender.value if entity.gender else None,
            mbti=entity.mbti.value if entity.mbti else None,
            status=entity.status.value if isinstance(entity.status, AccountStatus) else entity.status,
        )
