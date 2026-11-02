from getpass import getpass
from werkzeug.security import generate_password_hash
password=getpass('Choose a NEW  password (do not reuse a password shared in chat): ')
if len(password)<12: raise SystemExit('Use at least 12 characters.')
print('\nAdd this to your .env as ADMIN_PASSWORD_HASH=\n')
print(generate_password_hash(password))
