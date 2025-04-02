# reset_password.py
import asyncio
import getpass
import sys
from contextlib import asynccontextmanager

from beaverhabits.app.db import get_async_session, get_user_db
from beaverhabits.app.users import get_user_manager
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
                    
                    # Update password
                    # FastAPI Users UserManager expects a Pydantic model for updates
                    # We need to hash the password before updating
                    hashed_password = user_manager.password_helper.hash(new_password)
                    user_update = {"hashed_password": hashed_password} 
                    
                    # The update method in UserManager takes the update dict and the user object
                    await user_manager.update(user_update, user, safe=True) # Use safe=True to avoid updating other fields
                    
                    # Commit the session to save changes
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
