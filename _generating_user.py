#Example of generating a new user : 

import hashlib
username = "user2"  # replace with desired username
password = "user2"  # replace with desired password
hash = hashlib.sha256(password.encode()).hexdigest()
print(f"Hash for {username}: {hash}")