# reset_password.py
import asyncio
import getpass
import sys
from contextlib import asynccontextmanager

from beaverhabits.app.db import get_async_session, get_user_db
from beaverhabits.app.users import get_user_manager
from beaverhabits.app.schemas import UserUpdate  # Import UserUpdate schema
from beaverhabits.logging import logger

get_async_session_context = asynccontextmanager(get_async_session)
get_user_db_context = asynccontextmanager(get_user_db)
get_user_manager_context = asynccontextmanager(get_user_manager)

async def reset_password(email: str, new_password: str):
    try:
        logger.info(f"Starting password reset for email: {email}")
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    # Get user by email
                    user = await user_manager.get_by_email(email)
                    if not user:
                        print(f"User with email {email} not found")
                        return False
                    # Create UserUpdate schema instance with the new password
                    user_update_schema = UserUpdate(password=new_password)
                    
                    # The update method in UserManager takes the UserUpdate schema and the user object
                    await user_manager.update(user_update_schema, user, safe=True) # Use safe=True to avoid updating other fields
                    
                    # Commit the session to save changes (UserManager might handle this, but explicit commit is safer)
                    await session.commit()
                    
                    print(f"Password successfully reset for {email}")
                    return True
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        logger.exception(f"Password reset failed for {email}")
        return False

def main():
    print("BeaverHabits Password Reset Tool")
    print("===============================")
    
    # Get email
    email = input("Enter your email: ")
    if not email:
        print("Email is required")
        sys.exit(1)
    
    # Get new password
    new_password = getpass.getpass("Enter new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    
    if new_password != confirm_password:
        print("Passwords do not match")
        sys.exit(1)
    
    # Basic password length check (FastAPI Users might have more complex rules)
    if len(new_password) < 8: 
        print("Password must be at least 8 characters long")
        sys.exit(1)
    
    # Run the password reset
    success = asyncio.run(reset_password(email, new_password))
    
    if success:
        print("Password reset successful. You can now log in with your new password.")
    else:
        print("Password reset failed.")

if __name__ == "__main__":
    main()
