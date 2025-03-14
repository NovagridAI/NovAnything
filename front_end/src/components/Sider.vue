<!--
 * @Author: 祝占朋 wb.zhuzp01@rd.netease.com
 * @Date: 2023-11-01 14:57:33
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-02 16:52:03
 * @FilePath: front_end/src/components/Sider.vue
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
<template>
  <div class="sider">
    <div class="logo">NovAnything</div>
    <div class="header-navs">
      <div v-for="item in filteredNavList" :key="item.name"
        :class="['nav-item', navIndex === item.value ? 'nav-item-active' : '']" @click="setNavIdx(item.value)">
        <!--        <div :class="['item-icon', item.value === 0 ? 'knowledge-icon' : 'bot-icon']"></div>-->
        <div :class="['item-icon']">
          <component :is="item.icon" />
        </div>
        <div class="nav-item-name">{{ item.name }}</div>
      </div>
    </div>
    <div v-if="navIndex === 0" class="knowledge">
      <div class="add-btn">
        <!-- <AddInput @add="addKb" /> -->
        <!-- <AddInput /> -->
      </div>
      <!-- <div class="content">
        <SiderCard :list="knowledgeBaseList"></SiderCard>
      </div> -->
      <!-- <div class="bottom-btn-box">
        <a-button class="manage" @click="goManage">
          <template #icon>
            <img class="folder" src="../assets/home/icon-folder.png" alt="图标" />
          </template>
知识库管理</a-button>
</div> -->
    </div>
    <div v-else-if="navIndex === 1" class="bots">
      <div class="bots-tab" @click="changePage('/bots')">{{ getLanguage().bots.myBots }}</div>
      <NewBotsDialog />
      <SelectKnowledgeDialog />
      <CopyUrlDialog />
    </div>
    <div v-else-if="navIndex === 2" class="quick-start" style="display: none;">
      <div class="content">
        <div :class="['card-new', chatId === null ? 'active' : '', showLoading ? 'disabled' : '']"
          @click="quickClickHandle(0)">
          <PlusOutlined class="plus-icon" />
          {{ getLanguage().home.newConversationQuick }}
        </div>
        <SiderCardItem v-for="item of historyList" :key="item.historyId" :card-data="item"
          @click="quickClickHandle(1, item)" />
      </div>
    </div>
    <div class="account">
      <div class="logout-btn" @click="handleLogout">
        <LogoutOutlined class="logout-icon" />
        {{ '退出登录' }}
      </div>
    </div>
    <ChatSourceDialog />
    <DeleteModal />
    <UrlUploadDialog />
    <EditQaSetDialog />
  </div>
</template>
<script lang="ts" setup>
// import dayjs from 'dayjs';
import AddInput from '@/components/AddInput.vue';
import SiderCard from '@/components/SiderCard.vue';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
// import FileUploadDialog from '@/components/FileUploadDialog.vue';
import UrlUploadDialog from '@/components/UrlUploadDialog.vue';
import DeleteModal from '@/components/DeleteModal.vue';
import EditQaSetDialog from '@/components/EditQaSetDialog.vue';
import NewBotsDialog from '@/components/Bots/NewBotsDialog.vue';
import SelectKnowledgeDialog from '@/components/Bots/SelectKnowledgeDialog.vue';
import CopyUrlDialog from '@/components/Bots/CopyUrlDialog.vue';
import ChatSourceDialog from '@/components/ChatSourceDialog.vue';
import { useHeader } from '@/store/useHeader';
import routeController from '@/controller/router';
import SiderCardItem from '@/components/SiderCardItem.vue';
import { IHistoryList, useQuickStart } from '@/store/useQuickStart';
import SvgIcon from '@/components/SvgIcon.vue';
import { getLanguage } from '@/language';
// import { message } from 'ant-design-vue';
// import { useKnowledgeModal } from '@/store/useKnowledgeModal';
import { resultControl } from '@/utils/utils';
import urlResquest from '@/services/urlConfig';
import { IChatItemInfo, IFileListItem } from '@/utils/types';
import { useUploadFiles } from '@/store/useUploadFiles';
import { FolderOutlined, ThunderboltOutlined, RobotOutlined, UserOutlined, PlusOutlined, LogoutOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import Cookies from 'js-cookie';
import { useUser } from '@/store/useUser';
// import urlResquest from '@/services/urlConfig';
// import { pageStatus } from '@/utils/enum';
// import { resultControl } from '@/utils/utils';

// const { setModalVisible } = useKnowledgeModal();
// const { modalVisible } = storeToRefs(useKnowledgeModal());

// const router = useRouter();
// const { getList, setCurrentId, setCurrentKbName, setDefault } = useKnowledgeBase();
// const { knowledgeBaseList, selectList } = storeToRefs(useKnowledgeBase());
const { knowledgeBaseList, currentKbName } = storeToRefs(useKnowledgeBase());
const { historyList, showLoading, chatId, QA_List, kbId } = storeToRefs(useQuickStart());
const { getChatById, addHistoryList, updateHistoryList, addChatList, addFileToBeSendList } =
  useQuickStart();
const { uploadFileListQuick } = storeToRefs(useUploadFiles());
const { initUploadFileListQuick } = useUploadFiles();
const { navIndex } = storeToRefs(useHeader());
const { changePage } = routeController();
const { setNavIndex } = useHeader();
const { userInfo } = useUser();

const navList = [
  {
    name: getLanguage().header.quickStart,
    value: 2,
    icon: markRaw(ThunderboltOutlined)
  },
  {
    name: getLanguage().header.knowledge,
    value: 0,
    icon: markRaw(FolderOutlined)
  },
  // {
  //   name: 'Bots',
  //   value: 1,
  //   icon: markRaw(RobotOutlined)
  // },
  {
    name: getLanguage().header.account,
    value: 3,
    icon: markRaw(UserOutlined)
  },
];

// 添加这段代码，根据用户角色过滤导航项
const filteredNavList = computed(() => {
  const userRole = (userInfo as any).role;
  // 如果不是管理员，则过滤掉用户管理选项
  if (userRole !== 'admin' && userRole !== 'superadmin') {
    return navList.filter(item => item.value !== 3);
  }
  return navList;
});

// header的item-icon选择
const iconMap = new Map([
  [0, 'knowledge-icon'],
  [1, 'bot-icon'],
  [2, 'quick-icon'],
]);

const getIcon = itemValue => {
  return iconMap.get(itemValue);
};

const setNavIdx = value => {
  if (navIndex.value === value) {
    return;
  }
  setNavIndex(value);
  if (value === 0) {
    changePage('/home');
  } else if (value === 1) {
    changePage('/bots');
  } else if (value === 2) {
    changePage('/quickstart');
  } else if (value === 3) {
    changePage('/account');
  }
};


// 快速开始逻辑
function addQuestion(q, fileDataList: IFileListItem[]) {
  QA_List.value.push({
    question: q,
    type: 'user',
    fileDataList: fileDataList,
  });
  // scrollBottom();
}

function addAnswer(
  question: string,
  itemInfo: IChatItemInfo,
  answer: string,
  picList,
  qaId,
  source
) {
  QA_List.value.push({
    answer,
    itemInfo,
    question,
    type: 'ai',
    qaId,
    copied: false,
    like: false,
    unlike: false,
    source: source ? source : [],
    showTools: true,
    picList,
  });
}

// 快速开始的：0新建对话, 1选中对话
const quickClickHandle = async (type: 0 | 1, cardData?: IHistoryList) => {
  if (showLoading.value) return;
  // 切换对话的时候保存当前文件的上传情况
  if (uploadFileListQuick.value.length) {
    addFileToBeSendList(chatId.value, [...uploadFileListQuick.value]);
    initUploadFileListQuick();
  }
  if (type === 0) {
    // 新建对话，需要创建对话（知识库）并跳转到新对话
    const res: any = await resultControl(
      await urlResquest.createKb({ kb_name: '未命名对话', is_quick: true })
    );
    kbId.value = res.kb_id;
    QA_List.value = [];
    // 当前对话id为新建的historyId
    chatId.value = addHistoryList('未命名对话');
    updateHistoryList('未命名对话', chatId.value, kbId.value);
    // 更新最大的chatList
    addChatList(chatId.value, QA_List.value);
  } else if (type === 1) {
    if (chatId.value === cardData.historyId) return;
    chatId.value = cardData.historyId;
    QA_List.value = [];
    kbId.value = cardData.kbId;
    currentKbName.value = cardData.title;
    nextTick(() => {
      const chat = getChatById(chatId.value);
      chat.list.forEach(item => {
        if (item.type === 'user') {
          addQuestion(item.question, item.fileDataList);
        } else if (item.type === 'ai') {
          addAnswer(
            item.question,
            item.itemInfo,
            item.answer,
            item.picList,
            item.qaId,
            item.source
          );
        }
      });
    });
  }
};

// 退出登录
const handleLogout = () => {
  // 清除token
  localStorage.removeItem('token');
  Cookies.remove('token');
  localStorage.clear();
  // 可能需要清除其他用户相关信息
  message.success('退出成功');
  // 跳转到登录页面
  changePage('/login');
};

onUnmounted(() => {
  QA_List.value = [];
  chatId.value = null;
  kbId.value = '';
});
</script>

<style lang="scss" scoped>
.sider {
  .logo {
    cursor: pointer;
    // width: 100%;
    // height: 50px;
    // background: $mainBgColor;
    // border-radius: 12px;
    // text-align: center;
    // line-height: 50px;
    margin: 12px 16px 10px 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid $lineColor;
    background-image: linear-gradient(to right, #3b82f6 , #4f46e5);
    color: transparent;
    background-clip: text;
    // color: linear-gradient(to right, #7b5ef2, #c383fe);
    font-size: 22px;
    font-weight: 700;
    // color: $primaryColor;
  }

  .header-navs {
    // height: 50px;
    // margin: 12px 24px;
    display: flex;
    flex-direction: column;
    // justify-content: flex-start;
    align-items: left;
    background: $mainBgColor;
    // border-radius: 12px;
    padding: 8px 12px;

    .nav-item-active {
      color: #fff;

      // .bot-icon {
      //   background-image: url('@/assets/header/bots-active-icon.png');
      // }

      .knowledge-icon {
        background-image: url('@/assets/header/knowledge-active-icon.png');
      }

      .quick-icon {
        background-image: url('@/assets/header/quick-active-icon.png');
      }
    }

    .nav-item {
      // height: 36px;
      padding: 8px 12px;
      margin-bottom: 8px;
      // margin: 5px 10px;
      display: flex;
      // flex-direction: column;
      align-items: center;
      // justify-content: center;
      font-size: 14px;
      cursor: pointer;
      color: $textColor;
      border-radius: 8px;
      transition: all 0.3s ease;

      &:hover:not(.nav-item-active) {
        background: $hoverBgColor;
        color: $textTitleColor;
        // box-shadow: 0 1px 4px rgba(123, 94, 242, 0.2);
      }

      span {
        white-space: nowrap;
        font-weight: 500;
      }

      .item-icon {
        line-height: 18px;
        font-size: 18px;
        background-size: contain;
        background-position: center;
      }

      .nav-item-name {
        margin-left: 8px;
      }
    }

    .nav-item-active {
      background: $secondaryBgColor;
      color: $textTitleColor;
      font-weight: 700;
      // box-shadow: 0 2px 8px rgba(123, 94, 242, 0.2);

      .item-icon {
        font-weight: 700;
        opacity: 1;
      }

      // &:hover {
      //   background: #fff;
      // color: $title1;
      // box-shadow: 0 2px 8px rgba(123, 94, 242, 0.2);
      // }
    }
  }

  display: flex;
  flex-direction: column;
  width: 220px;
  height: calc(100vh);
  background-color: $mainBgColor;

  .knowledge {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .quick-start {
    height: 100%;
    display: flex;
    flex-direction: column;

    .card-new {
      width: 190px;
      height: 36px;
      margin: 0 auto 16px;
      border-radius: 8px;
      display: flex;
      padding: 8px 12px;
      // justify-content: center;
      align-items: center;
      font-size: 14px;
      overflow: hidden;
      background: #333647;
      cursor: pointer;
      color: #fff;

      .plus-icon {
        margin-right: 8px;
      }
    }

    .active {
      background: $primaryColor;
    }

    .disabled {
      cursor: not-allowed !important;

      span {
        cursor: not-allowed !important;
      }

      .close-icon {
        cursor: not-allowed !important;
      }

      .close-icon:hover {
        background: transparent !important;
      }
    }
  }

  .account {
    padding: 20px;
    margin-top: auto;
    
    .logout-btn {
      display: flex;
      align-items: center;
      padding: 10px 15px;
      background: rgba(220, 38, 38, 0.1);
      border-radius: 8px;
      color: #dc2626;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        background: rgba(220, 38, 38, 0.2);
      }
      
      .logout-icon {
        margin-right: 8px;
        font-size: 16px;
        color: #dc2626;
      }
    }
  }

  .add-btn {
    margin: 14px 12px 20px 12px;
    width: calc(100% - 24px);

    :deep(.ant-input-affix-wrapper) {
      padding: 4px;
      border: 1px solid #373b4d;
      background: linear-gradient(0deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.2)), #26293b;
    }

    :deep(.ant-input) {
      color: #ffffff;
      padding-left: 4px;
      background: linear-gradient(0deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.2)), #26293b;

      &::placeholder {
        color: #999999;
      }
    }
  }

  .bottom-btn-box {
    position: fixed;
    width: 280px;
    bottom: 29px;

    .manage {
      width: calc(100% - 40px);
      margin: 0 20px;
      height: 40px;
    }

    .folder {
      width: 16px;
      height: 16px;
      margin-right: 8px;
    }

    :deep(.ant-btn) {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #4d71ff !important;
      background: rgba(255, 255, 255, 0.7) !important;
      border: 1px solid #ffffff !important;
    }
  }

  .bots {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 12px;

    .bots-tab {
      width: 232px;
      height: 46px;
      border-radius: 8px;
      // background: #7261e9;
      font-family: PingFang SC;
      font-size: 16px;
      font-weight: 500;
      text-align: center;
      line-height: 46px;
      color: #fff;
      cursor: pointer;
    }
  }
}

.content {
  flex: 1;
  margin-bottom: 20px;
  margin-top: 20px;
  overflow-y: scroll;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}
</style>
