from sanic import Blueprint
from qanything_kernel.qanything_server import dept, group, kb

# 创建蓝图
admin_bp = Blueprint('admin', url_prefix='/api/admin')
user_bp = Blueprint('user', url_prefix='/api/user')

# 注册部门管理路由
admin_bp.add_route(dept.create_department, '/department/create', methods=['POST'])
admin_bp.add_route(dept.list_departments, '/department/list', methods=['GET'])
admin_bp.add_route(dept.update_department, '/department/update', methods=['POST'])
admin_bp.add_route(dept.delete_department, '/department/delete', methods=['POST'])

# 注册用户组管理路由
admin_bp.add_route(group.create_group, '/group/create', methods=['POST'])
admin_bp.add_route(group.list_groups, '/group/list', methods=['GET'])
admin_bp.add_route(group.update_group, '/group/update', methods=['POST'])
admin_bp.add_route(group.delete_group, '/group/delete', methods=['POST'])
admin_bp.add_route(group.add_user_to_group, '/group/add_user', methods=['POST'])
admin_bp.add_route(group.remove_user_from_group, '/group/remove_user', methods=['POST'])
admin_bp.add_route(group.list_group_members, '/group/members', methods=['GET'])

# 注册知识库权限管理路由
admin_bp.add_route(kb.grant_kb_access, '/kb/grant_access', methods=['POST'])
admin_bp.add_route(kb.revoke_kb_access, '/kb/revoke_access', methods=['POST'])
admin_bp.add_route(kb.list_kb_access, '/kb/access_list', methods=['GET'])
admin_bp.add_route(kb.list_subject_access, '/kb/subject_access', methods=['GET'])
# 添加批量设置知识库权限的路由
admin_bp.add_route(kb.batch_grant_kb_access, '/kb/batch_grant_access', methods=['POST'])
admin_bp.add_route(kb.batch_revoke_kb_access, '/kb/batch_revoke_access', methods=['POST'])
admin_bp.add_route(kb.batch_set_kb_access, '/kb/batch_set_access', methods=['POST'])

# 注册用户权限检查路由
user_bp.add_route(kb.check_kb_access, '/kb/check_access', methods=['GET'])
user_bp.add_route(kb.list_accessible_kbs, '/kb/accessible_list', methods=['GET'])

def register_routes(app):
    """注册所有路由到应用"""
    app.blueprint(admin_bp)
    app.blueprint(user_bp)