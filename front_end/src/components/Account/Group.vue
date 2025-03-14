<template>
  <div class="group-container">
    <a-table 
      :dataSource="groupData" 
      :columns="columns" 
      :pagination="{
        position: ['bottomRight']
      }"
      style="height: 100%;"
      :loading="tableLoading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-dropdown>
            <template #overlay>
              <a-menu>
                <!-- <a-menu-item @click="editGroup(record)">
                  <template #icon><EditOutlined /></template>
                  编辑信息
                </a-menu-item> -->
                <a-menu-item @click="manageMembers(record)">
                  <template #icon><UserOutlined /></template>
                  管理成员
                </a-menu-item>
                <!-- <a-menu-item @click="transferOwnership(record)">
                  <template #icon><SwapOutlined /></template>
                  转让所有者
                </a-menu-item> -->
                <a-menu-divider />
                <a-menu-item danger @click="deleteGroup(record)">
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-menu-item>
              </a-menu>
            </template>
            <a-button type="link">
              <MoreOutlined />
            </a-button>
          </a-dropdown>
        </template>
      </template>
    </a-table>

    <!-- 创建群组弹窗 -->
    <a-modal
      v-model:visible="createModalVisible"
      title="创建群组"
      @ok="handleCreateOk"
      @cancel="handleCreateCancel"
      :confirmLoading="createLoading"
    >
      <a-form :model="createForm">
        <a-form-item>
          <a-input v-model:value="createForm.name" placeholder="请输入群组名称" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 管理成员弹窗 -->
    <a-modal
      v-model:visible="manageMembersVisible"
      title="管理群组成员"
      width="800px"
      @ok="handleManageMembersOk"
      @cancel="handleManageMembersCancel"
      :footer="null"
    >
      <!-- <a-input-search
        v-model:value="searchMember"
        placeholder="搜索用户名"
        style="margin-bottom: 16px"
      /> -->
      
      <div class="members-container">
        <div class="members-column">
          <div class="column-header">可添加成员</div>
          <a-spin :spinning="membersLoading">
            <div class="members-list">
              <div 
                v-for="member in filteredAllMembers" 
                :key="member.user_id"
                :class="['member-item', { disabled: member.disabled }]"
                @click="!member.disabled && addMemberToGroup(member.user_id)"
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
                  <a-tag color="default">已在群组</a-tag>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
        
        <div class="members-column">
          <div class="column-header">群组成员</div>
          <a-spin :spinning="membersLoading">
            <div class="members-list">
              <div 
                v-for="member in filteredGroupMembers" 
                :key="member.user_id"
                class="member-item"
                @click="removeMemberFromGroup(member.user_id)"
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
  </div>
</template>

<script setup>
import { ref, onMounted, defineExpose, computed } from 'vue'
import {
  MoreOutlined,
  EditOutlined,
  UserOutlined,
  SwapOutlined,
  DeleteOutlined,
  PlusOutlined,
  MinusOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import urlResquest from '@/services/urlConfig'

const columns = [
  {
    title: '群组名称',
    dataIndex: 'group_name',
    key: 'group_name'
  },
  // {
  //   title: '所有者',
  //   dataIndex: 'owner',
  //   key: 'owner'
  // },
  // {
  //   title: '成员',
  //   dataIndex: 'members',
  //   key: 'members'
  // },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

const tableLoading = ref(false)

// 创建群组相关状态
const createModalVisible = ref(false)
const createLoading = ref(false)
const groupData = ref([])
const createForm = ref({
  name: ''
})

// 管理成员相关状态
const manageMembersVisible = ref(false)
const searchMember = ref('')
const membersLoading = ref(false)
const allMembers = ref([])
const groupMembers = ref([])
const currentGroupId = ref(null)
const currentGroupName = ref('')

const getGroupList = async () => {
  tableLoading.value = true
  try {
    const res = await urlResquest.groupList()
    if (res.code === 200) {
      groupData.value = res.data.map(item => ({
        group_id: item.group_id,
        group_name: item.group_name,
        owner: item.owner,
        members: item.members || ''
      }))
    } else {
      message.error(res.msg || '获取群组列表失败')
    }
  } catch (error) {
    console.error('获取群组列表失败:', error)
    message.error('获取群组列表失败')
  } finally {
    tableLoading.value = false
  }
}

onMounted(() => {
  getGroupList()
})

// 打开创建群组弹窗
const showCreateModal = () => {
  createModalVisible.value = true
}

// 创建群组
const handleCreateOk = async () => {
  if (!createForm.value.name.trim()) {
    message.warning('请输入群组名称')
    return
  }
  
  createLoading.value = true
  try {
    // 发送创建群组请求
    const res = await urlResquest.createGroup({
      group_name: createForm.value.name
    })
    
    if (res.code === 200) {
      message.success('创建群组成功')
      createModalVisible.value = false
      createForm.value = { name: '' }
      // 刷新群组列表
      getGroupList()
    } else {
      message.error(res.msg || '创建群组失败')
    }
  } catch (error) {
    console.error('创建群组失败:', error)
    message.error('创建群组失败')
  } finally {
    createLoading.value = false
  }
}

// 取消创建
const handleCreateCancel = () => {
  createModalVisible.value = false
  createForm.value = { name: '' }
}

const editGroup = (record) => {
  console.log('编辑群组:', record)
}

// 管理成员
const manageMembers = (record) => {
  currentGroupId.value = record.group_id
  currentGroupName.value = record.group_name
  manageMembersVisible.value = true
  searchMember.value = ''
  getUserList()
}

// 获取用户列表
const getUserList = async () => {
  membersLoading.value = true
  try {
    const res = await urlResquest.userList()
    if (res.code === 200) {
      const users = res.data
      
      // 筛选出当前群组的成员
      groupMembers.value = users
        .filter(user => {
          return user.groups && user.groups.some(group => group.group_id === currentGroupId.value)
        })
        .map(user => ({
          ...user,
          key: user.user_id
        }))
      
      // 筛选出不在当前群组的成员
      allMembers.value = users
        .filter(user => {
          // 如果用户已在当前群组，则排除
          if (user.groups && user.groups.some(group => group.group_id === currentGroupId.value)) {
            return false
          }
          return true
        })
        .map(user => ({
          ...user,
          key: user.user_id,
          disabled: false
        }))
    } else {
      message.error(res.msg || '获取用户列表失败')
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    message.error('获取用户列表失败')
  } finally {
    membersLoading.value = false
  }
}

// 添加成员到群组
const addMemberToGroup = async (userId) => {
  try {
    // 使用 group/add_user 接口添加用户到群组
    const res = await urlResquest.addUserToGroup({
      user_id: localStorage.getItem('userId') || '',
      target_user_ids: [userId],
      group_id: currentGroupId.value
    })
    
    if (res.code === 200) {
      message.success('添加成员成功')
      
      // 找到要移动的成员
      const memberToMove = allMembers.value.find(m => m.user_id === userId)
      if (memberToMove) {
        // 从左侧列表中移除
        allMembers.value = allMembers.value.filter(
          member => member.user_id !== userId
        )
        
        // 添加到右侧群组成员列表
        groupMembers.value.push({
          ...memberToMove,
          groups: [...(memberToMove.groups || []), {
            group_id: currentGroupId.value,
            group_name: currentGroupName.value
          }]
        })
        
        // 刷新用户列表
        getUserList()
      }
    } else {
      message.error(res.msg || '添加成员失败')
    }
  } catch (error) {
    console.error('添加成员失败:', error)
    message.error('添加成员失败')
  }
}

// 从群组移除成员
const removeMemberFromGroup = async (userId) => {
  try {
    // 使用 group/remove_user 接口从群组移除用户
    const res = await urlResquest.removeUserFromGroup({
      user_id: localStorage.getItem('userId') || '',
      target_user_id: userId,
      group_id: currentGroupId.value
    })
    
    if (res.code === 200) {
      message.success('移除成员成功')
      
      // 找到要移除的成员
      const memberToRemove = groupMembers.value.find(m => m.user_id === userId)
      if (memberToRemove) {
        // 从右侧群组成员中移除
        groupMembers.value = groupMembers.value.filter(
          member => member.user_id !== userId
        )
        
        // 添加到左侧所有成员列表
        allMembers.value.push({
          ...memberToRemove,
          groups: (memberToRemove.groups || []).filter(
            group => group.group_id !== currentGroupId.value
          ),
          disabled: false
        })
        
        // 刷新用户列表
        getUserList()
      }
    } else {
      message.error(res.msg || '移除成员失败')
    }
  } catch (error) {
    console.error('移除成员失败:', error)
    message.error('移除成员失败')
  }
}

const transferOwnership = (record) => {
  console.log('转让所有者:', record)
}

const deleteGroup = (record) => {
  Modal.confirm({
    title: '删除警告',
    content: '确认删除该群组？',
    okText: '确认',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        console.log(record.group_id)
        const res = await urlResquest.deleteGroup({
          group_id: record.group_id,
          user_id: localStorage.getItem('userId') || ''
        });
        
        if (res.code === 200) {
          message.success('删除成功');
          // 刷新群组列表
          getGroupList();
        } else {
          message.error(res.msg || '删除失败');
        }
      } catch (error) {
        console.error('删除群组失败:', error);
        message.error('删除群组失败');
      }
    }
  });
}

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

const filteredGroupMembers = computed(() => {
  if (!searchMember.value) return groupMembers.value;
  return groupMembers.value.filter(member => 
    member.user_name.toLowerCase().includes(searchMember.value.toLowerCase())
  );
});

// 暴露方法给父组件
defineExpose({
  showCreateModal
})
</script>

<style scoped>
.group-container {
  height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

:deep(.ant-table-wrapper) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.ant-spin-nested-loading) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.ant-spin-container) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.ant-table) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

:deep(.ant-table-container) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 成员管理弹窗样式 */
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
</style>
