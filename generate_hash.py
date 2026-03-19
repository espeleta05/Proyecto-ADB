import bcrypt

password = "4567"

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

print(hashed.decode())