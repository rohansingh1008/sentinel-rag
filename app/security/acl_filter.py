from qdrant_client.models import Filter, FieldCondition, MatchAny

ROLE_PERMISSIONS = {
    "guest": ["public"],
    "employee": ["public", "internal"],
    "admin": ["public", "internal", "confidential"],
}

def build_acl_filter(user_role: str) -> Filter:
    allowed_levels = ROLE_PERMISSIONS.get(user_role, ["public"])
    return Filter(
        must=[
            FieldCondition(
                key="access_level",
                match=MatchAny(any=allowed_levels)
            )
        ]
    )