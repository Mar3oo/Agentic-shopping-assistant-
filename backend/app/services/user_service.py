from Data_Base.user_repo import create_guest_user


def create_guest_user_response() -> dict:
    user = create_guest_user()
    return {
        "status": "success",
        "message": "Guest user created",
        "data": {
            "user_id": user["user_id"],
            "mode": user["mode"],
        },
    }
