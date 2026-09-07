from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


password = "test_password_123"

hashed = hash_password(password)

print("Password hashed successfully:")
print(hashed)

print(
    "Correct password:",
    verify_password(password, hashed)
)

print(
    "Wrong password:",
    verify_password(
        "wrong_password",
        hashed
    )
)

token = create_access_token(123)

print("\nJWT created successfully.")

decoded_user_id = decode_access_token(token)

print(
    "Decoded user ID:",
    decoded_user_id
)