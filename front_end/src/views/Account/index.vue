<template>
  <div class="account-container">
    <!-- <CollapsibleSidebar /> -->
    <div class="account-content">
      <!-- Tab 导航 -->
      <div class="tabs-wrapper">
        <div class="tabs-nav">
          <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
            :class="['tab-button', { active: activeTab === tab.id }]">
            <div class="tab-content">
              <!-- <svg-icon :name="tab.icon" class="tab-icon"></svg-icon> -->
              <span>{{ tab.name }}</span>
            </div>
          </button>
        </div>
        <div class="action-buttons">
          <template v-if="activeTab === 'department'">
            <a-input
              placeholder="搜索部门"
              style="width: 200px; margin-right: 16px"
              @search="onSearch"
            />
            <a-button type="primary" :disabled="false" @click="inviteMember">
              <template #icon><UserAddOutlined /></template>
              邀请成员
            </a-button>
          </template>
          
          <template v-if="activeTab === 'group'">
            <a-button type="primary" @click="createGroup">
              <template #icon><PlusOutlined /></template>
              创建群组
            </a-button>
          </template>

          <template v-if="activeTab === 'member'">
            <a-input
              placeholder="搜索成员"
              style="width: 200px; margin-right: 16px"
              @search="onSearch"
            />
            <a-button type="primary" :disabled="false" @click="inviteMember">
              <template #icon><UserAddOutlined /></template>
              邀请成员
            </a-button>
          </template>

          <template v-if="activeTab === 'permission'">
            <a-input
              placeholder="搜索成员/部门/群组名称"
              style="width: 240px; margin-right: 16px"
              @search="onSearch"
            />
            <a-button type="primary" @click="addPermission">
              <template #icon><PlusOutlined /></template>
              添加权限
            </a-button>
          </template>
        </div>
      </div>

      <!-- Tab 内容区域 -->
      <div class="tab-panel">
        <transition name="fade" mode="out-in">
          <div class="tab-inner" v-if="activeTab === 'member'">
            <Member :userList="userList" :loading="tableLoading" @refresh="getUserList" />
          </div>
          <div class="tab-inner" v-else-if="activeTab === 'department'">
            <Department />
          </div>
          <div class="tab-inner" v-else-if="activeTab === 'group'">
            <Group ref="groupRef" />
          </div>
          <div class="tab-inner" v-else-if="activeTab === 'permission'">
            <Permission />
          </div>
        </transition>
      </div>
    </div>

    <!-- 添加邀请成员弹窗 -->
    <a-modal
      v-model:visible="inviteModalVisible"
      title="邀请成员"
      @ok="handleInviteConfirm"
      @cancel="handleInviteCancel"
      :confirmLoading="inviteLoading"
      class="invite-modal"
      :closable="false"
    >
      <a-form :model="inviteForm">
        <a-form-item name="username">
          <a-input v-model:value="inviteForm.username" placeholder="请输入用户名" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { UserAddOutlined, PlusOutlined } from '@ant-design/icons-vue';
import Member from '@/components/Account/Member.vue';
import Department from '@/components/Account/Department.vue';
import Group from '@/components/Account/Group.vue';
import Permission from '@/components/Account/Permission.vue';
import { ref, onMounted } from 'vue';
import urlResquest from '@/services/urlConfig';
import { resultControl } from '@/utils/utils';
import { message } from 'ant-design-vue';

const tabs = [
  {
    id: 'member',
    name: '成员',
    icon: 'user'
  },
  {
    id: 'department',
    name: '部门',
    icon: 'shield'
  },
  {
    id: 'group',
    name: '群组',
    icon: 'bell'
  },
  // {
  //   id: 'permission',
  //   name: '权限',
  //   icon: 'credit-card'
  // }
];

const activeTab = ref('member');

const onSearch = (value: string) => {
  console.log('搜索:', value);
};

// 邀请成员相关状态
const inviteModalVisible = ref(false);
const inviteLoading = ref(false);
const inviteForm = ref({
  username: ''
});

// 打开邀请弹窗
const inviteMember = () => {
  inviteModalVisible.value = true;
};

// 取消邀请
const handleInviteCancel = () => {
  inviteModalVisible.value = false;
  inviteForm.value.username = '';
};

// 确认邀请
const handleInviteConfirm = async () => {
  if (!inviteForm.value.username) {
    message.warning('请输入用户名');
    return;
  }

  inviteLoading.value = true;
  try {
    const result: any = await urlResquest.createUser({
      user_name: inviteForm.value.username,
      password: '123456',
    });
    
    // 使用 resultControl 统一处理响应
    // const result = await resultControl(res);
    message.success('邀请成功');
    inviteModalVisible.value = false;
    inviteForm.value.username = '';
    // 刷新用户列表
    getUserList();
  } catch (error) {
    console.error('邀请失败:', error);
    message.error(error.msg || '邀请失败');
  } finally {
    inviteLoading.value = false;
  }
};

const groupRef = ref(null)

const createGroup = () => {
  groupRef.value.showCreateModal()
}

const addPermission = () => {
  console.log('添加权限');
};

// 用户列表数据
const userList = ref([]);

// 添加 loading 状态
const tableLoading = ref(false);

// 修改获取用户列表函数
const getUserList = async () => {
  tableLoading.value = true;
  try {
    const res: any = await urlResquest.userList();
    console.log(res);
    if(res.code === 200) {
      userList.value = res.data;
    } else {
      message.error(res.msg || '获取用户列表失败');
    }
  } catch (error) {
    console.error('获取用户列表失败:', error);
    message.error('获取用户列表失败');
  } finally {
    tableLoading.value = false;
  }
};

// 在组件挂载时获取数据
onMounted(() => {
  getUserList();
});
</script>

<style scoped lang="scss">
.account-container {
  display: flex;
  height: 100vh;
}

.account-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 24px;
  background-color: $mainBgColor;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #667085;
}

.tabs-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.tabs-nav {
  background-color: $secondaryBgColor;
  padding: 4px 4px;
  border-radius: 8px;
  width: auto;
  margin-bottom: 0;
}

.action-buttons {
  display: flex;
  align-items: center;
}

.tab-button {
  flex: 1;
  width: 146px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  color: $textColor;

  &:hover:not(.active) {
    background-color: #f4f4f5;
    color: #667085;
  }

  &.active {
    background-color: $mainBgColor;
    color: $textTitleColor;
    box-shadow: $shadow;
  }
}

.tab-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.tab-icon {
  width: 20px;
  height: 20px;
}

.tab-panel {
  background-color: #fff;
  flex: 1;
  border-radius: 12px;
  padding: 24px;
  min-height: 300px;

  .tab-inner {
    height: 100%;
    flex: 1;
  }
  // box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

// 响应式设计
@media screen and (max-width: 768px) {
  .tabs-wrapper {
    flex-direction: column;
    gap: 16px;
  }

  .tabs-nav {
    width: 100%;
  }

  .action-buttons {
    width: 100%;
    flex-direction: column;
    gap: 12px;
    
    .ant-input-search {
      width: 100% !important;
      margin-right: 0;
      margin-bottom: 8px;
    }

    .ant-btn {
      width: 100%;
    }
  }
}

// 添加过渡效果
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: translateX(0);
}

// 添加邀请成员弹窗样式
:deep(.invite-modal) {
  .ant-modal-title {
    text-align: center;
  }
  
  .ant-form {
    margin-top: 16px;
  }
}
</style>
