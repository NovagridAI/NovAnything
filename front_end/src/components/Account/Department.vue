<template>
  <div class="department-container">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- <div class="header-actions">
        <a-button type="primary" @click="showCreateModal">创建部门</a-button>
      </div> -->

      <div class="department-path">
        <a-breadcrumb>
          <a-breadcrumb-item>
            <a @click="showDepartment(null)">全部部门</a>
          </a-breadcrumb-item>
          <a-breadcrumb-item v-if="currentDepartment">
            {{ currentDepartment.dept_name }}
          </a-breadcrumb-item>
        </a-breadcrumb>
      </div>

      <a-table :columns="columns" :data-source="tableData" :pagination="false" :loading="tableLoading">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="department-row">
              <div class="department-info">
                <a @click="showDepartment(record.dept_id)">
                  {{ record.dept_name }}
                  <span v-if="getChildrenCount(record.dept_id)" class="sub-count">
                    ({{ getChildrenCount(record.dept_id) }})
                  </span>
                </a>
                
                <!-- 展开/收起按钮 -->
                <a-button 
                  v-if="getDepartmentMembers(record.dept_id).length > 0"
                  type="link" 
                  size="small"
                  @click.stop="toggleDepartment(record.dept_id)"
                  style="margin-left: 8px;"
                >
                  <template #icon>
                    <caret-down-outlined v-if="isDepartmentExpanded(record.dept_id)" />
                    <caret-right-outlined v-else />
                  </template>
                  {{ isDepartmentExpanded(record.dept_id) ? '收起成员' : '查看成员' }}
                </a-button>
              </div>
              
              <!-- 部门成员列表 -->
              <div v-if="isDepartmentExpanded(record.dept_id)" class="department-members">
                <div 
                  v-for="member in getDepartmentMembers(record.dept_id)" 
                  :key="member.user_id"
                  class="member-item-inline"
                >
                  <user-outlined />
                  <span class="member-name-inline">{{ member.user_name }}</span>
                </div>
                <div v-if="getDepartmentMembers(record.dept_id).length === 0" class="no-members">
                  暂无成员
                </div>
              </div>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 右侧边栏 -->
    <div class="right-sidebar">
      <!-- <div class="sidebar-header">
        <div class="department-name">{{ currentDepartment ? currentDepartment.dept_name : '全部部门' }}</div>
        <div class="department-desc">管理部门</div>
      </div> -->
      
      <div class="sidebar-content">
        <a-button type="primary" block @click="showCreateModal" :loading="createLoading">
          <plus-outlined />{{ currentParentId === null ? '创建部门' : '创建子部门' }}
        </a-button>
        
        <!-- 只在查看具体部门时显示分割线和菜单 -->
        <template v-if="currentParentId !== null">
          <a-divider />
          
          <a-menu mode="inline">
            <a-menu-item key="members" @click="showManageMembers">
              <team-outlined />
              <span>管理成员</span>
            </a-menu-item>
            <!-- <a-menu-item key="move" @click="showMoveModal">
              <swap-outlined />
              <span>移动部门</span>
            </a-menu-item> -->
            <a-menu-item key="delete" @click="showDeleteConfirm" :disabled="deleteLoading">
              <delete-outlined />
              <span>删除部门</span>
            </a-menu-item>
          </a-menu>
        </template>
      </div>
    </div>

    <!-- 创建部门弹窗 -->
    <a-modal
      v-model:visible="createModalVisible"
      title="创建部门"
      @ok="handleCreateOk"
      @cancel="handleCreateCancel"
      :confirmLoading="createLoading"
    >
      <a-form :model="createForm">
        <a-form-item label="名称">
          <a-input v-model:value="createForm.name" placeholder="部门名称" />
        </a-form-item>
        <a-form-item label="介绍">
          <a-textarea v-model:value="createForm.description" placeholder="介绍" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 管理成员弹窗 -->
    <a-modal
      v-model:visible="manageMembersVisible"
      title="管理部门成员"
      width="800px"
      @ok="handleManageMembersOk"
      @cancel="handleManageMembersCancel"
      :footer="null"
    >
      <a-input-search
        v-model:value="searchMember"
        placeholder="搜索用户名"
        style="margin-bottom: 16px"
      />
      
      <div class="members-container">
        <div class="members-column">
          <div class="column-header">可添加成员</div>
          <a-spin :spinning="membersLoading">
            <div class="members-list">
              <div 
                v-for="member in filteredAllMembers" 
                :key="member.user_id"
                :class="['member-item', { disabled: member.disabled }]"
                @click="!member.disabled && addMemberToDepartment(member.user_id)"
              >
                <div class="member-avatar">
                  <user-outlined />
                </div>
                <div class="member-name">{{ member.user_name }}</div>
                <div class="member-action" v-if="!member.disabled">
                  <plus-outlined />
                  <span class="action-text">添加</span>
                </div>
                <div class="member-status" v-if="member.disabled">
                  <tag color="default">已有部门</tag>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
        
        <div class="members-column">
          <div class="column-header">部门成员</div>
          <a-spin :spinning="membersLoading">
            <div class="members-list">
              <div 
                v-for="member in filteredDepartmentMembers" 
                :key="member.user_id"
                class="member-item"
                @click="removeMemberFromDepartment(member.user_id)"
              >
                <div class="member-avatar">
                  <user-outlined />
                </div>
                <div class="member-name">{{ member.user_name }}</div>
                <div class="member-action remove">
                  <minus-outlined />
                  <span class="action-text">移除</span>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
      </div>
    </a-modal>

    <!-- 移动部门弹窗 -->
    <a-modal
      v-model:visible="moveModalVisible"
      title="移动部门"
      @ok="handleMoveOk"
      @cancel="handleMoveCancel"
    >
      <a-tree
        v-model:selectedKeys="selectedDepartments"
        :tree-data="departmentTree"
        @select="onDepartmentSelect"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  PlusOutlined, 
  MinusOutlined, 
  UserOutlined,
  TeamOutlined, 
  DeleteOutlined,
  CaretRightOutlined,
  CaretDownOutlined
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import urlResquest from '@/services/urlConfig'
import type { TableColumnType } from 'ant-design-vue'

const currentDepartment = ref('Team')
const createModalVisible = ref(false)
const manageMembersVisible = ref(false)
const moveModalVisible = ref(false)
const searchMember = ref('')
const selectedMembers = ref([])
const selectedDepartments = ref([])

const dataSource = ref([])
const createForm = ref({
  name: '',
  description: ''
})

const columns = ref<TableColumnType[]>([
  {
    title: '部门名称',
    dataIndex: 'dept_name',
    key: 'name',
  },
  {
    title: '创建时间',
    dataIndex: 'creation_time',
    key: 'creation_time',
  }
])

const memberColumns = [
  {
    title: '用户名',
    dataIndex: 'username',
  }
]

const memberList = ref([
  {
    key: '1',
    username: 'Member',
  }
])

const departmentTree = ref([
  {
    title: 'o5Ljw6jYZ7 Team',
    key: '1',
    children: [
      {
        title: '222',
        key: '2',
      },
    ],
  }
])

// 添加 loading 状态
const tableLoading = ref(false)
const createLoading = ref(false)
const deleteLoading = ref(false)
const membersLoading = ref(false)

// 添加新的状态
const userList = ref<any[]>([]); // 存储所有用户
const expandedDepartments = ref<string[]>([]); // 存储展开的部门ID

// 构建树形结构
const buildTree = (items: any[]) => {
  const result: any[] = []
  const map = new Map()

  // 首先创建一个以 id 为键的 Map
  items.forEach(item => {
    map.set(item.dept_id, { ...item, children: [], expanded: false, level: 0 })
  })

  // 构建树形结构
  items.forEach(item => {
    const node = map.get(item.dept_id)
    if (item.parent_dept_id && map.has(item.parent_dept_id)) {
      const parent = map.get(item.parent_dept_id)
      parent.children.push(node)
      node.level = parent.level + 1
    } else {
      result.push(node)
    }
  })

  return result
}

// 展开/收起部门
const toggleExpand = (record: any) => {
  if (record.children?.length) {
    record.expanded = !record.expanded
  }
}

// 格式化数据为扁平结构，但保持层级关系
const formattedData = computed(() => {
  const result: any[] = []
  
  const flatten = (items: any[], level = 0) => {
    items.forEach(item => {
      result.push({
        ...item,
        level,
      })
      
      if (item.expanded && item.children?.length) {
        flatten(item.children, level + 1)
      }
    })
  }
  
  flatten(buildTree(dataSource.value))
  return result
})

// 获取部门列表
const getDepartmentList = async () => {
  try {
    tableLoading.value = true;
    const res = await urlResquest.departmentList();
    if (res.code === 200) {
      departmentList.value = res.data;
      console.log('部门列表:', departmentList.value); // 添加日志查看数据
    } else {
      message.error(res.msg || '获取部门列表失败');
    }
  } catch (error) {
    console.error('获取部门列表失败:', error);
    message.error('获取部门列表失败');
  } finally {
    tableLoading.value = false;
  }
};

// 创建部门
const handleCreateOk = async () => {
  if (!createForm.value.name) {
    message.warning('请输入部门名称');
    return;
  }

  createLoading.value = true;
  try {
    const res = await urlResquest.createDepartment({
      dept_name: createForm.value.name,
      description: createForm.value.description,
      parent_dept_id: currentParentId.value || null, // 如果是顶层，传null
      user_id: localStorage.getItem('userId')
    });

    if (res.code === 200) {
      message.success('创建成功');
      createModalVisible.value = false;
      getDepartmentList(); // 刷新部门列表
    } else {
      message.error(res.msg || '创建失败');
    }
  } catch (error) {
    console.error('创建部门失败:', error);
    message.error('创建部门失败');
  } finally {
    createLoading.value = false;
  }
};

const handleCreateCancel = () => {
  createModalVisible.value = false;
};

const showCreateModal = () => {
  createModalVisible.value = true;
  createForm.value = {
    name: '',
    description: ''
  };
};

const showManageMembers = () => {
  manageMembersVisible.value = true;
  searchMember.value = '';
  
  // 筛选出当前部门的成员
  departmentMembers.value = userList.value
    .filter(user => user.department && user.department.dept_id === currentParentId.value)
    .map(user => ({
      ...user,
      key: user.user_id
    }));
  
  // 筛选出不在当前部门的成员
  allMembers.value = userList.value
    .filter(user => {
      // 如果用户已在当前部门，则排除
      if (user.department && user.department.dept_id === currentParentId.value) return false;
      
      // 检查是否有部门
      const hasDepartment = user.department !== null && user.department !== undefined;
      
      return {
        ...user,
        key: user.user_id,
        disabled: hasDepartment // 只有真正有部门的成员才禁用
      };
    })
    .map(user => {
      // 检查是否有部门
      const hasDepartment = user.department !== null && user.department !== undefined;
      
      return {
        ...user,
        key: user.user_id,
        disabled: hasDepartment // 只有真正有部门的成员才禁用
      };
    });
};

const showMoveModal = () => {
  moveModalVisible.value = true
}

const showDeleteConfirm = () => {
  Modal.confirm({
    title: '删除警告',
    content: '确认删除该部门？',
    okText: '确认',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      if (!currentParentId.value) {
        message.error('无法删除根部门');
        return;
      }
      
      // 检查是否有子部门
      const hasChildren = getChildrenCount(currentParentId.value) > 0;
      if (hasChildren) {
        message.error('该部门下有子部门，请先删除子部门');
        return;
      }
      
      deleteLoading.value = true;
      try {
        const res = await urlResquest.deleteDepartment({
          dept_id: currentParentId.value,
          user_id: localStorage.getItem('userId')
        });
        
        if (res.code === 200) {
          message.success('删除成功');
          // 返回上一级
          const parentDept = departmentList.value.find(
            dept => dept.dept_id === currentParentId.value
          );
          showDepartment(parentDept?.parent_dept_id || null);
          // 刷新部门列表
          getDepartmentList();
        } else {
          message.error(res.msg || '删除失败');
        }
      } catch (error) {
        console.error('删除部门失败:', error);
        if (error.response && error.response.data && error.response.data.msg) {
          message.error(error.response.data.msg);
        } else {
          message.error('删除部门失败');
        }
      } finally {
        deleteLoading.value = false;
      }
    },
  });
};

const enterDepartment = (record) => {
  console.log('进入部门:', record)
}

onMounted(() => {
  getDepartmentList()
  getUserList()
})

interface DepartmentType {
  dept_id: string;
  dept_name: string;
  parent_dept_id: string | null;
  parent_dept_name: string | null;
  creation_time: string;
}

const departmentList = ref<DepartmentType[]>([])
const currentParentId = ref<string | null>(null)

// 表格显示的数据
const tableData = computed(() => {
  // 当 currentParentId 为 null 时，显示顶层部门
  return departmentList.value.filter(dept => {
    if (currentParentId.value === null) {
      return dept.parent_dept_id === null; // 显示顶层部门
    }
    return dept.parent_dept_id === currentParentId.value; // 显示子部门
  });
})

// 获取子部门数量
const getChildrenCount = (deptId: string) => {
  return departmentList.value.filter(dept => 
    dept.parent_dept_id === deptId
  ).length
}

// 获取当前部门信息
const currentDepartmentInfo = computed(() => {
  if (!currentParentId.value) return null
  return departmentList.value.find(dept => 
    dept.dept_id === currentParentId.value
  )
})

// 显示指定部门的子部门
const showDepartment = (deptId: string | null) => {
  currentParentId.value = deptId
  
  // 如果有部门ID，找到对应的部门信息
  if (deptId) {
    currentDepartment.value = departmentList.value.find(
      dept => dept.dept_id === deptId
    ) || null;
  } else {
    currentDepartment.value = null;
  }
  
  // 每次切换部门时，确保用户列表是最新的
  getUserList();
};

// 管理成员相关
const allMembers = ref<any[]>([])
const departmentMembers = ref<any[]>([])

// 获取所有成员
const getAllMembers = async () => {
  membersLoading.value = true;
  try {
    const res = await urlResquest.userList();
    if (res.code === 200) {
      const allUsers = res.data;
      
      // 筛选出当前部门的成员
      departmentMembers.value = allUsers
        .filter((user: any) => user.dept_id === currentParentId.value)
        .map((user: any) => ({
          ...user,
          key: user.user_id
        }));
      
      // 筛选出不在当前部门的成员
      allMembers.value = allUsers
        .filter((user: any) => user.dept_id !== currentParentId.value)
        .map((user: any) => ({
          ...user,
          key: user.user_id,
          disabled: user.dept_id !== null // 如果已经有部门则禁用
        }));
    } else {
      message.error(res.msg || '获取成员列表失败');
    }
  } catch (error) {
    console.error('获取成员列表失败:', error);
    message.error('获取成员列表失败');
  } finally {
    membersLoading.value = false;
  }
};

// 获取部门成员 - 修正空值处理
const getDepartmentMembers = (deptId: string) => {
  return userList.value.filter(user => {
    // 检查用户是否有部门信息
    if (!user.department) {
      // 如果查询的是无部门用户
      return deptId === null || deptId === undefined || deptId === '';
    } else {
      // 使用新的数据结构中的 department.dept_id 进行比较
      return user.department.dept_id === deptId;
    }
  });
};

// 添加成员到部门
const addMemberToDepartment = async (userId: string) => {
  try {
    const res = await urlResquest.updateUser({
      user_id: localStorage.getItem('userId') || '',
      target_user_id: userId,
      dept_id: currentParentId.value
    });
    
    if (res.code === 200) {
      message.success('添加成员成功');
      
      // 找到要移动的成员
      const memberToMove = allMembers.value.find(m => m.user_id === userId);
      if (memberToMove) {
        // 从左侧列表中移除
        allMembers.value = allMembers.value.filter(
          member => member.user_id !== userId
        );
        
        // 添加到右侧部门成员列表
        departmentMembers.value.push({
          ...memberToMove,
          department: {
            dept_id: currentParentId.value,
            dept_name: currentDepartmentInfo.value?.dept_name || ''
          }
        });
        
        // 刷新用户列表以更新展示
        getUserList();
      }
    } else {
      message.error(res.msg || '添加成员失败');
    }
  } catch (error) {
    console.error('添加成员失败:', error);
    message.error('添加成员失败');
  }
};

// 从部门移除成员
const removeMemberFromDepartment = async (userId: string) => {
  try {
    const res = await urlResquest.updateUser({
      user_id: localStorage.getItem('userId') || '',
      target_user_id: userId,
      dept_id: null // 设置为 null 表示移除部门
    });
    
    if (res.code === 200) {
      message.success('移除成员成功');
      
      // 找到要移除的成员
      const memberToRemove = departmentMembers.value.find(m => m.user_id === userId);
      if (memberToRemove) {
        // 从右侧部门成员中移除
        departmentMembers.value = departmentMembers.value.filter(
          member => member.user_id !== userId
        );
        
        // 添加到左侧所有成员列表
        allMembers.value.push({
          ...memberToRemove,
          department: null,
          disabled: false
        });
        
        // 刷新用户列表以更新展示
        getUserList();
      }
    } else {
      message.error(res.msg || '移除成员失败');
    }
  } catch (error) {
    console.error('移除成员失败:', error);
    message.error('移除成员失败');
  }
};

// 处理管理成员确认
const handleManageMembersOk = () => {
  manageMembersVisible.value = false;
};

// 处理管理成员取消
const handleManageMembersCancel = () => {
  manageMembersVisible.value = false;
};

// 过滤成员列表
const filteredAllMembers = computed(() => {
  if (!searchMember.value) return allMembers.value;
  return allMembers.value.filter(member => 
    member.user_name.toLowerCase().includes(searchMember.value.toLowerCase())
  );
});

const filteredDepartmentMembers = computed(() => {
  if (!searchMember.value) return departmentMembers.value;
  return departmentMembers.value.filter(member => 
    member.user_name.toLowerCase().includes(searchMember.value.toLowerCase())
  );
});

// 获取用户列表
const getUserList = async () => {
  try {
    const res = await urlResquest.userList();
    if (res.code === 200) {
      userList.value = res.data;
    } else {
      message.error(res.msg || '获取用户列表失败');
    }
  } catch (error) {
    console.error('获取用户列表失败:', error);
    message.error('获取用户列表失败');
  }
};

// 切换部门展开状态
const toggleDepartment = (deptId: string) => {
  if (expandedDepartments.value.includes(deptId)) {
    expandedDepartments.value = expandedDepartments.value.filter(id => id !== deptId);
  } else {
    expandedDepartments.value.push(deptId);
  }
};

// 判断部门是否展开
const isDepartmentExpanded = (deptId: string) => {
  return expandedDepartments.value.includes(deptId);
};
</script>

<style scoped>
.department-container {
  display: flex;
  height: 100%;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}

.right-sidebar {
  width: 256px;
  border-left: 1px solid #f0f0f0;
  background: #fff;
}

.sidebar-header {
  padding: 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.department-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.department-desc {
  font-size: 14px;
  color: #666;
}

.sidebar-content {
  padding: 16px;
}

:deep(.ant-menu-inline) {
  border-right: none;
}

:deep(.ant-menu-item) {
  height: 40px;
  line-height: 40px;
  margin-top: 4px;
  margin-bottom: 4px;
}

.expand-icon {
  margin-right: 8px;
  font-size: 12px;
  transition: transform 0.3s;
}

.sub-count {
  margin-left: 8px;
  color: #999;
  font-size: 12px;
}

/* :deep(.ant-table-row) {
  td:first-child {
    padding-left: v-bind('`${record.level * 24}px`');
  }
} */

.department-path {
  margin-bottom: 16px;
}

:deep(.ant-breadcrumb) {
  a {
    color: #1890ff;
    cursor: pointer;
    
    &:hover {
      color: #40a9ff;
    }
  }
}

.members-container {
  display: flex;
  gap: 20px;
  height: 400px;
}

.members-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.column-header {
  padding: 12px 16px;
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 500;
  color: #333;
}

.members-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.3s;
  background-color: #fff;
  border: 1px solid #f0f0f0;
}

.member-item:hover {
  background-color: #f6f6f6;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.member-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #fafafa;
}

.member-item.disabled:hover {
  transform: none;
  box-shadow: none;
}

.member-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #e6f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  color: #1890ff;
}

.member-name {
  flex: 1;
  font-size: 14px;
}

.member-action {
  display: flex;
  align-items: center;
  color: #1890ff;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.3s;
}

.member-item:hover .member-action {
  opacity: 1;
}

.member-action.remove {
  color: #ff4d4f;
}

.action-text {
  margin-left: 4px;
}

.member-status {
  font-size: 12px;
}

.department-row {
  display: flex;
  flex-direction: column;
}

.department-info {
  display: flex;
  align-items: center;
}

.department-members {
  margin-top: 10px;
  margin-left: 24px;
  padding: 10px 0;
  transition: all 0.3s ease;
}

.member-item-inline {
  display: inline-flex;
  align-items: center;
  margin-right: 16px;
  margin-bottom: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  border: 1px solid #f0f0f0;
}

.member-item-inline:hover {
  border-color: #1890ff;
}

.member-item-inline .anticon {
  color: #1890ff;
  font-size: 14px;
}

.member-name-inline {
  margin-left: 6px;
  font-size: 14px;
  color: #333;
}

.no-members {
  color: #999;
  font-style: italic;
  padding: 8px 0;
  margin-left: 8px;
}

/* 优化展开/收起按钮 */
.department-info .ant-btn-link {
  font-size: 13px;
  padding: 0 8px;
  height: 24px;
  color: #1890ff;
}

.department-info .ant-btn-link:hover {
  color: #40a9ff;
}

.department-info .ant-btn-link .anticon {
  font-size: 12px;
}
</style>
