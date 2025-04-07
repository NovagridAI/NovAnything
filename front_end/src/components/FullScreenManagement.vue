<template>
    <div class="management-layout">
        <!-- 侧边栏 -->
        <div class="sidebar">
            <div class="sidebar-header">
                <h3>组织管理</h3>
                <p class="sidebar-desc">管理团队成员的组织结构和权限设置</p>
                <arco-button class="add-department-btn" type="outline" long @click="showAddDepartmentModal">
                    <template #icon><icon-plus /></template>
                    创建部门
                </arco-button>
            </div>

            <div class="sidebar-tree">
                <arco-tree blockNode :data="departmentTree" :default-expanded-keys="['product']"
                    :selected-keys="selectedDepartment" @select="handleDepartmentSelect">
                    <template #title="{ title }">
                        <span>{{ title }}</span>
                    </template>
                    <template #extra="nodeData">
                        <arco-popover>
                            <div class=" node-action-trigger" @click="() => console.log(nodeData)">
                                <icon-more-vertical class="node-action-icon" />
                            </div>
                            <template #content>
                                <div class="tree-node-actions no-padding">
                                    <arco-button class="action-button danger" type="text" size="small" status="danger"
                                        @click.stop="handleDeleteDepartment(nodeData)">
                                        <template #icon><icon-delete /></template>
                                        删除部门
                                    </arco-button>
                                </div>
                            </template>
                        </arco-popover>
                    </template>
                </arco-tree>
            </div>
        </div>

        <!-- 用户管理内容区 -->
        <div class="user-management-container">
            <div class="header">
                <arco-input v-model="searchKeyword" placeholder="搜索成员" allow-clear class="search-input" />
                <div class="action-buttons">
                    <arco-button type="primary" @click="showAddUserModal">
                        <template #icon><icon-plus /></template>
                        添加用户
                    </arco-button>
                    <arco-button type="outline" @click="handleBatchMove">
                        <template #icon><icon-swap /></template>
                        批量移动
                    </arco-button>
                </div>
            </div>

            <arco-table ref="tableRef" :data="filteredUserList" :columns="columns" :pagination="false"
                @page-change="onPageChange" row-key="id" :row-selection="{
                    type: 'checkbox',
                    showCheckedAll: true
                }" v-model:selectedKeys="selectedKeys" :loading="loadingUsers">
                <template #columns>
                    <arco-table-column title="用户名" data-index="username" />
                    <arco-table-column title="角色" data-index="role" />
                    <arco-table-column title="创建时间" data-index="createTime" />
                    <arco-table-column title="操作">
                        <template #cell="{ record }">
                            <arco-space>
                                <!-- <arco-button type="text" size="small" @click="handleEdit(record)">编辑</arco-button> -->
                                <arco-link type="text" size="small" @click="handleMove(record)">移动</arco-link>
                                <arco-link type="text" size="small" @click="handleChangePassword(record)">修改密码</arco-link>

                                <!-- 使用 Popover 替换直接删除按钮 -->
                                <arco-popover position="top" trigger="click">
                                    <arco-button type="text" status="danger" size="small">删除</arco-button>
                                    <template #content>
                                        <div style="padding: 4px 8px;">
                                            <p style="margin-bottom: 8px;">确定要删除用户吗？</p>
                                            <div style="display: flex; justify-content: flex-end;">
                                                <arco-space>
                                                    <arco-button size="mini" type="primary" status="danger"
                                                        @click="confirmDelete(record)">
                                                        确定删除
                                                    </arco-button>
                                                </arco-space>
                                            </div>
                                        </div>
                                    </template>
                                </arco-popover>
                            </arco-space>
                        </template>
                    </arco-table-column>
                </template>
            </arco-table>

            <!-- 添加用户弹窗 -->
            <arco-modal v-model:visible="addUserModalVisible" title="添加用户" @ok="confirmAddUser" @cancel="cancelAddUser">
                <arco-form :model="userForm" layout="vertical">
                    <arco-form-item field="username" label="用户名">
                        <arco-input v-model="userForm.username" placeholder="请输入用户名" />
                    </arco-form-item>
                    <arco-form-item field="password" label="密码">
                        <arco-input-password v-model="userForm.password" placeholder="请输入密码" />
                    </arco-form-item>
                    <arco-form-item field="role" label="角色">
                        <arco-select v-model="userForm.role" placeholder="请选择角色">
                            <!-- <arco-option value="superadmin">超级管理员</arco-option> -->
                            <arco-option value="admin">管理员</arco-option>
                            <arco-option value="user">普通用户</arco-option>
                        </arco-select>
                    </arco-form-item>
                    <arco-form-item field="deptId" label="所属部门">
                        <arco-select v-model="userForm.deptId" placeholder="请选择部门">
                            <arco-option v-for="dept in flatDepartments" :key="dept.key" :value="dept.key"
                                :label="dept.title">
                                {{ dept.displayTitle }}
                            </arco-option>
                        </arco-select>
                    </arco-form-item>
                </arco-form>
            </arco-modal>

            <!-- 移动用户弹窗 -->
            <arco-modal v-model:visible="moveUserModalVisible" title="移动用户" @ok="confirmMoveUser"
                @cancel="cancelMoveUser">
                <p>请选择移动到的部门</p>
                <arco-select v-model="moveTargetDeptId" placeholder="请选择目标部门" style="width: 100%">
                    <arco-option v-for="dept in flatDepartments" :key="dept.key" :value="dept.key" :label="dept.title">
                        {{ dept.displayTitle }}
                    </arco-option>
                </arco-select>
            </arco-modal>
        </div>

        <!-- 添加部门弹窗 -->
        <arco-modal v-model:visible="addDepartmentModalVisible" title="创建部门" @ok="confirmAddDepartment"
            @cancel="cancelAddDepartment">
            <arco-form :model="departmentForm" layout="vertical">
                <arco-form-item field="name" label="部门名称">
                    <arco-input v-model="departmentForm.name" placeholder="请输入部门名称" />
                </arco-form-item>
                <arco-form-item field="parentId" label="上级部门">
                    <arco-select v-model="departmentForm.parentId" placeholder="请选择上级部门(可选)" allow-clear>
                        <arco-option v-for="dept in flatDepartments" :key="dept.key" :value="dept.key"
                            :label="dept.title">
                            {{ dept.displayTitle }}
                        </arco-option>
                    </arco-select>
                </arco-form-item>
            </arco-form>
        </arco-modal>

        <!-- 删除部门确认弹窗 -->
        <arco-modal 
            v-model:visible="deleteDeptModalVisible" 
            title="删除部门" 
            @cancel="deleteDeptModalVisible = false"
            @ok="confirmDeleteDepartment"
            ok-text="确认删除"
        >
            <p>确定要删除部门 "{{ deptToDelete?.title }}" 吗？</p>
            <p style="color: var(--color-text-3);">此操作不可撤销，请谨慎操作。</p>
        </arco-modal>

        <!-- 修改密码弹窗 -->
        <arco-modal v-model:visible="changePasswordModalVisible" title="修改密码" @ok="confirmChangePassword" @cancel="cancelChangePassword">
            <arco-form :model="passwordForm" layout="vertical">
                <arco-form-item field="oldPassword" label="当前密码">
                    <arco-input-password v-model="passwordForm.oldPassword" placeholder="请输入当前密码" />
                </arco-form-item>
                <arco-form-item field="newPassword" label="新密码">
                    <arco-input-password v-model="passwordForm.newPassword" placeholder="请输入新密码" />
                </arco-form-item>
                <arco-form-item field="confirmPassword" label="确认密码">
                    <arco-input-password v-model="passwordForm.confirmPassword" placeholder="请再次输入新密码" />
                </arco-form-item>
            </arco-form>
        </arco-modal>
    </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue';
import { IconPlus, IconSwap, IconDelete, IconMoreVertical, IconUser } from '@arco-design/web-vue/es/icon';
import urlResquest from '@/services/urlConfig'
import { Message, Modal } from '@arco-design/web-vue';

// 部门树数据
const departmentTree = ref([]);

// 当前选中的部门
const selectedDepartment = ref([]);

// 获取部门列表数据
const fetchDepartmentList = async () => {
    try {
        const res = await urlResquest.departmentList();
        if (res && res.data) {
            // 将平面数据转换为树形结构
            departmentTree.value = buildDepartmentTree(res.data);

            // 如果有数据，默认选中第一个部门
            if (departmentTree.value.length > 0) {
                const firstDept = departmentTree.value[0];
                selectedDepartment.value = [firstDept.key];
            }
        }
    } catch (error) {
        console.error('获取部门列表失败:', error);
    }
};

// 将平面部门数据转换为树形结构
const buildDepartmentTree = (departments) => {
    // 创建一个映射表，用于快速查找部门
    const deptMap = {};
    departments.forEach(dept => {
        deptMap[dept.dept_id] = {
            key: dept.dept_id,
            title: dept.dept_name,
            children: [],
            // 保存原始数据，以便需要时使用
            raw: { ...dept }
        };
    });

    // 构建树形结构
    const result = [];
    departments.forEach(dept => {
        const deptNode = deptMap[dept.dept_id];

        if (dept.parent_dept_id) {
            // 如果有父部门，将当前部门添加到父部门的children中
            const parentNode = deptMap[dept.parent_dept_id];
            if (parentNode) {
                parentNode.children.push(deptNode);
            } else {
                // 如果找不到父部门，将当前部门添加到顶层
                result.push(deptNode);
            }
        } else {
            // 如果没有父部门，将当前部门添加到顶层
            result.push(deptNode);
        }
    });

    // 移除空的children数组
    const cleanupEmptyChildren = (nodes) => {
        nodes.forEach(node => {
            if (node.children.length === 0) {
                delete node.children;
            } else {
                cleanupEmptyChildren(node.children);
            }
        });
    };

    cleanupEmptyChildren(result);
    return result;
};

// 组件挂载时获取部门数据
onMounted(() => {
    fetchDepartmentList();
});

// 处理部门选择
const handleDepartmentSelect = (selectedKeys) => {
    selectedDepartment.value = selectedKeys;
};

// 用户列表数据
const userList = ref([]);

// 角色映射
const roleMap = {
    'superadmin': '超级管理员',
    'admin': '管理员',
    'user': '普通用户'
};

// 加载用户列表
const loadingUsers = ref(false);

// 获取部门用户
const fetchDepartmentUsers = async (deptId) => {
    if (!deptId) return;

    loadingUsers.value = true;
    try {
        const res = await urlResquest.departmentUsers({ dept_id: deptId });
        if (res && res.code === 200) {
            // 将API返回的用户数据转换为表格需要的格式
            userList.value = (res.data.users || []).map(user => ({
                id: user.user_id,
                username: user.username,
                role: roleMap[user.role] || '普通用户', // 使用角色映射转换为中文
                createTime: user.create_time || new Date().toLocaleString(),
                // 保存原始数据，以便需要时使用
                raw: { ...user }
            }));
        } else {
            Message.error(res?.msg || '获取部门用户失败');
            userList.value = [];
        }
    } catch (error) {
        console.error('获取部门用户失败:', error);
        Message.error('获取部门用户失败，请稍后重试');
        userList.value = [];
    } finally {
        loadingUsers.value = false;
    }
};

// 监听选中部门变化，加载对应的用户列表
watch(selectedDepartment, (newVal) => {
    if (newVal && newVal.length > 0) {
        fetchDepartmentUsers(newVal[0]);
    } else {
        userList.value = [];
    }
});

// 搜索关键词
const searchKeyword = ref('');

// 过滤后的用户列表
const filteredUserList = computed(() => {
    if (!searchKeyword.value) return userList.value;
    return userList.value.filter(user =>
        user.username.includes(searchKeyword.value) ||
        user.role.includes(searchKeyword.value)
    );
});

// 分页配置
const pagination = reactive({
    total: 200,
    current: 1,
    pageSize: 10,
    showTotal: true,
    showJumper: true,
    showPageSize: true,
});

// 存储选中的行键值
const selectedKeys = ref([]);

// 表格列配置
const columns = [
    {
        title: '用户名',
        dataIndex: 'username',
    },
    {
        title: '角色',
        dataIndex: 'role',
    },
    {
        title: '创建时间',
        dataIndex: 'createTime',
    },
    {
        title: '操作',
        dataIndex: 'operations',
        width: 200,
    }
];

// 添加用户相关
const addUserModalVisible = ref(false);
const userForm = reactive({
    username: '',
    password: '',
    role: 'user',
    deptId: '',
    userId: null
});

// 显示添加用户弹窗
const showAddUserModal = () => {
    userForm.username = '';
    userForm.password = '';
    userForm.role = 'user';

    if (selectedDepartment.value && selectedDepartment.value.length > 0) {
        userForm.deptId = selectedDepartment.value[0];
    } else {
        userForm.deptId = '';
    }

    userForm.userId = null;
    addUserModalVisible.value = true;
};

// 确认添加用户
const confirmAddUser = async () => {
    if (!userForm.username || !userForm.password) {
        Message.error('用户名和密码不能为空');
        return;
    }

    if (!userForm.deptId) {
        Message.error('请选择部门');
        return;
    }

    try {
        const loadingMessage = Message.loading({
            content: '正在创建用户...',
            duration: 0
        });

        const res = await urlResquest.createUser({
            username: userForm.username,
            password: userForm.password,
            role: userForm.role || 'user',
            dept_id: userForm.deptId
        });

        loadingMessage.close();

        if (res && res.code === 200) {
            Message.success('用户创建成功');

            userForm.username = '';
            userForm.password = '';
            userForm.role = 'user';
            userForm.deptId = '';
            addUserModalVisible.value = false;

            fetchDepartmentUsers(selectedDepartment.value[0]);
        } else {
            Message.error(res?.msg || '创建用户失败');
        }
    } catch (error) {
        console.error('创建用户失败:', error);
        Message.error('创建用户失败，请稍后重试');
    }
};

// 取消添加用户
const cancelAddUser = () => {
    userForm.username = '';
    userForm.password = '';
    userForm.role = 'user';
    userForm.deptId = '';
    userForm.userId = null;
    addUserModalVisible.value = false;
};

// 编辑用户
const handleEdit = (record) => {
    userForm.username = record.username;
    userForm.role = record.role;
    userForm.password = '';
    userForm.userId = record.id;

    if (selectedDepartment.value && selectedDepartment.value.length > 0) {
        userForm.deptId = selectedDepartment.value[0];
    } else {
        userForm.deptId = '';
    }

    addUserModalVisible.value = true;
};

// 移动用户相关
const moveUserModalVisible = ref(false);
const moveTargetDeptId = ref('');
const usersToMove = ref([]);

// 移动单个用户
const handleMove = (record) => {
    moveTargetDeptId.value = '';
    usersToMove.value = [record.id];
    moveUserModalVisible.value = true;
};

// 添加表格引用
const tableRef = ref(null);

// 批量移动用户
const handleBatchMove = () => {
    if (selectedKeys.value.length === 0) {
        Message.warning('请先选择要移动的用户');
        return;
    }

    moveTargetDeptId.value = '';
    usersToMove.value = selectedKeys.value;
    moveUserModalVisible.value = true;
};

// 确认移动用户
const confirmMoveUser = async () => {
    if (!moveTargetDeptId.value) {
        Message.error('请选择目标部门');
        return;
    }

    try {
        const loadingMessage = Message.loading({
            content: '正在移动用户...',
            duration: 0
        });

        // 使用现有的 addUserToGroup API
        const res = await urlResquest.addUserToDepartment({
            user_id: moveTargetDeptId.value,  // 目标部门ID作为user_id
            target_user_ids: usersToMove.value, // 要移动的用户ID数组
            dept_id: moveTargetDeptId.value  // 如果不需要group_id，传空字符串
        });

        loadingMessage.close();

        if (res && res.code === 200) {
            Message.success('用户移动成功');
            moveUserModalVisible.value = false;

            // 如果当前选中的部门是目标部门，刷新用户列表
            if (selectedDepartment.value[0] === moveTargetDeptId.value) {
                fetchDepartmentUsers(selectedDepartment.value[0]);
            } else {
                // 否则从当前列表中移除这些用户
                userList.value = userList.value.filter(user => !usersToMove.value.includes(user.id));
            }

            // 清空选中项
            selectedKeys.value = [];
        } else {
            Message.error(res?.msg || '用户移动失败');
        }
    } catch (error) {
        console.error('移动用户失败:', error);
        Message.error('移动用户失败，请稍后重试');
    }
};

// 取消移动用户
const cancelMoveUser = () => {
    moveUserModalVisible.value = false;
    moveTargetDeptId.value = '';
    usersToMove.value = [];
    // 清空选中项
    // selectedKeys.value = [];
};

// 删除用户
const handleDelete = async (record) => {
    try {
        const res = await urlResquest.deleteUser({ user_id: record.id, target_user_id: record.id });

        if (res && res.code === 200) {
            Message.success('用户删除成功');

            userList.value = userList.value.filter(user => user.id !== record.id);
        } else {
            Message.error(res?.msg || '删除用户失败');
        }
    } catch (error) {
        console.error('删除用户失败:', error);
        Message.error('删除用户失败，请稍后重试');
    }
};

// 确认删除用户
const confirmDelete = async (record) => {
    try {
        const res = await urlResquest.deleteUser({ user_id: record.id });

        if (res && res.code === 200) {
            Message.success('用户删除成功');

            userList.value = userList.value.filter(user => user.id !== record.id);
        } else {
            Message.error(res?.msg || '删除用户失败');
        }
    } catch (error) {
        console.error('删除用户失败:', error);
        Message.error('删除用户失败，请稍后重试');
    }
};

// 批量删除也添加确认弹窗
const batchDeleteVisible = ref(false);

// 批量删除
const handleBatchDelete = () => {
    if (selectedKeys.value.length === 0) {
        Message.warning('请先选择要删除的用户');
        return;
    }

    batchDeleteVisible.value = true;
};

// 确认批量删除
const confirmBatchDelete = async () => {
    try {
        const userIds = selectedKeys.value;
        const res = await Promise.all(userIds.map(id => urlResquest.deleteUser({ user_id: id })));

        const allSuccess = res.every(r => r && r.code === 200);

        if (allSuccess) {
            Message.success('批量删除成功');

            userList.value = userList.value.filter(user => !userIds.includes(user.id));
        } else {
            Message.warning('部分用户删除失败');

            if (selectedDepartment.value && selectedDepartment.value.length > 0) {
                fetchDepartmentUsers(selectedDepartment.value[0]);
            }
        }

        // 清空选中项
        selectedKeys.value = [];
        batchDeleteVisible.value = false;
    } catch (error) {
        console.error('批量删除用户失败:', error);
        Message.error('批量删除用户失败，请稍后重试');

        // 发生错误时也清空选中项
        selectedKeys.value = [];
        batchDeleteVisible.value = false;
    }
};

// 页码变化
const onPageChange = (page) => {
    pagination.current = page;
};

// 添加部门相关
const addDepartmentModalVisible = ref(false);
const departmentForm = reactive({
    name: '',
    parentId: ''
});

// 将树形结构扁平化为列表，用于上级部门选择
const flatDepartments = computed(() => {
    const result = [];

    const flatten = (items, level = 0) => {
        if (!items) return;

        items.forEach(item => {
            result.push({
                key: item.key,
                title: item.title,
                // 添加一个新属性用于显示带缩进的文本
                displayTitle: '　'.repeat(level) + item.title
            });

            if (item.children && item.children.length > 0) {
                flatten(item.children, level + 1);
            }
        });
    };

    flatten(departmentTree.value);
    return result;
});

// 显示添加部门弹窗
const showAddDepartmentModal = () => {
    addDepartmentModalVisible.value = true;
};

// 确认添加部门
const confirmAddDepartment = async () => {
    if (!departmentForm.name) {
        Message.error('请输入部门名称');
        return;
    }

    try {
        const res = await urlResquest.createDepartment({
            dept_name: departmentForm.name,
            parent_dept_id: departmentForm.parentId || null
        });

        if (res && res.code === 200) {
            Message.success('部门创建成功');

            departmentForm.name = '';
            departmentForm.parentId = '';
            addDepartmentModalVisible.value = false;

            fetchDepartmentList();
        } else {
            Message.error(res?.msg || '创建部门失败');
        }
    } catch (error) {
        console.error('创建部门失败:', error);
        Message.error('创建部门失败，请稍后重试');
    }
};

// 取消添加部门
const cancelAddDepartment = () => {
    departmentForm.name = '';
    departmentForm.parentId = '';
    addDepartmentModalVisible.value = false;
};

// 获取弹出层容器
const popupContainer = () => {
    return document.body;
};

// 处理移动部门
const handleMoveDepartment = (nodeData) => {
    console.log('移动部门:', nodeData);
    Message.info(`准备移动部门: ${nodeData.title}`);
};

// 添加删除部门确认弹窗状态
const deleteDeptModalVisible = ref(false);
const deptToDelete = ref(null);

// 处理删除部门
const handleDeleteDepartment = (nodeData) => {
    console.log('删除部门数据:', nodeData);
    
    if (!nodeData || !nodeData.key) {
        console.error('无效的节点数据');
        Message.error('无法获取部门信息，请刷新页面后重试');
        return;
    }
    
    // 安全地检查children属性
    const hasChildren = nodeData.children && Array.isArray(nodeData.children) && nodeData.children.length > 0;
    
    if (hasChildren) {
        Message.warning('该部门下有子部门，无法直接删除');
        return;
    }
    
    // 使用确认对话框
    Modal.confirm({
        title: '删除部门',
        content: `确定要删除部门 "${nodeData.title}" 吗？此操作不可撤销，请谨慎操作。`,
        okText: '确认删除',
        okButtonProps: { status: 'danger' },
        onOk: () => {
            console.log('确认删除部门:', nodeData.key);
            return deleteDepartment(nodeData.key);
        }
    });
};

// 确认删除部门
const confirmDeleteDepartment = async () => {
    if (!deptToDelete.value) return;

    try {
        await deleteDepartment(deptToDelete.value.key);
        deleteDeptModalVisible.value = false;
        deptToDelete.value = null;
    } catch (error) {
        console.error('确认删除部门失败:', error);
    }
};

// 删除部门API调用
const deleteDepartment = async (deptId) => {
    try {
        const loadingMessage = Message.loading({
            content: '正在删除部门...',
            duration: 0
        });

        const res = await urlResquest.deleteDepartment({ dept_id: deptId });

        loadingMessage.close();

        if (res && res.code === 200) {
            Message.success('部门删除成功');

            // 刷新部门列表
            fetchDepartmentList();

            // 如果当前选中的是被删除的部门，清空选择
            if (selectedDepartment.value && selectedDepartment.value[0] === deptId) {
                selectedDepartment.value = [];
                userList.value = [];
            }
        } else {
            Message.error(res?.msg || '删除部门失败');
        }
    } catch (error) {
        console.error('删除部门失败:', error);
        Message.error('删除部门失败，请稍后重试');
    }
};

// 修改密码相关
const changePasswordModalVisible = ref(false);
const passwordForm = reactive({
    newPassword: '',
    confirmPassword: '',
    userId: null
});

// 处理修改密码
const handleChangePassword = (record) => {
    passwordForm.newPassword = '';
    passwordForm.confirmPassword = '';
    passwordForm.userId = record.id;
    changePasswordModalVisible.value = true;
};

// 确认修改密码
const confirmChangePassword = async () => {
    if (!passwordForm.newPassword || !passwordForm.confirmPassword) {
        Message.error('请输入新密码和确认密码');
        return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
        Message.error('两次输入的密码不一致');
        return;
    }

    try {
        const loadingMessage = Message.loading({
            content: '正在修改密码...',
            duration: 0
        });

        const res = await urlResquest.changeUserPassword({
            user_id: passwordForm.userId,
            new_password: passwordForm.newPassword,
            old_password: passwordForm.oldPassword
        });

        loadingMessage.close();

        if (res && res.code === 200) {
            Message.success('密码修改成功');
            changePasswordModalVisible.value = false;
            passwordForm.newPassword = '';
            passwordForm.confirmPassword = '';
            passwordForm.userId = null;
        } else {
            Message.error(res?.msg || '密码修改失败');
        }
    } catch (error) {
        console.error('修改密码失败:', error);
        Message.error('修改密码失败，请稍后重试');
    }
};

// 取消修改密码
const cancelChangePassword = () => {
    passwordForm.newPassword = '';
    passwordForm.confirmPassword = '';
    passwordForm.userId = null;
    changePasswordModalVisible.value = false;
};
</script>

<style scoped>
.management-layout {
    display: flex;
    height: 100%;
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.sidebar {
    width: 312px;
    border-right: 1px solid var(--color-border);
    padding: 16px 0;
    background-color: var(--color-bg-1);
}

.sidebar-header {
    padding: 0 16px 16px;
    border-bottom: 1px solid var(--color-border);
    margin-bottom: 8px;
}

.sidebar-header h3 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 500;
    color: #1a1a1a;
}

.sidebar-desc {
    color: #767676;
    font-size: 16px;
    margin: 0 0 16px 0;
    line-height: 1.5;
}

.add-department-btn {
    width: 100%;
}

.user-management-container {
    flex: 1;
    padding: 20px;
    overflow: auto;
}

.header {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 20px;
}

.search-input {
    margin-right: 12px;
    width: 220px;
}

.action-buttons {
    display: flex;
    gap: 10px;
}

.sidebar-tree {
    padding: 0 16px;
}

.node-action-trigger {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    cursor: pointer;
}

.node-action-icon {
    cursor: pointer;
    color: var(--color-text-3);
    transition: color 0.2s;
}

.node-action-icon:hover {
    color: var(--color-text-1);
}

.tree-node-actions {
    min-width: 100px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.action-button {
    justify-content: flex-start;
    width: 100%;
    text-align: left;
}

.action-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    cursor: pointer;
    transition: background-color 0.2s;
    border-radius: 2px;
}

.action-item:hover {
    background-color: var(--color-fill-2);
}

.action-item.danger {
    color: var(--color-danger);
}

.action-item.danger:hover {
    background-color: var(--color-danger-light-1);
}

.action-item i {
    margin-right: 8px;
    font-size: 14px;
}

.action-item span {
    font-size: 14px;
}
</style>