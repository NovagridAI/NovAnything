<!--
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2023-12-26 14:49:41
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-06 10:09:33
 * @FilePath: front_end/src/components/OptionList.vue
 * @Description: 
-->
<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#5a47e5' } }">
    <div class="list-page">
      <div class="content">
        <div class="options">
          <a-button type="primary" class="to-chat" @click="goChat">
            <LeftOutlined class="back-icon" />
            <span>{{ home.conversation }}</span>
          </a-button>
          <p class="kb-name">
            <span class="name">
              {{ currentKbName.slice(0, 15) }}
            </span>
            <span class="id"> {{ home.knowledgeID }} {{ currentId }} </span>
          </p>
        </div>
        <div class="nav-info">
          <div class="navs">
            <div :class="['nav-item', 'nav-item-active']">
              {{ navIndex === 0 ? home.docSet : home.qaSet }}
            </div>
          </div>
          <div v-if="navIndex === 0" class="nav-progress">
            <UploadProgress :data-source="dataSource" />
          </div>
          <div class="handle-btn">

            <a-button v-if="navIndex === 0" danger class="clear-upload" @click="clearUpload">
              {{ home.clearAllFile }}
            </a-button>
            <a-button v-if="navIndex === 0" class="upload" @click="showFileUpload">
              {{ home.upload }}
            </a-button>
            <a-button v-if="navIndex === 0" class="add-link" @click="showUrlUpload">
              {{ home.addUrl }}
            </a-button>
            <a-button v-if="navIndex === 0" class="manage-members" @click="showManageMembers">
              <TeamOutlined />
              管理成员
            </a-button>
            <a-button v-if="navIndex === 1" class="upload" @click="showEditQaSet">
              {{ home.inputQa }}
            </a-button>
            <!-- <a-popover v-if="navIndex === 0" trigger="click" placement="top">
              <template #content>
                <TagsInput @confirm-tag="
                  newTags => {
                    tagConfirm('kb', currentId, newTags);
                  }
                " />
              </template>
              <a-button type="primary" style="margin: 0px 10px; height: 40px">所有文件一键添加tag</a-button>
            </a-popover>
            <a-popover v-if="navIndex === 0" trigger="click" placement="top">
              <template #content>
                <TagsInput @confirm-tag="
                  newTags => {
                    tagConfirm('fileBatch', [...selectedKeys.keys()], newTags);
                  }
                " />
              </template>
              <a-button type="primary" style="height: 40px">批量添加tag</a-button>
            </a-popover> -->
          </div>
        </div>
        <div class="table">
          <a-table v-if="navIndex === 0" :data-source="dataSource" :columns="columns" :pagination="kbPaginationConfig"
            :locale="{ emptyText: home.emptyText }" :hide-on-single-page="true" :show-size-changer="false"
            :row-selection="{ selectedRowKeys: [...selectedKeys.keys()], onSelect, onSelectAll }" @change="kbOnChange">
            <template #headerCell="{ column }">
              <!--            fileIdName-->
              <template v-if="column.key === 'status'">
                <span style="display: flex; align-items: center;">
                  {{ home.documentStatus }}
                  <a-tooltip color="#5a47e5">
                    <template #title>
                      {{ home.documentStatusNode }}
                    </template>
                    <QuestionCircleOutlined style="margin-left: 5px; font-size: 16px; color: #999;" />
                  </a-tooltip>
                </span>
              </template>
            </template>

            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'fileIdName'">
                <a-tooltip color="#fff" placement="topLeft">
                  <template #title>
                    <span style="color: #666; user-select: text">{{ record.fileIdName }}</span>
                  </template>
                  <span>{{ record.fileIdName }}</span>
                </a-tooltip>
              </template>
              <template v-else-if="column.key === 'fileTag'">
                <!-- <Tags v-if="record.status === 'green'" :tags="record.fileTag" @update:tags="
                  newTags => {
                    record.fileTag = newTags;
                  }
                " @confirm-tag="
                  newTags => {
                    tagConfirm('file', [record.fileId], newTags);
                  }
                " /> -->
              </template>
              <template v-else-if="column.key === 'status'">
                <div class="status-box">
                  <span class="icon-file-status">
                    <LoadingImg v-if="record.status === 'gray' || record.status === 'yellow'" class="file-status" />
                    <SvgIcon v-else class="file-status" :name="record.status === 'green' ? 'success' : 'error'" />
                  </span>
                  <span> {{ parseStatus(record.status) }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'remark'">
                <div v-if="typeof record.remark === 'string'">{{ record.remark }}</div>
                <div v-else>
                  <p v-for="(value, key) in record.remark" :key="key">
                    {{ `${key}: ${value}` }}
                  </p>
                </div>
              </template>
              <template v-else-if="column.key === 'options'">
                <a-popconfirm overlay-class-name="del-pop" placement="topRight" :title="common.deleteTitle"
                  :ok-text="common.confirm" :cancel-text="common.cancel" @confirm="confirm">
                  <!-- :disabled="record.status == 'gray' || record.status === 'yellow'" -->
                  <a-button type="text" class="delete-item" @click="deleteItem(record)">
                    {{ common.delete }}
                  </a-button>
                </a-popconfirm>
                <a-button type="text" class="view-item" :disabled="!(record.status === 'green')"
                  @click="viewItem(record)">
                  {{ common.view }}
                </a-button>
              </template>
            </template>
          </a-table>
          <a-table v-else :data-source="faqList" :columns="qaColumns" :locale="{ emptyText: home.emptyText }"
            :loading="loading" :pagination="paginationConfig" @change="onChange">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <div class="status-box">
                  <span class="icon-file-status">
                    <LoadingImg v-if="record.status === 'gray' || record.status === 'yellow'" class="file-status" />
                    <SvgIcon v-else class="file-status" :name="record.status === 'green' ? 'success' : 'error'" />
                  </span>
                  <span> {{ parseFaqStatus(record.status) }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'options'">
                <div class="options">
                  <a-button class="edit-item" type="link" :disabled="record.status !== 'green'"
                    @click="editQaItem(record)">
                    {{ bots.edit }}
                  </a-button>
                  <a-popconfirm overlay-class-name="qa-del-pop" placement="topRight" :title="home.deleteQaSetText"
                    :ok-text="common.confirm" :cancel-text="common.cancel" @confirm="qaConfirm">
                    <a-button class="delete-item" danger type="link" @click="deleteQaItem(record)">
                      {{ common.delete }}
                    </a-button>
                  </a-popconfirm>
                </div>
              </template>
            </template>
          </a-table>
        </div>
      </div>
    </div>
    <ChunkViewDialog :kb-id="currentId" :file-id="fileId" :file-name="fileIdName" />
    <FileUploadDialog :dialog-type="0" />
    <a-modal
      v-model:visible="manageMembersVisible"
      title="管理知识库成员权限"
      width="800px"
      @ok="handleManageMembersOk"
      @cancel="handleManageMembersCancel"
      :footer="null"
    >
      <div class="filter-container" style="margin-bottom: 16px">
        <a-select
          v-model:value="selectedSubjectType"
          style="width: 120px"
          @change="handleSubjectTypeChange"
        >
          <a-select-option value="user">用户</a-select-option>
          <a-select-option value="department">部门</a-select-option>
          <a-select-option value="group">用户组</a-select-option>
        </a-select>
      </div>
      
      <div class="members-container">
        <div class="members-column">
          <div class="column-header">可添加{{ subjectTypeLabel }}</div>
          <a-spin :spinning="membersLoading">
            <div class="members-list">
              <div 
                v-for="item in filteredAllSubjects" 
                :key="item.id"
                :class="['member-item', { disabled: item.disabled }]"
                @click="!item.disabled && addSubjectToKnowledgeBase(item.id)"
              >
                <div class="member-avatar">
                  <UserOutlined v-if="selectedSubjectType === 'user'" />
                  <TeamOutlined v-else-if="selectedSubjectType === 'department'" />
                  <UsergroupAddOutlined v-else-if="selectedSubjectType === 'group'" />
                </div>
                <div class="member-name">{{ item.name }}</div>
                <div class="member-action" v-if="!item.disabled">
                  <PlusOutlined />
                  <span class="action-text">添加</span>
                </div>
                <div class="member-status" v-if="item.disabled">
                  <a-tag color="default">已有权限</a-tag>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
        
        <div class="members-column">
          <div class="column-header">知识库{{ subjectTypeLabel }}</div>
          <a-spin :spinning="membersLoading">
            <div class="members-list">
              <div 
                v-for="item in filteredKnowledgeBaseSubjects" 
                :key="item.id"
                class="member-item"
                @click="removeSubjectFromKnowledgeBase(item.id)"
              >
                <div class="member-avatar">
                  <UserOutlined v-if="selectedSubjectType === 'user'" />
                  <TeamOutlined v-else-if="selectedSubjectType === 'department'" />
                  <UsergroupAddOutlined v-else-if="selectedSubjectType === 'group'" />
                </div>
                <div class="member-name">{{ item.name }}</div>
                <div class="member-action remove">
                  <MinusOutlined />
                  <span class="action-text">移除</span>
                </div>
              </div>
            </div>
          </a-spin>
        </div>
      </div>
    </a-modal>
  </a-config-provider>
</template>
<script lang="ts" setup>
import urlResquest from '@/services/urlConfig';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { useKnowledgeModal } from '@/store/useKnowledgeModal';
import { useChunkView } from '@/store/useChunkView';
import { useOptiionList } from '@/store/useOptiionList';
import { pageStatus } from '@/utils/enum';
import { resultControl } from '@/utils/utils';
import { message, Modal } from 'ant-design-vue';
import { getLanguage } from '@/language';
import LoadingImg from '@/components/LoadingImg.vue';
import UploadProgress from '@/components/UploadProgress.vue';
import ChunkViewDialog from '@/components/ChunkViewDialog.vue';
import FileUploadDialog from '@/components/FileUploadDialog.vue';
import { LeftOutlined, QuestionCircleOutlined, UserOutlined, PlusOutlined, MinusOutlined, TeamOutlined, UsergroupAddOutlined } from '@ant-design/icons-vue';
import Tags from '@/components/Tags.vue';
import TagsInput from '@/components/TagsInput.vue';

const { setDefault } = useKnowledgeBase();
const { currentKbName, currentId } = storeToRefs(useKnowledgeBase());
const { setModalVisible, setUrlModalVisible, setModalTitle } = useKnowledgeModal();
const { showChunkModel } = storeToRefs(useChunkView());
const {
  getDetails,
  setEditQaSet,
  setEditModalVisible,
  getFaqList,
  setFaqType,
  setPageNum,
  setKbPageNum,
} = useOptiionList();
const {
  dataSource,
  faqList,
  timer,
  faqTimer,
  total,
  pageNum,
  pageSize,
  loading,
  kbTotal,
  kbPageNum,
  kbPageSize,
} = storeToRefs(useOptiionList());

console.log(dataSource.value);
const home = getLanguage().home;
const common = getLanguage().common;
const bots = getLanguage().bots;

const navIndex = computed(() => computedKbType.value);

const computedKbType = computed(() => {
  if (currentId.value.endsWith('_FAQ')) {
    return 1;
  } else {
    return 0;
  }
});

const columns = [
  {
    title: home.documentId,
    dataIndex: 'fileId',
    key: 'fileId',
    width: '8%',
  },
  {
    title: home.documentName,
    dataIndex: 'fileIdName',
    key: 'fileIdName',
    width: '12%',
    ellipsis: true,
  },
  {
    title: home.documentTag,
    dataIndex: 'fileTag',
    key: 'fileTag',
    width: '12%',
  },
  {
    title: home.documentStatus,
    dataIndex: 'status',
    key: 'status',
    width: '10%',
    ellipsis: true,
  },
  {
    title: home.fileSize,
    dataIndex: 'bytes',
    key: 'bytes',
    width: '8%',
  },
  {
    title: home.contentLength,
    dataIndex: 'contentLength',
    key: 'contentLength',
    width: '10%',
  },
  {
    title: home.creationDate,
    dataIndex: 'createtime',
    key: 'createtime',
    width: '10%',
  },
  {
    title: home.remark,
    dataIndex: 'remark',
    key: 'remark',
    width: '15%',
  },
  {
    title: home.operate,
    key: 'options',
    width: '10%',
  },
];

const qaColumns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: '8%',
  },
  {
    title: home.question,
    dataIndex: 'question',
    key: 'question',
    width: '43%',
    ellipsis: true,
  },
  {
    title: home.status,
    dataIndex: 'status',
    key: 'status',
    width: '10%',
    ellipsis: true,
  },
  {
    title: home.characterCount,
    dataIndex: 'bytes',
    key: 'bytes',
    width: '10%',
  },
  {
    title: home.creationDate,
    dataIndex: 'createtime',
    key: 'createtime',
    width: '11%',
  },
  {
    title: home.operate,
    key: 'options',
    width: '10%',
  },
];

const tagConfirm = async (
  type: 'file' | 'fileBatch' | 'kb',
  id: string[] | string,
  newTags: Array<string>
) => {
  if (type === 'file') {
    console.log(type, id, newTags);
    await resultControl(
      await urlResquest.updateTags({
        tags: newTags,
        file_ids: id,
        is_replace: true,
      })
    );
    message.success('成功修改标签');
  } else if (type === 'fileBatch') {
    await resultControl(
      await urlResquest.updateTags({
        tags: newTags,
        file_ids: id,
        is_replace: false,
      })
    );
    message.success('成功批量添加标签');
    selectedKeys.value.clear();
    await getDetails();
  } else if (type === 'kb') {
    console.log(type, id, newTags);
    await resultControl(
      await urlResquest.updateTags({
        tags: newTags,
        kb_id: id,
        is_replace: false,
      })
    );
    message.success('成功为所有文件添加标签');
    await getDetails();
  }
};

const kbPaginationConfig = computed(() => ({
  current: kbPageNum.value,
  pageSize: kbPageSize.value,
  total: kbTotal.value,
  showSizeChanger: false,
  showTotal: total => `共 ${total} 条`,
}));

const paginationConfig = computed(() => ({
  current: pageNum.value,
  pageSize: pageSize.value,
  total: total.value,
  showSizeChanger: false,
  showTotal: total => `共 ${total} 条`,
}));

let optionItem: any = {};

const deleteItem = item => {
  optionItem = item;
};

const fileId = ref('');
const fileIdName = ref('');
const viewItem = async item => {
  fileId.value = item.fileId;
  fileIdName.value = item.fileIdName;
  showChunkModel.value = true;
};

const confirm = async () => {
  try {
    await resultControl(
      await urlResquest.deleteFile({ file_ids: [optionItem.fileId], kb_id: currentId.value })
    );
    message.success('删除成功');
    await getDetails();
    if (kbPageNum.value !== 1 && dataSource.value.length === 0) {
      kbPageNum.value -= 1;
      await getDetails();
    }
  } catch (e) {
    message.error(e.msg || '删除失败');
  }
};

let qaOptionItem: any = {};

const deleteQaItem = item => {
  qaOptionItem = item;
};

const qaConfirm = async () => {
  try {
    await resultControl(
      await urlResquest.deleteFile({
        kb_id: `${currentId.value}_FAQ`,
        file_ids: [qaOptionItem.faqId],
      })
    );
    message.success('删除成功');
    await getFaqList();
    if (pageNum.value !== 1 && faqList.value.length === 0) {
      pageNum.value -= 1;
      await getFaqList();
    }
  } catch (e) {
    message.error(e.msg || '删除失败');
  }
};

const editQaItem = item => {
  setFaqType('edit');
  setEditQaSet(item);
  setEditModalVisible(true);
};
const goChat = () => {
  setDefault(pageStatus.normal);
};

const showFileUpload = () => {
  setModalVisible(true);
  setModalTitle(home.upload);
};

const showUrlUpload = () => {
  setUrlModalVisible(true);
  setModalTitle(common.addUrl);
};

const showEditQaSet = () => {
  setFaqType('upload');
  setEditModalVisible(true);
};

const clearUpload = () => {
  Modal.confirm({
    title: home.clearAllFile,
    content: h('p', home.clearAllFileConfirm),
    centered: true,
    maskClosable: true,
    okText: common.confirm,
    okType: 'danger',
    async onOk() {
      try {
        await resultControl(await urlResquest.clearUpload({ status: 'gray', kb_ids: [] }));
        message.success('操作成功');
        getDetails();
      } catch (e) {
        message.error(e.msg || '操作失败');
      }
    },
  });
};

const parseStatus = status => {
  let str: string;
  switch (status) {
    case 'gray':
      str = common.inLine;
      break;
    case 'yellow':
      str = common.parsing;
      break;
    case 'green':
      str = common.succeeded;
      break;
    default:
      str = common.failed;
      break;
  }
  return str;
};

const parseFaqStatus = status => {
  let str = common.failed;
  switch (status) {
    case 'gray':
      str = common.uploadCompleted;
      break;
    case 'yellow':
      str = common.inLine;
      break;
    case 'green':
      str = common.learningCompleted;
      break;
    default:
      break;
  }
  return str;
};

const onChange = pagination => {
  const { current } = pagination;
  setPageNum(current);
  getFaqList();
};

const kbOnChange = pagination => {
  setKbPageNum(pagination.current);
  getDetails();
};

const selectedKeys = ref<Map<string, string>>(new Map());

const onSelect = (selectedRow: any) => {
  const key = selectedRow.fileId;
  const fileIdName = selectedRow.fileIdName;
  if (selectedKeys.value.has(key)) {
    selectedKeys.value.delete(key);
  } else {
    selectedKeys.value.set(key, fileIdName);
  }
};

const onSelectAll = (...args) => {
  const changeRows = args[2];
  changeRows.map(item => {
    const key = item.key;
    const fileIdName = item.fileIdName;
    if (selectedKeys.value.has(key)) {
      selectedKeys.value.delete(key);
    } else {
      selectedKeys.value.set(key, fileIdName);
    }
  });
};

watch(
  currentId,
  () => {
    setKbPageNum(1);
    setPageNum(1);
    getDetails();
  },
  {
    immediate: true,
  }
);

onBeforeUnmount(() => {
  clearTimeout(timer.value);
  clearTimeout(faqTimer.value);
  setKbPageNum(1);
  setPageNum(1);
});

// 添加成员管理相关的状态
const manageMembersVisible = ref(false);
const searchMember = ref('');
const membersLoading = ref(false);
const allSubjects = ref([]);

// 添加主体类型选择
const selectedSubjectType = ref('user');

// 根据选择的主体类型返回对应的标签文本
const subjectTypeLabel = computed(() => {
  switch (selectedSubjectType.value) {
    case 'user': return '成员';
    case 'department': return '部门';
    case 'group': return '用户组';
    default: return '成员';
  }
});

// 处理主体类型变更
const handleSubjectTypeChange = (value) => {
  selectedSubjectType.value = value;
  getSubjectList();
};

// 获取主体列表（用户/部门/用户组）
const getSubjectList = async () => {
  membersLoading.value = true;
  try {
    let res;
    
    switch (selectedSubjectType.value) {
      case 'user':
        res = await urlResquest.userList();
        if (res.code === 200) {
          allSubjects.value = res.data.map(user => ({
            id: user.user_id,
            name: user.user_name,
            permissions: user.permissions,
            role: user.role
          }));
        }
        break;
        
      case 'department':
        res = await urlResquest.departmentList();
        if (res.code === 200) {
          allSubjects.value = res.data.map(dept => ({
            id: dept.dept_id,
            name: dept.dept_name,
            permissions: dept.permissions || []
          }));
        }
        break;
        
      case 'group':
        res = await urlResquest.groupList();
        if (res.code === 200) {
          allSubjects.value = res.data.map(group => ({
            id: group.group_id,
            name: group.group_name,
            permissions: group.permissions || []
          }));
        }
        break;
    }
    
    if (res.code !== 200) {
      message.error(res.msg || `获取${subjectTypeLabel.value}列表失败`);
    }
  } catch (error) {
    console.error(`获取${subjectTypeLabel.value}列表失败:`, error);
    message.error(`获取${subjectTypeLabel.value}列表失败`);
  } finally {
    membersLoading.value = false;
  }
};

// 检查主体是否对指定知识库有权限
const checkSubjectHasPermission = (subject, kbId) => {
  if (!subject) return false;
  
  // 处理部门和用户组的情况，它们的权限是一个数组
  if (selectedSubjectType.value === 'department' || selectedSubjectType.value === 'group') {
    // 检查权限数组中是否包含当前知识库ID
    return Array.isArray(subject.permissions) && 
           subject.permissions.some(permission => permission.kb_id === kbId);
  }
  
  // 处理用户的情况，用户的权限是一个对象
  if (subject.permissions) {
    // 检查所有主体类型通用的权限字段
    const commonPermissionChecks = [
      // 检查直接访问权限
      subject.permissions.direct_access && 
      subject.permissions.direct_access.some(access => access.kb_id === kbId),
      
      // 检查拥有的知识库
      subject.permissions.owned_kbs && 
      subject.permissions.owned_kbs.some(kb => kb.kb_id === kbId),
      
      // 检查部门访问权限
      subject.permissions.department_access && 
      Array.isArray(subject.permissions.department_access) && 
      subject.permissions.department_access.some(access => access.kb_id === kbId),
      
      // 检查群组访问权限
      subject.permissions.group_access && 
      Array.isArray(subject.permissions.group_access) && 
      subject.permissions.group_access.some(access => access.kb_id === kbId)
    ];
    
    // 如果任何一个权限检查通过，则返回true
    return commonPermissionChecks.some(check => check === true);
  }
  
  return false;
};

// 过滤主体列表
const filteredAllSubjects = computed(() => {
  // 排除 superadmin 角色的用户
  let filteredList = allSubjects.value;
  
  if (selectedSubjectType.value === 'user') {
    filteredList = filteredList.filter(subject => subject.role !== 'superadmin');
  }
  
  return filteredList.filter(subject => {
    // 检查主体是否对当前知识库有权限
    const hasPermission = checkSubjectHasPermission(subject, currentId.value);
    
    subject.disabled = hasPermission;
    
    return !hasPermission;
  });
});

const filteredKnowledgeBaseSubjects = computed(() => {
  // 过滤出有权限的主体，排除 superadmin
  let filteredList = allSubjects.value;
  
  if (selectedSubjectType.value === 'user') {
    filteredList = filteredList.filter(subject => subject.role !== 'superadmin');
  }
  
  return filteredList.filter(subject => 
    checkSubjectHasPermission(subject, currentId.value)
  );
});

// 打开成员管理弹窗
const showManageMembers = () => {
  manageMembersVisible.value = true;
  getSubjectList();
};

// 添加主体到知识库
const addSubjectToKnowledgeBase = async (subjectId) => {
  const subject = allSubjects.value.find(s => s.id === subjectId);
  if (subject) {
    try {
      // 调用 grant_access API 添加权限
      const res = await urlResquest.grantKbAccess({ 
        kb_id: currentId.value,
        user_id: localStorage.getItem('userId'),
        subject_type: selectedSubjectType.value,
        subject_id: subjectId,
        permission_type: 'read' // 或其他权限类型
      });
      
      if (res.code === 200) {
        message.success(`已添加${subjectTypeLabel.value}: ${subject.name}`);
        // 重新获取列表以更新权限
        await getSubjectList();
      } else {
        message.error(res.msg || `添加${subjectTypeLabel.value}失败`);
      }
    } catch (error) {
      console.error(`添加${subjectTypeLabel.value}失败:`, error);
      message.error(`添加${subjectTypeLabel.value}失败`);
    }
  }
};

// 从知识库移除主体
const removeSubjectFromKnowledgeBase = async (subjectId) => {
  const subject = allSubjects.value.find(s => s.id === subjectId);
  if (subject) {
    try {
      // 调用 revoke_access API 移除权限
      const res = await urlResquest.revokeKbAccess({ 
        kb_id: currentId.value,
        user_id: localStorage.getItem('userId'),
        subject_type: selectedSubjectType.value,
        subject_id: subjectId
      });
      
      if (res.code === 200) {
        message.success(`已移除${subjectTypeLabel.value}: ${subject.name}`);
        // 重新获取列表以更新权限
        await getSubjectList();
      } else {
        message.error(res.msg || `移除${subjectTypeLabel.value}失败`);
      }
    } catch (error) {
      console.error(`移除${subjectTypeLabel.value}失败:`, error);
      message.error(`移除${subjectTypeLabel.value}失败`);
    }
  }
};

// 处理成员管理确认
const handleManageMembersOk = () => {
  manageMembersVisible.value = false;
};

// 处理成员管理取消
const handleManageMembersCancel = () => {
  manageMembersVisible.value = false;
};

// 在页面挂载时获取用户列表
onMounted(() => {
  // 保留原有的onMounted逻辑
  if (computedKbType.value === 0) {
    getDetails();
    clearInterval(timer.value);
    timer.value = setInterval(() => {
      getDetails();
    }, 5000);
  } else {
    getFaqList();
    clearInterval(faqTimer.value);
    faqTimer.value = setInterval(() => {
      getFaqList();
    }, 5000);
  }
  
  // 获取主体列表
  getSubjectList();
});
</script>

<style lang="scss" scoped>
.list-page {
  overflow: hidden;
  width: 100%;
  height: 100%;
  font-family: PingFang SC;

  .content {
    height: calc(100vh);
    padding: 24px 32px;
    background: $mainBgColor;
    border-radius: 12px 0 0 0;
  }
}

.options {
  display: flex;
  align-items: center;
  margin-bottom: 20px;

  .to-chat {
    display: flex;
    align-items: center;
    height: 40px;
    padding: 8px 20px;
    font-size: 16px;

    .back-icon {
      font-size: 16px;
    }

    span {
      font-size: 16px;
      font-weight: 500;
      color: #ffffff;
    }
  }

  .kb-name {
    margin: 0 20px 0 30px;
    font-size: 24px;
    font-weight: 500;
    color: #222222;

    .name {
      margin-right: 20px;
    }

    .id {
      font-size: 14px;
      font-weight: 400;
      color: #999;
    }
  }

  .kb-tag {
    flex: 1;
    display: flex;
    justify-content: flex-end;
  }
}

.nav-info {
  width: 100%;
  height: 40px;
  margin: 20px 0 14px 0;
  display: flex;
  justify-content: space-between;

  .navs {
    height: 40px;
    padding: 4px;
    border-radius: 8px;
    background: $secondaryBgColor;
    display: flex;

    .nav-item {
      min-width: 100px;
      padding: 0 20px;
      height: 32px;
      font-size: 16px;
      color: #666666;
      border-radius: 6px;
      text-align: center;
      line-height: 32px;
    }

    .nav-item-active {
      background: #fff;
      font-weight: 500;
      color: $baseColor;
    }
  }

  .nav-progress {
    width: 40%;
    margin: 0 10px 50px;
    display: flex;
    align-items: center;
  }

  .handle-btn {
    display: flex;

    .clear-upload {
      height: 40px;
      margin-right: 10px;
    }

    .upload {
      cursor: pointer;
      height: 40px;
      padding: 8px 20px;
      border-radius: 4px;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;
      color: #ffffff;
      border: 1px solid $baseColor;
      color: $baseColor;

      &:hover {
        border: 1px solid lighten($baseColor, 20%);
        color: lighten($baseColor, 20%);
      }
    }

    .add-link {
      cursor: pointer;
      height: 40px;
      margin-left: 16px;
      padding: 8px 20px;
      border-radius: 4px;
      background: #ffffff;
      border: 1px solid $baseColor;
      color: $baseColor;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;

      &:hover {
        border: 1px solid lighten($baseColor, 20%);
        color: lighten($baseColor, 20%);
      }
    }

    .manage-members {
      cursor: pointer;
      height: 40px;
      margin-left: 16px;
      padding: 8px 20px;
      border-radius: 4px;
      background: #ffffff;
      border: 1px solid $baseColor;
      color: $baseColor;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;

      &:hover {
        border: 1px solid lighten($baseColor, 20%);
        color: lighten($baseColor, 20%);
      }
    }
  }
}

.table {
  height: 100%;
  margin-bottom: 32px;
  overflow: auto;
  border-radius: 12px;
  background-color: #fff;

  &::-webkit-scrollbar {
    width: 0;
  }

  .options {
    width: 80px;
    display: flex;
    justify-content: space-between;
  }

  .delete-item {
    padding: 2px;
    font-size: 14px;
    font-weight: normal;
    line-height: 22px;
    margin-right: 5px;
    color: #ff524c;
  }

  .view-item {
    padding: 2px;
    font-size: 14px;
    font-weight: normal;
    line-height: 22px;
    margin-right: 5px;
    color: #4d71ff;
  }

  .edit-item {
    padding: 0;
  }

  .file-status {
    width: 16px;
    height: 16px;
  }

  .status-box {
    display: flex;
    align-items: center;

    .icon-file-status {
      display: flex;
      align-items: center;
    }

    span {
      display: block;

      margin-right: 8px;

      svg {
        width: 16px;
        height: 16px;
      }
    }
  }
}

:deep(.ant-table-wrapper .ant-table-thead > tr > th) {
  font-size: 14px !important;
  font-weight: 500 !important;
  line-height: 24px !important;
  padding: 15px 0 15px 36px !important;
  color: #222222 !important;
  background-color: lighten($baseColor, 45%);

  .small {
    font-size: 12px !important;
  }

  &:before {
    width: 0 !important;
  }
}

:deep(.ant-table-tbody > tr > td) {
  font-size: 14px;
  font-weight: normal;
  line-height: 22px;
  color: #666666;
  background-color: #fff;
  padding: 20px 0 20px 36px !important;
  border: 0 !important;
  box-shadow: inset 0px -1px 0px 0px rgba(0, 0, 0, 0.05);

  &:hover {
    background-color: rgba(233, 237, 247, 0.3);
  }
}

:deep(.ant-pagination) {
  margin: 16px 20px !important;
}

:deep(.ant-pagination-item) {
  box-sizing: border-box !important;
  border: 1px solid #dde2ec !important;
}

:deep(.ant-pagination-item-active) {
  background: #5a47e5 !important;
  color: #fff !important;

  a {
    color: #fff !important;
  }
}

:deep(.options > .ant-btn) {
  height: auto;
}

:deep(.ant-btn-link) {
  color: #5a47e5;
}

:deep(.ant-btn-link:disabled) {
  color: rgba(0, 0, 0, 0.25);
}

:deep(.ant-table-empty .ant-table-placeholder .ant-table-cell) {
  color: #999999 !important;
}

/* 修改成员管理弹窗样式 */
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
  flex-shrink: 0; /* 防止标题被压缩 */
  font-size: 16px; /* 增加标题文字大小 */
}

.members-list {
  flex: 1;
  overflow-y: auto; /* 允许垂直滚动 */
  padding: 8px;
  max-height: calc(400px - 45px); /* 减去标题高度 */
  scrollbar-width: thin; /* Firefox */
  scrollbar-color: rgba(0, 0, 0, 0.3) transparent; /* Firefox */
}

/* 自定义滚动条样式 (Webkit浏览器) */
.members-list::-webkit-scrollbar {
  width: 6px;
}

.members-list::-webkit-scrollbar-track {
  background: transparent;
}

.members-list::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 3px;
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
  font-size: 16px; /* 增加成员项文字大小 */
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
  font-size: 16px; /* 增加成员名称文字大小 */
}

.member-action {
  display: flex;
  align-items: center;
  color: #1890ff;
  font-size: 16px; /* 增加操作按钮文字大小 */
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
  font-size: 16px; /* 增加操作文字大小 */
}

.member-status {
  font-size: 16px; /* 增加状态文字大小 */
}

.manage-members {
  cursor: pointer;
  height: 40px;
  margin-left: 16px;
  padding: 8px 20px;
  border-radius: 4px;
  background: #ffffff;
  border: 1px solid $baseColor;
  color: $baseColor;
  font-size: 16px;
  font-weight: 500;
  line-height: 24px;

  &:hover {
    border: 1px solid lighten($baseColor, 20%);
    color: lighten($baseColor, 20%);
  }
}

/* 修改按钮文字大小 */
.filter-container {
  .ant-select {
    font-size: 16px;
  }
}

/* 确保下拉菜单中的文字也是16px */
:deep(.ant-select-dropdown) {
  .ant-select-item {
    font-size: 16px;
  }
}

/* 确保弹窗标题也是16px */
:deep(.ant-modal-title) {
  font-size: 18px; /* 弹窗标题稍大一点 */
}
</style>

<style lang="scss">
.del-pop {
  margin-right: 10px;

  .ant-popover-content {
    .ant-btn-default {
      padding: 1px 8px;
      border: 1px solid rgba(0, 0, 0, 0.15) !important;

      span {
        line-height: 1;
      }
    }

    .ant-popover-inner {
      padding: 12px 16px;
      transform: translateX(44px);
    }

    .ant-popconfirm-message-icon {
      svg {
        font-size: 16px;
      }
    }

    .ant-popconfirm-message-title {
      width: 168px;
      height: 36px;
      line-height: 36px;
    }

    .ant-popconfirm-message {
      align-items: center !important;
    }
  }
}

.qa-del-pop {
  .ant-popover-inner {
    padding-top: 20px;
    height: 100px;
  }

  .ant-popconfirm-buttons {
    margin-top: 16px;
  }

  .ant-btn-sm {
    width: 60px;
  }

  .ant-btn-sm.ant-btn-loading {
    width: auto !important;
  }
}
</style>
