from typing import cast
from app.domain.user import User, UserRole, SubscriptionPlan
from app.db.models.user import UserModel


class UserMapper:
    """Maps between User domain entity and UserModel DB model"""
    
    @staticmethod
    def to_domain(model: UserModel) -> User:
        """Convert DB model to domain entity"""
        return User(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            role=cast(UserRole, model.role),
            subscription_plan=cast(SubscriptionPlan, model.subscription_plan),
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
