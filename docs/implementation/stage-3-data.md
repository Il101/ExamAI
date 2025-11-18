# Stage 3: Data Layer

**Time:** 3-4 days  
**Goal:** Implement database layer with SQLAlchemy, Alembic migrations, Repository pattern, and mappers

## 3.1 Database Architecture

### Philosophy
- **Async Everything**: Use asyncpg + SQLAlchemy async
- **Repository Pattern**: Abstract database operations
- **Mappers**: Convert between Domain ↔ DB models
- **Row Level Security**: Leverage Supabase RLS for multi-tenancy

---

## 3.2 SQLAlchemy Models

### Step 3.2.1: Base Model Setup
```python
# backend/app/db/base.py
from datetime import datetime
from typing import Any
from sqlalchemy import MetaData, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid


# Naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Base class for all database models"""
    metadata = metadata
    
    # Common columns for all tables
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
```

### Step 3.2.2: User Model
```python
# backend/app/db/models/user.py
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.db.base import Base


class UserModel(Base):
    """SQLAlchemy User model"""
    
    __tablename__ = "users"
    
    # Basic info
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Role & subscription
    role: Mapped[str] = mapped_column(String(50), default="student", nullable=False)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    
    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # verification_token is handled by Supabase Auth
    
    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(10), default="ru", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    daily_study_goal_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    
    # Timestamps (inherited from Base + additional)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    exams: Mapped[list["ExamModel"]] = relationship(
        "ExamModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    topics: Mapped[list["TopicModel"]] = relationship(
        "TopicModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    review_items: Mapped[list["ReviewItemModel"]] = relationship(
        "ReviewItemModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    study_sessions: Mapped[list["StudySessionModel"]] = relationship(
        "StudySessionModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    subscriptions: Mapped[list["SubscriptionModel"]] = relationship(
        "SubscriptionModel",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email={self.email})>"
```

### Step 3.2.3: Exam Model
```python
# backend/app/db/models/exam.py
from sqlalchemy import String, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
import uuid
from app.db.base import Base


class ExamModel(Base):
    """SQLAlchemy Exam model"""
    
    __tablename__ = "exams"
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Content
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    
    # AI usage tracking
    token_count_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Topic count
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="exams")
    
    topics: Mapped[list["TopicModel"]] = relationship(
        "TopicModel",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="TopicModel.order_index"
    )
    
    study_sessions: Mapped[list["StudySessionModel"]] = relationship(
        "StudySessionModel",
        back_populates="exam",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ExamModel(id={self.id}, title={self.title}, status={self.status})>"
```

### Step 3.2.4: Topic Model
```python
# backend/app/db/models/topic.py
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class TopicModel(Base):
    """SQLAlchemy Topic model"""
    
    __tablename__ = "topics"
    
    # Foreign keys
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Content
    topic_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_study_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    exam: Mapped["ExamModel"] = relationship("ExamModel", back_populates="topics")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="topics")
    
    review_items: Mapped[list["ReviewItemModel"]] = relationship(
        "ReviewItemModel",
        back_populates="topic",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TopicModel(id={self.id}, topic_name={self.topic_name})>"
```

### Step 3.2.5: ReviewItem Model
```python
# backend/app/db/models/review.py
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from datetime import datetime
import uuid
from app.db.base import Base


class ReviewItemModel(Base):
    """SQLAlchemy ReviewItem model for spaced repetition"""
    
    __tablename__ = "review_items"
    
    # Foreign keys
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Question/Answer
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # FSRS algorithm parameters
    stability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    
    # Review history
    next_review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True  # Index for efficient "due today" queries
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_review_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    topic: Mapped["TopicModel"] = relationship("TopicModel", back_populates="review_items")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="review_items")
    
    def __repr__(self) -> str:
        return f"<ReviewItemModel(id={self.id}, next_review={self.next_review_date})>"
```

### Step 3.2.6: StudySession Model
```python
# backend/app/db/models/study_session.py
from sqlalchemy import Integer, Boolean, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from datetime import datetime
import uuid
from app.db.base import Base


class StudySessionModel(Base):
    """SQLAlchemy StudySession model"""
    
    __tablename__ = "study_sessions"
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Session info
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Pomodoro
    pomodoro_duration_minutes: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    pomodoros_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Topics studied (array of UUIDs)
    topic_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False
    )
    
    # Statistics
    items_reviewed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="study_sessions")
    exam: Mapped["ExamModel"] = relationship("ExamModel", back_populates="study_sessions")
    
    def __repr__(self) -> str:
        return f"<StudySessionModel(id={self.id}, started_at={self.started_at})>"
```

### Step 3.2.7: Subscription Model
```python
# backend/app/db/models/subscription.py
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from datetime import datetime
import uuid
from app.db.base import Base


class SubscriptionModel(Base):
    """SQLAlchemy Subscription model"""
    
    __tablename__ = "subscriptions"
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Plan info
    plan_type: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    # Billing cycle
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # External billing (Stripe)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Cancel info
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="subscriptions")
    
    def __repr__(self) -> str:
        return f"<SubscriptionModel(id={self.id}, plan={self.plan_type}, status={self.status})>"
```

---

## 3.3 Database Connection & Session

### Step 3.3.1: Database Configuration
```python
# backend/app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL in debug mode
    future=True,
    pool_pre_ping=True,  # Check connection before using
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    Usage in FastAPI endpoints:
    
    @app.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create all tables)"""
    from app.db.base import Base
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections"""
    await engine.dispose()
```

---

## 3.4 Mappers (Domain ↔ DB Models)

### Step 3.4.1: User Mapper
```python
# backend/app/db/mappers/user_mapper.py
from app.domain.user import User
from app.db.models.user import UserModel


class UserMapper:
    """Maps between User domain entity and UserModel DB model"""
    
    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Convert DB model to domain entity"""
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            role=model.role,
            subscription_plan=model.subscription_plan,
            is_verified=model.is_verified,
            verification_token=model.verification_token,
            created_at=model.created_at,
            last_login=model.last_login,
            preferred_language=model.preferred_language,
            timezone=model.timezone,
            daily_study_goal_minutes=model.daily_study_goal_minutes,
        )
    
    @staticmethod
    def to_model(domain: User) -> UserModel:
        """Convert domain entity to DB model"""
        return UserModel(
            id=domain.id,
            email=domain.email,
            password_hash=domain.password_hash,
            full_name=domain.full_name,
            role=domain.role,
            subscription_plan=domain.subscription_plan,
            is_verified=domain.is_verified,
            verification_token=domain.verification_token,
            created_at=domain.created_at,
            last_login=domain.last_login,
            preferred_language=domain.preferred_language,
            timezone=domain.timezone,
            daily_study_goal_minutes=domain.daily_study_goal_minutes,
        )
    
    @staticmethod
    def update_model(model: UserModel, domain: User) -> UserModel:
        """Update existing DB model with domain data"""
        model.email = domain.email
        model.password_hash = domain.password_hash
        model.full_name = domain.full_name
        model.role = domain.role
        model.subscription_plan = domain.subscription_plan
        model.is_verified = domain.is_verified
        model.verification_token = domain.verification_token
        model.last_login = domain.last_login
        model.preferred_language = domain.preferred_language
        model.timezone = domain.timezone
        model.daily_study_goal_minutes = domain.daily_study_goal_minutes
        
        return model
```

### Step 3.4.2: Exam Mapper
```python
# backend/app/db/mappers/exam_mapper.py
from app.domain.exam import Exam
from app.db.models.exam import ExamModel


class ExamMapper:
    """Maps between Exam domain entity and ExamModel DB model"""
    
    @staticmethod
    def to_domain(model: ExamModel) -> Exam:
        """Convert DB model to domain entity"""
        return Exam(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            subject=model.subject,
            exam_type=model.exam_type,
            level=model.level,
            original_content=model.original_content,
            ai_summary=model.ai_summary,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            token_count_input=model.token_count_input,
            token_count_output=model.token_count_output,
            generation_cost_usd=model.generation_cost_usd,
            topic_count=model.topic_count,
        )
    
    @staticmethod
    def to_model(domain: Exam) -> ExamModel:
        """Convert domain entity to DB model"""
        return ExamModel(
            id=domain.id,
            user_id=domain.user_id,
            title=domain.title,
            subject=domain.subject,
            exam_type=domain.exam_type,
            level=domain.level,
            original_content=domain.original_content,
            ai_summary=domain.ai_summary,
            status=domain.status,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
            token_count_input=domain.token_count_input,
            token_count_output=domain.token_count_output,
            generation_cost_usd=domain.generation_cost_usd,
            topic_count=domain.topic_count,
        )
```

---

## 3.5 Repository Pattern

### Step 3.5.1: Base Repository
```python
# backend/app/repositories/base.py
from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from uuid import UUID


T = TypeVar('T')  # Domain entity type
M = TypeVar('M')  # DB model type


class BaseRepository(Generic[T, M]):
    """
    Base repository with common CRUD operations.
    Subclass this for specific entity repositories.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        model_class: Type[M],
        mapper
    ):
        self.session = session
        self.model_class = model_class
        self.mapper = mapper
    
    async def create(self, entity: T) -> T:
        """Create new entity"""
        try:
            model = self.mapper.to_model(entity)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            
            return self.mapper.to_domain(model)
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID"""
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_domain(model)
    
    async def update(self, entity: T) -> T:
        """Update existing entity"""
        stmt = select(self.model_class).where(self.model_class.id == entity.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            raise ValueError(f"Entity with id {entity.id} not found")
        
        model = self.mapper.update_model(model, entity)
        await self.session.flush()
        await self.session.refresh(model)
        
        return self.mapper.to_domain(model)
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID"""
        stmt = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount > 0
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List all entities with pagination"""
        stmt = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def count(self) -> int:
        """Count total entities"""
        stmt = select(func.count()).select_from(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalar_one()
```

### Step 3.5.2: User Repository
```python
# backend/app/repositories/user_repository.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.user import User
from app.db.models.user import UserModel
from app.db.mappers.user_mapper import UserMapper
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserModel]):
    """Repository for User entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, UserMapper)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_domain(model)
    
    async def get_by_verification_token(self, token: str) -> Optional[User]:
        """Get user by verification token"""
        stmt = select(UserModel).where(UserModel.verification_token == token)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_domain(model)
    
    async def exists_by_email(self, email: str) -> bool:
        """Check if user with email exists"""
        stmt = select(UserModel.id).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
```

### Step 3.5.3: Exam Repository
```python
# backend/app/repositories/exam_repository.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.exam import Exam, ExamStatus
from app.db.models.exam import ExamModel
from app.db.mappers.exam_mapper import ExamMapper
from app.repositories.base import BaseRepository


class ExamRepository(BaseRepository[Exam, ExamModel]):
    """Repository for Exam entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExamModel, ExamMapper)
    
    async def list_by_user(
        self,
        user_id: UUID,
        status: Optional[ExamStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Exam]:
        """List exams by user with optional status filter"""
        stmt = select(ExamModel).where(ExamModel.user_id == user_id)
        
        if status:
            stmt = stmt.where(ExamModel.status == status)
        
        stmt = stmt.order_by(ExamModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def count_by_user(self, user_id: UUID, status: Optional[ExamStatus] = None) -> int:
        """Count user's exams"""
        stmt = select(func.count()).select_from(ExamModel).where(ExamModel.user_id == user_id)
        
        if status:
            stmt = stmt.where(ExamModel.status == status)
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def get_by_user_and_id(self, user_id: UUID, exam_id: UUID) -> Optional[Exam]:
        """Get exam by user and ID (for authorization)"""
        stmt = select(ExamModel).where(
            ExamModel.id == exam_id,
            ExamModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model is None:
            return None
        
        return self.mapper.to_domain(model)
```

### Step 3.5.4: ReviewItem Repository
```python
# backend/app/repositories/review_repository.py
from typing import List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.review import ReviewItem
from app.db.models.review import ReviewItemModel
from app.db.mappers.review_mapper import ReviewItemMapper
from app.repositories.base import BaseRepository


class ReviewItemRepository(BaseRepository[ReviewItem, ReviewItemModel]):
    """Repository for ReviewItem entity"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewItemModel, ReviewItemMapper)
    
    async def list_due_by_user(
        self,
        user_id: UUID,
        limit: int = 100
    ) -> List[ReviewItem]:
        """Get review items due for review"""
        now = datetime.utcnow()
        
        stmt = select(ReviewItemModel).where(
            ReviewItemModel.user_id == user_id,
            ReviewItemModel.next_review_date <= now
        ).order_by(
            ReviewItemModel.next_review_date.asc()
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def list_by_topic(self, topic_id: UUID) -> List[ReviewItem]:
        """Get all review items for a topic"""
        stmt = select(ReviewItemModel).where(
            ReviewItemModel.topic_id == topic_id
        ).order_by(ReviewItemModel.created_at.asc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self.mapper.to_domain(model) for model in models]
    
    async def count_due_by_user(self, user_id: UUID) -> int:
        """Count items due for review"""
        now = datetime.utcnow()
        
        stmt = select(func.count()).select_from(ReviewItemModel).where(
            ReviewItemModel.user_id == user_id,
            ReviewItemModel.next_review_date <= now
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
```

---

## 3.6 Alembic Migrations

### Step 3.6.1: Alembic Setup
```ini
# backend/alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql+asyncpg://localhost/examai

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Step 3.6.2: Alembic Env
```python
# backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio

from app.core.config import settings
from app.db.base import Base

# Import all models to ensure they're registered
from app.db.models.user import UserModel
from app.db.models.exam import ExamModel
from app.db.models.topic import TopicModel
from app.db.models.review import ReviewItemModel
from app.db.models.study_session import StudySessionModel
from app.db.models.subscription import SubscriptionModel


config = context.config

# Override sqlalchemy.url with actual DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### Step 3.6.3: Create Initial Migration
```bash
# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## 3.7 Integration Tests

### Step 3.7.1: Test Database Setup
```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.core.config import settings


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    # Use separate test database
    test_db_url = settings.DATABASE_URL.replace("/examai", "/examai_test")
    
    engine = create_async_engine(test_db_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session"""
    TestSessionLocal = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
```

### Step 3.7.2: Test User Repository
```python
# backend/tests/integration/repositories/test_user_repository.py
import pytest
from app.domain.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestUserRepository:
    """Integration tests for UserRepository"""
    
    async def test_create_user(self, test_session):
        """Test creating user"""
        repo = UserRepository(test_session)
        
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed"
        )
        
        created = await repo.create(user)
        
        assert created.id is not None
        assert created.email == "test@example.com"
    
    async def test_get_by_email(self, test_session):
        """Test getting user by email"""
        repo = UserRepository(test_session)
        
        user = User(email="test@example.com", full_name="Test", password_hash="hashed")
        await repo.create(user)
        
        found = await repo.get_by_email("test@example.com")
        
        assert found is not None
        assert found.email == "test@example.com"
    
    async def test_update_user(self, test_session):
        """Test updating user"""
        repo = UserRepository(test_session)
        
        user = User(email="test@example.com", full_name="Old Name", password_hash="hashed")
        created = await repo.create(user)
        
        created.full_name = "New Name"
        updated = await repo.update(created)
        
        assert updated.full_name == "New Name"
    
    async def test_delete_user(self, test_session):
        """Test deleting user"""
        repo = UserRepository(test_session)
        
        user = User(email="test@example.com", full_name="Test", password_hash="hashed")
        created = await repo.create(user)
        
        deleted = await repo.delete(created.id)
        
        assert deleted is True
        
        found = await repo.get_by_id(created.id)
        assert found is None
```

---

## 3.8 Best Practices & Next Steps

### Code Quality
- **Async/await everywhere**: All DB operations are async
- **Type safety**: Full type hints on all methods
- **Mappers**: Clean separation between domain and persistence
- **Repository pattern**: Easy to mock for testing

### Testing
- Integration tests with real database
- Test all repository methods
- Use transactions for test isolation

### Next Steps
1. Run migrations: `alembic upgrade head`
2. Run integration tests: `pytest tests/integration/`
3. Verify database schema in Supabase
4. Proceed to **Stage 4: Service Layer**
