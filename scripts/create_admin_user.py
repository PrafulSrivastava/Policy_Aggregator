"""Script to create an admin user for the Policy Aggregator application."""

import asyncio
import sys
import getpass
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import init_db, async_session_maker, get_database_url
from api.repositories.user_repository import UserRepository
from api.auth.auth import get_password_hash


async def create_admin_user(username: str, password: str) -> None:
    """
    Create an admin user in the database.
    
    Args:
        username: Username for the admin user
        password: Plain text password (will be hashed)
        
    Raises:
        ValueError: If username already exists
        Exception: If database operation fails
    """
    # Initialize database connection
    init_db()
    
    # Import after init_db to ensure async_session_maker is set
    from api.database import async_session_maker
    
    # Create database session
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        
        # Check if user already exists
        existing_user = await user_repo.get_by_username(username)
        if existing_user:
            raise ValueError(f"User with username '{username}' already exists")
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create user
        user_data = {
            "username": username,
            "hashed_password": hashed_password,
            "is_active": True
        }
        
        try:
            user = await user_repo.create(user_data)
            await session.commit()
            print(f"✓ Admin user '{username}' created successfully!")
            print(f"  User ID: {user.id}")
            return user
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to create user: {str(e)}")


def main():
    """Main function to run the script interactively or with command-line arguments."""
    # Parse command-line arguments
    if len(sys.argv) >= 3:
        # Username and password provided as arguments
        username = sys.argv[1]
        password = sys.argv[2]
    elif len(sys.argv) == 2:
        # Only username provided, prompt for password
        username = sys.argv[1]
        password = getpass.getpass("Enter password: ")
    else:
        # Interactive mode: prompt for both
        print("Create Admin User")
        print("=" * 50)
        username = input("Enter username: ").strip()
        if not username:
            print("Error: Username cannot be empty")
            sys.exit(1)
        
        password = getpass.getpass("Enter password: ")
        if not password:
            print("Error: Password cannot be empty")
            sys.exit(1)
        
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match")
            sys.exit(1)
    
    # Validate inputs
    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)
    
    if not password:
        print("Error: Password cannot be empty")
        sys.exit(1)
    
    if len(password) < 8:
        print("Warning: Password is less than 8 characters. Consider using a stronger password.")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            sys.exit(0)
    
    # Create user
    try:
        asyncio.run(create_admin_user(username, password))
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

