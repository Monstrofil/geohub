"""
Create superuser command
"""
import getpass
from cli.base import BaseCommand
from models import User


class CreateSuperUserCommand(BaseCommand):
    """Create a superuser account"""
    
    help = "Create a superuser account with admin privileges"
    
    def add_arguments(self):
        self.parser.add_argument(
            'username',
            nargs='?',
            default='root',
            help='Username for the superuser (default: root)'
        )
        self.parser.add_argument(
            '--email',
            help='Email address for the superuser'
        )
        self.parser.add_argument(
            '--password',
            help='Password for the superuser (will prompt if not provided)'
        )
        self.parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for input, use defaults and provided arguments'
        )
    
    async def handle(self, **options):
        username = options['username']
        email = options.get('email')
        password = options.get('password')
        no_input = options.get('no_input', False)
        
        # Check if user already exists
        existing_user = await User.filter(username=username).first()
        if existing_user:
            if existing_user.is_admin:
                print(f"Superuser '{username}' already exists.")
                return
            else:
                # User exists but is not admin, ask if we should make them admin
                if not no_input:
                    response = input(f"User '{username}' exists but is not a superuser. Make them a superuser? (y/N): ")
                    if response.lower() not in ['y', 'yes']:
                        print("Operation cancelled.")
                        return
                
                existing_user.is_admin = True
                await existing_user.save()
                print(f"User '{username}' has been granted superuser privileges.")
                return
        
        # Get email if not provided
        if not email and not no_input:
            email = input("Email address: ").strip()
            if not email:
                email = f"{username}@example.com"
                print(f"Using default email: {email}")
        elif not email:
            email = f"{username}@example.com"
        
        # Get password if not provided
        if not password and not no_input:
            while True:
                password = getpass.getpass("Password: ")
                if not password:
                    print("Password cannot be empty.")
                    continue
                
                password_confirm = getpass.getpass("Password (again): ")
                if password != password_confirm:
                    print("Passwords don't match. Please try again.")
                    continue
                break
        elif not password:
            # Default password for no-input mode
            password = "admin123"
            print("Using default password: admin123")
        
        # Create the superuser
        try:
            user = User(
                username=username,
                email=email,
                is_admin=True,
                is_active=True
            )
            user.set_password(password)
            await user.save()
            
            print(f"Superuser '{username}' created successfully!")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print("Admin: Yes")
            
        except Exception as e:
            print(f"Error creating superuser: {e}")
            raise


# Export the command
command = CreateSuperUserCommand
