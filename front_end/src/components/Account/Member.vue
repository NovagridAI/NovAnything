<template>
  <div>
    <!-- <h1>Member</h1> -->
    <a-table :columns="columns" :data-source="props.userList" :pagination="false">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'operation'">
          <a-space :size="16">
            <a-tooltip :title="record.status === 1 ? '停用用户' : '启用用户'">
              <stop-outlined 
                :class="{ 'disabled': record.status === 0 }"
                @click="handleStatus(record)" 
              />
            </a-tooltip>
            <a-tooltip title="升级为管理员">
              <user-switch-outlined 
                :class="{ 'disabled': record.role === 'admin' }"
                @click="handleUpgrade(record)" 
              />
            </a-tooltip>
            <a-tooltip title="删除用户">
              <delete-outlined 
                class="delete-icon" 
                @click="handleDelete(record)" 
              />
            </a-tooltip>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 确认对话框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalConfig.title"
      @ok="handleModalOk"
      @cancel="modalVisible = false"
    >
      <p>{{ modalConfig.content }}</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { StopOutlined, UserSwitchOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import type { TableColumnType } from 'ant-design-vue';

interface UserType {
  id: string;
  username: string;
  loginType: string;
  department: string;
  updateTime: string;
  status: number;
  role: string;
}

const props = defineProps({
  userList: {
    type: Array as () => UserType[],
    default: () => [],
  },
});

const emit = defineEmits(['refresh']);

// 表格列定义
const columns = ref<TableColumnType[]>([
  {
    title: '用户名',
    dataIndex: 'user_name',
    key: 'user_name',
  },
  // {
  //   title: '登录方式',
  //   dataIndex: 'loginType', 
  //   key: 'loginType',
  // },
  {
    title: '部门',
    dataIndex: 'role',
    key: 'role',
  },
  {
    title: '加入/更新时间',
    dataIndex: 'creation_time',
    key: 'creation_time',
  },
  {
    title: '操作',
    key: 'operation',
  },
]);

// 模态框配置
const modalVisible = ref(false);
const modalConfig = ref({
  title: '',
  content: '',
  action: '',
  record: null as UserType | null,
});

// 处理用户状态变更
const handleStatus = (record: UserType) => {
  modalConfig.value = {
    title: record.status === 1 ? '停用用户' : '启用用户',
    content: `确定要${record.status === 1 ? '停用' : '启用'}该用户吗？`,
    action: 'status',
    record,
  };
  modalVisible.value = true;
};

// 处理升级管理员
const handleUpgrade = (record: UserType) => {
  if (record.role === 'admin') {
    message.warning('该用户已经是管理员');
    return;
  }
  modalConfig.value = {
    title: '升级为管理员',
    content: '确定要将该用户升级为管理员吗？',
    action: 'upgrade',
    record,
  };
  modalVisible.value = true;
};

// 处理删除用户
const handleDelete = (record: UserType) => {
  modalConfig.value = {
    title: '删除用户',
    content: '确定要删除该用户吗？此操作不可恢复。',
    action: 'delete',
    record,
  };
  modalVisible.value = true;
};

// 处理模态框确认
const handleModalOk = async () => {
  try {
    const { action, record } = modalConfig.value;
    if (!record) return;

    // TODO: 替换为实际的 API 调用
    switch (action) {
      case 'status':
        // await api.updateUserStatus(record.id, record.status === 1 ? 0 : 1);
        message.success(`${record.status === 1 ? '停用' : '启用'}成功`);
        break;
      case 'upgrade':
        // await api.upgradeToAdmin(record.id);
        message.success('升级成功');
        break;
      case 'delete':
        // await api.deleteUser(record.id);
        message.success('删除成功');
        break;
    }
    
    modalVisible.value = false;
    emit('refresh'); // 通知父组件刷新数据
  } catch (error) {
    message.error('操作失败');
  }
};
</script>

<style scoped>
.anticon {
  font-size: 16px;
  cursor: pointer;
}

.anticon:hover {
  color: #1890ff;
}

.disabled {
  color: #d9d9d9;
  cursor: not-allowed;
}

.disabled:hover {
  color: #d9d9d9;
}

.delete-icon {
  color: #ff4d4f;
}

.delete-icon:hover {
  color: #ff7875;
}
</style>

