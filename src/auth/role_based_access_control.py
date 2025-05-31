class AccessControl:
    def __init__(self):
        self.roles_permissions = {
            'admin': ['create', 'read', 'update', 'delete'],
            'user': ['read'],
            'guest': []
        }

    def check_permission(self, user_role, action):
        return action in self.roles_permissions.get(user_role, [])