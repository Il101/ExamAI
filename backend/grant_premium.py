"""
Script to grant premium status to all existing user accounts.
This updates both the user.subscription_plan field and creates/updates subscription records.
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.user import UserModel
from app.db.models.subscription import SubscriptionModel
from app.db.session import AsyncSessionLocal



async def grant_premium_to_all_users():
    """Grant premium status to all existing users."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Get all users
            result = await session.execute(select(UserModel))
            users = result.scalars().all()
            
            if not users:
                print("No users found in database.")
                return
            
            print(f"Found {len(users)} users. Granting premium status...")
            
            # Step 2: Update all users to premium plan
            await session.execute(
                update(UserModel)
                .values(subscription_plan="premium")
            )
            
            # Step 3: Create or update subscription records for each user
            current_time = datetime.now(timezone.utc)
            period_end = current_time + timedelta(days=365)  # 1 year premium
            
            for user in users:
                # Check if user already has a subscription
                sub_result = await session.execute(
                    select(SubscriptionModel).where(
                        SubscriptionModel.user_id == user.id
                    )
                )
                existing_sub = sub_result.scalars().first()
                
                if existing_sub:
                    # Update existing subscription
                    existing_sub.plan_type = "premium"
                    existing_sub.status = "active"
                    existing_sub.current_period_start = current_time
                    existing_sub.current_period_end = period_end
                    existing_sub.cancel_at_period_end = False
                    existing_sub.canceled_at = None
                    print(f"  ✓ Updated subscription for {user.email}")
                else:
                    # Create new subscription
                    new_sub = SubscriptionModel(
                        user_id=user.id,
                        plan_type="premium",
                        status="active",
                        current_period_start=current_time,
                        current_period_end=period_end,
                        cancel_at_period_end=False
                    )
                    session.add(new_sub)
                    print(f"  ✓ Created premium subscription for {user.email}")
            
            # Commit all changes
            await session.commit()
            
            print(f"\n✅ Successfully granted premium status to {len(users)} users!")
            print(f"Premium period: {current_time.date()} to {period_end.date()}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error granting premium status: {e}")
            raise


async def verify_premium_status():
    """Verify that all users have premium status."""
    
    async with AsyncSessionLocal() as session:
        # Count users by subscription plan
        result = await session.execute(select(UserModel))
        users = result.scalars().all()
        
        plan_counts = {}
        for user in users:
            plan = user.subscription_plan
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
        
        print("\n📊 User Subscription Status:")
        for plan, count in sorted(plan_counts.items()):
            print(f"  {plan}: {count} users")
        
        # Check subscriptions table
        sub_result = await session.execute(select(SubscriptionModel))
        subscriptions = sub_result.scalars().all()
        
        active_premium = sum(1 for sub in subscriptions if sub.plan_type == "premium" and sub.status == "active")
        print(f"\n📊 Active Premium Subscriptions: {active_premium}")


async def main():
    """Main function."""
    print("=" * 60)
    print("Grant Premium Status to All Users")
    print("=" * 60)
    
    # Show current status
    print("\nCurrent status:")
    await verify_premium_status()
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input("\nDo you want to grant premium status to ALL users? (yes/no): ")
    
    if response.lower() != "yes":
        print("Operation cancelled.")
        return
    
    # Grant premium
    await grant_premium_to_all_users()
    
    # Verify
    print("\nVerifying changes:")
    await verify_premium_status()
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
