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
                <a-menu-item @click="editGroup(record)">
                  <template #icon><EditOutlined /></template>
                  编辑信息
                </a-menu-item>
                <a-menu-item @click="manageMembers(record)">
                  <template #icon><UserOutlined /></template>
                  管理成员
                </a-menu-item>
                <a-menu-item @click="transferOwnership(record)">
                  <template #icon><SwapOutlined /></template>
                  转让所有者
                </a-menu-item>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  MoreOutlined,
  EditOutlined,
  UserOutlined,
  SwapOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import urlResquest from '@/services/urlConfig'

const columns = [
  {
    title: '群组名称',
    dataIndex: 'groupName',
    key: 'groupName'
  },
  {
    title: '所有者',
    dataIndex: 'owner',
    key: 'owner'
  },
  {
    title: '成员',
    dataIndex: 'members',
    key: 'members'
  },
  {
    title: '操作',
    key: 'action',
    width: 150
  }
]

const groupData = ref([
  {
    key: '1',
    groupName: 'o5Ljw6jYZ7 Team (1)',
    owner: 'Member',
    members: ''
  },
  {
    key: '2',
    groupName: '222 (1)',
    owner: 'Member',
    members: ''
  },
  {
    key: '3',
    groupName: '1111 (1)',
    owner: 'Member',
    members: ''
  }
])

const tableLoading = ref(false)

const getGroupList = async () => {
  tableLoading.value = true
  try {
    const res = await urlResquest.groupList()
    if (res.code === 200) {
      groupData.value = res.data.map(item => ({
        key: item.id,
        groupName: item.name,
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

const editGroup = (record) => {
  console.log('编辑群组:', record)
}

const manageMembers = (record) => {
  console.log('管理成员:', record)
}

const transferOwnership = (record) => {
  console.log('转让所有者:', record)
}

const deleteGroup = (record) => {
  console.log('删除群组:', record)
}
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
</style>
