<template>
  <ChatHeaderMenu />
  <!-- <HistoryChat
    :observer="observer"
    :observe-dom="observeDom"
    :qa-observe-dom="qaObserveDom"
    :qa-observer="qaObserver"
    :show-loading="showLoading"
    @scrollBottom="scrollBottom"
    @setObserveDom="setObserveDom"
    @setQaObserverDom="setQaObserverDom"
    @clearHistory="clearHistory"
  /> -->
  <div class="container showSider">
    <div class="my-page">
      <div id="chat" ref="chatContainer" class="chat showSider">
        <ul id="chat-ul" ref="scrollDom">
          <li v-for="(item, index) in QA_List" :key="index">
            <div v-if="item.type === 'user'" class="user" 
                 @mouseenter="handleUserMessageHover(index, true)" 
                 @mouseleave="handleUserMessageHover(index, false)">
              <img class="avatar" src="../assets/home/avatar.png" alt="头像" />
              <div class="user-message-container">
                <!-- 正常显示模式 -->
                <p v-if="!item.isEditing" class="question-text" style="white-space: pre-wrap;">{{ item.question }}</p>
                
                <!-- 编辑模式 -->
                <div v-if="item.isEditing" class="edit-mode">
                  <textarea 
                    v-model="item.editingText" 
                    placeholder="编辑消息内容..."
                    class="edit-textarea-native"
                    @keydown="handleEditKeydown($event, index)"
                    ref="editTextarea"
                  ></textarea>
                  <div class="edit-actions">
                    <arco-button size="small" @click="cancelEdit(index)">取消</arco-button>
                    <arco-button size="small" type="primary" @click="confirmEdit(index)">重新发送</arco-button>
                  </div>
                </div>
                
                <!-- 编辑按钮 -->
                <div v-if="item.showEditIcon && !item.isEditing && !showLoading" 
                     class="edit-icon" 
                     @click="startEdit(index)">
                  <SvgIcon name="edit" />
                </div>
              </div>
            </div>
            <div v-else class="ai">
              <img class="avatar" src="../assets/home/novLogo.png" alt="头像" />
              <div class="ai-content">
                <div class="ai-right">
                  <p class="question-text" :class="[
                    !item.source.length && !item?.picList?.length ? 'change-radius' : '',
                    item.showTools ? '' : 'flashing',
                  ]">
                    <HighLightMarkDown :content="item.answer.toString()" />
                    <ChatInfoPanel v-if="Object.keys(item?.itemInfo?.tokenInfo || {}).length"
                      :chat-item-info="item.itemInfo" />
                  </p>
                  <template v-if="item.source.length">
                    <div :class="[
                      'source-total',
                      !showSourceIdxs.includes(index) ? 'source-total-last' : '',
                    ]">
                      <span v-if="language === 'zh'">
                        找到了{{ item.source.length }}个信息来源：
                      </span>
                      <span v-else> Found {{ item.source.length }} source of information </span>
                      <SvgIcon v-show="!showSourceIdxs.includes(index)" name="down" @click="showSourceList(index)" />
                      <SvgIcon v-show="showSourceIdxs.includes(index)" name="up" @click="hideSourceList(index)" />
                    </div>
                    <div v-show="showSourceIdxs.includes(index)" class="source-list">
                      <div v-for="(sourceItem, sourceIndex) in item.source" :key="sourceIndex" class="data-source">
                        <p v-show="sourceItem.file_name" class="control">
                          <span class="tips">{{ common.dataSource }}{{ sourceIndex + 1 }}:</span>
                          <a v-if="sourceItem.file_url.startsWith('http')" :href="sourceItem.file_url" target="_blank">
                            {{ sourceItem.file_name }}
                          </a>
                          <span v-else :class="[
                            'file',
                            checkFileType(sourceItem.file_name) ? 'filename-active' : '',
                          ]" @click="handleChatSource(sourceItem)">
                            {{ sourceItem.file_name }}
                          </span>
                          <SvgIcon v-show="sourceItem.showDetailDataSource" name="iconup"
                            @click="hideDetail(item, sourceIndex)" />
                          <SvgIcon v-show="!sourceItem.showDetailDataSource" name="icondown"
                            @click="showDetail(item, sourceIndex)" />
                        </p>
                        <Transition name="sourceitem">
                          <div v-show="sourceItem.showDetailDataSource" class="source-content">
                            <!--                            <p v-html="sourceItem.content?.replaceAll('\n', '<br/>')"></p>-->
                            <HighLightMarkDown :content="sourceItem.content" />
                            <p class="score">
                              <span class="tips">{{ common.correlation }}</span>
                              {{ sourceItem.score }}
                            </p>
                          </div>
                        </Transition>
                      </div>
                    </div>
                  </template>
                  <div v-if="item.showTools" class="feed-back">
                    <div class="reload-box" @click="reAnswer(item)">
                      <SvgIcon name="reload"></SvgIcon>
                      <span class="reload-text">{{ common.regenerate }}</span>
                    </div>
                    <div class="tools">
                      <SvgIcon :style="{
                        color: item.copied ? '#4D71FF' : '',
                      }" name="copy" @click="myCopy(item)"></SvgIcon>
                      <!-- <SvgIcon :style="{
                        color: item.like ? '#4D71FF' : '',
                      }" name="like" @click="like(item, $event)"></SvgIcon>
                      <SvgIcon :style="{
                        color: item.unlike ? '#4D71FF' : '',
                      }" name="unlike" @click="unlike(item)"></SvgIcon> -->
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </li>
          <div v-if="thinkingLoading" class="loading-dots">
            <img class="avatar" src="../assets/home/novLogo.png" alt="头像" />
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
        </ul>
      </div>
      <div v-if="showLoading" class="stop-btn">
        <a-button @click="stopChat">
          <template #icon>
            <SvgIcon name="stop" :class="showLoading ? 'loading' : ''"></SvgIcon>
          </template>
          {{ common.stop }}
        </a-button>
      </div>
      <TempFileContainer />
      <div class="question-container">
        <div class="icon-container">
          <keep-alive>
            <ChatAdvanceSettings v-if="true" />
          </keep-alive>
          <icon-upload class="action-icon" @click="openFileUpload" />
        </div>
        <div class="question-container-button">
          <arco-button type="primary" :disabled="showLoading" @click="send">
            <icon-send class="action-icon" style="margin-right: 8px;" /> 发送消息
          </arco-button>
        </div>
        <arco-textarea v-model="question" placeholder="输入聊天内容..." allow-clear :auto-size="{ minRows: 6 }"
          :resize="false" class="full-width-textarea" style="padding-top: 58px;" @keydown="handleKeydown" />
      </div>
      <div class="question-box">
        <div class="question">

          <!-- <ChatTextarea v-model:input-value="question" :options="mentionOptions" @send="send">
            <a-popover>
              <template #content>
                {{ selectList.length ? common.chatShare : common.chatShareNoChatId }}
              </template>
              <span
                :class="[
                  'question-icon',
                  showLoading || !selectList.length ? 'isPreventClick' : '',
                ]"
                @click="shareChat"
              >
                <SvgIcon name="chat-share" />
              </span>
            </a-popover>
            <a-popover placement="topLeft">
              <template #content>{{ common.chatToPic }}</template>
              <span
                :class="['question-icon', showLoading ? 'isPreventClick' : '']"
                @click="downloadChat"
              >
                <SvgIcon name="chat-download" />
              </span>
            </a-popover>
            <a-popover>
              <template #content>{{ common.clearChat }}</template>
              <span
                :class="['question-icon', showLoading ? 'isPreventClick' : '']"
                @click="deleteChat"
              >
                <SvgIcon name="chat-delete" />
              </span>
            </a-popover>
            <a-popover>
              <template #content>{{ common.modelSettingTitle }}</template>
              <span class="question-icon" @click="handleModalChange(true)">
                <SvgIcon name="chat-setting" />
              </span>
            </a-popover>
            <a-button type="primary" :disabled="showLoading" shape="circle" @click="send">
              <SvgIcon name="sendplane" />
            </a-button>
          </ChatTextarea> -->
        </div>
      </div>
    </div>
    <ConversationHistory ref="conversationHistoryRef" @new-chat="newChat" />
    <div class="scroll-btn-div">
      <img class="avatar" src="@/assets/home/scroll-down.png" alt="滑到底部" @click="scrollBottom" />
    </div>
  </div>
  <ChatSettingDialog ref="chatSettingForDialogRef" />
  <DefaultModal :content="content" :confirm-loading="confirmLoading" @ok="confirm" />
  <FileUploadDialog ref="fileUploadDialogRef" :dialog-type="2" :temporary-id="tempId" />
  <CopyUrlDialog />
</template>
<script lang="ts" setup>
import { apiBase } from '@/services';
import { IChatItem } from '@/utils/types';
import { throttle } from '@/utils/utils';
import { useClipboard } from '@vueuse/core';
import SvgIcon from './SvgIcon.vue';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useChat } from '@/store/useChat';
import { useChatSource } from '@/store/useChatSource';
import { Typewriter } from '@/utils/typewriter';
import DefaultModal from './DefaultModal.vue';
import html2canvas from 'html2canvas';
import urlResquest, { userId, userPhone } from '@/services/urlConfig';
import { getLanguage } from '@/language';
import { useLanguage } from '@/store/useLanguage';
import { ChatInfoClass, formatTimestamp, resultControl } from '@/utils/utils';
import ChatSettingDialog from '@/components/ChatSettingDialog.vue';
import HistoryChat from '@/components/Home/HistoryChat.vue';
import { useHomeChat } from '@/store/useHomeChat';
import HighLightMarkDown from '@/components/HighLightMarkDown.vue';
import { useChatSetting } from '@/store/useChatSetting';
import ChatInfoPanel from '@/components/ChatInfoPanel.vue';
import { useBots } from '@/store/useBots';
import CopyUrlDialog from '@/components/Bots/CopyUrlDialog.vue';
import ChatTextarea from '@/components/ChatTextarea.vue';
import { IconUpload, IconPlus, IconSend } from '@arco-design/web-vue/es/icon';
import Cookies from 'js-cookie'
import ChatAdvanceSettings from '@/components/ChatAdvanceSettings.vue';
import ChatHeaderMenu from '@/components/ChatHeaderMenu.vue';
import ConversationHistory from '@/components/ConversationHistory.vue';
import { useAdvanceSettings } from '@/store/useAdvanceSettings';
import { useKnowledgeModal } from '@/store/useKnowledgeModal';
import FileUploadDialog from '@/components/FileUploadDialog.vue';
import { useOptiionList } from '@/store/useOptiionList';
import { Message } from '@arco-design/web-vue';
import { useUser } from '@/store/useUser';
import { useRouter } from 'vue-router';
import { nextTick } from 'vue';

const common = getLanguage().common;

const typewriter = new Typewriter((str: string) => {
  if (str) {
    QA_List.value[QA_List.value.length - 1].answer += str || '';
  }
});

const { selectList, knowledgeBaseList, tempId } = storeToRefs(useKnowledgeBase());
const { setTempId } = useKnowledgeBase();
const { QA_List, chatId, pageId, qaPageId, historyList, currentQaId } = storeToRefs(useHomeChat());
const { chatSettingFormActive } = storeToRefs(useChatSetting());
const { setAllChatSettingConfigured } = useChatSetting();
const { userSettings } = storeToRefs(useAdvanceSettings());
const { userInfo } = storeToRefs(useUser());
const router = useRouter();
const { copy } = useClipboard();
const { addHistoryList, updateHistoryList, addChatList, clearChatList, setCurrentQaId } = useHomeChat();
const { setChatSourceVisible, setSourceType, setSourceUrl, setTextContent } = useChatSource();
const { setCopyUrlVisible, setWebUrl } = useBots();
const { language } = storeToRefs(useLanguage());
const { setModalVisible } = useKnowledgeModal();
const { getTempDetail, setTempDetail } = useOptiionList();
const { tempDetail } = storeToRefs(useOptiionList());
const { setSelectList, setKnowledgeBaseList } = useKnowledgeBase();
declare module _czc {
  const push: (array: any) => void;
}

//当前问的问题
const question = ref('');

// 暂时禁用引用图文功能 - 过滤和去重图片函数 - 如需重新启用请取消以下注释
/*
const filterAndDeduplicateImages = (showImages) => {
  if (!showImages || !Array.isArray(showImages)) {
    return showImages;
  }
  
  console.log('开始前端图片过滤，原始列表:', showImages);
  console.log('当前回答标题状态:', currentAnswerHasImageTitle.value);
  
  // 收集所有图片内容（排除标题）
  const allImageContent = [];
  let titleCount = 0;
  
  for (const item of showImages) {
    // 如果是标题行
    if (item.includes('引用图文如下')) {
      titleCount++;
      console.log(`发现第${titleCount}个标题:`, item);
      continue; // 跳过所有后端发来的标题，我们自己控制
    }
    
    // 提取图片路径进行去重
    const pathMatch = item.match(/!\[.*?\]\((.*?)\)/);
    if (pathMatch) {
      const imagePath = pathMatch[1];
      // 使用全局的图片路径记录进行去重
      if (!currentAnswerImagePaths.value.has(imagePath)) {
        currentAnswerImagePaths.value.add(imagePath);
        allImageContent.push(item);
        console.log('保留图片:', imagePath);
      } else {
        console.log('去重跳过图片 (已在当前回答中存在):', imagePath);
      }
    } else {
      // 如果不是图片格式，也保留
      allImageContent.push(item);
      console.log('保留非图片内容:', item);
    }
  }
  
  console.log(`发现${titleCount}个标题，去重后${allImageContent.length}张图片`);
  
  // 构建最终结果：只有当前回答中还没有添加过标题时才添加
  if (allImageContent.length > 0) {
    let filteredResult = [];
    
    // 如果当前回答还没有添加过标题，添加标题
    if (!currentAnswerHasImageTitle.value) {
      filteredResult.push('\n### 引用图文如下：\n');
      currentAnswerHasImageTitle.value = true;
      console.log('添加标题（首次）');
    } else {
      console.log('跳过标题（已存在）');
    }
    
    // 添加图片内容
    filteredResult.push(...allImageContent);
    
    console.log('前端图片过滤结果:', `原始${showImages.length}项 -> 过滤后${filteredResult.length}项`);
    console.log('最终结果:', filteredResult);
    return filteredResult;
  } else {
    console.log('没有有效图片，返回空数组');
    return [];
  }
};
*/

//问答的上下文
const history = computed(() => {
  const context = userSettings.value.context;
  if (context === 0) return [];
  const usefulChat = QA_List.value.filter(item => item.type === 'ai');
  const historyChat = context === 11 ? usefulChat : usefulChat.slice(-context);
  return historyChat.map(item => [item.question, item.answer]);
});

//当前是否回答中
const showLoading = ref(false);

//当前是否在生成对话
const thinkingLoading = ref(false);

// 暂时禁用引用图文功能相关变量 - 如需重新启用请取消以下注释
/*
// 记录当前回答中已添加的图片路径，用于去重
const currentAnswerImagePaths = ref(new Set());

// 记录当前回答是否已添加过"引用图文如下"标题
const currentAnswerHasImageTitle = ref(false);
*/

const showSourceIdxs = ref([]);

// 被监听的元素
const observeDom = ref(null);

// 问答列表被监听的元素
const qaObserveDom = ref(null);

//取消请求用
let ctrl: AbortController;

const chatContainer = ref(null);
const scrollDom = ref(null);
const conversationHistoryRef = ref(null);

const scrollBottom = () => {
  nextTick(() => {
    scrollDom.value?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  });
};

async function newChat() {
  if (showLoading.value) {
    return;
  }
  if (chatId.value === null) {
    Message.info('已切换最新对话');
    return;
  }

  try {
    console.log('=== 开始创建新话题 ===');
    
    // 创建临时知识库
    console.log('1. 创建临时知识库...');
    const kb_id = await createTempKnowledgeBase();
    console.log('临时知识库创建成功，ID:', kb_id);
    
    // 获取当前活跃模型名称
    const modelName = chatSettingFormActive.value?.apiModelName || '默认模型';
    console.log('2. 使用模型:', modelName);
    
    // 立即创建新话题记录
    console.log('3. 创建新话题记录...');
    const res: any = await createQaLog({
      query: '新话题',
      kb_ids: [kb_id],
      model: modelName,
    });
    console.log('新话题记录创建成功，qa_id:', res.qa_id);
    
    // 重置对话状态
    console.log('4. 重置对话状态...');
    currentQaId.value = res.qa_id;
    chatId.value = res.qa_id;
    QA_List.value = [];
    qaPageId.value = 1;
    pageId.value = 1;
    setSelectList([kb_id]);
    setTempId(kb_id);
    
    console.log('5. 刷新话题列表...');
    // 延迟刷新话题列表以显示新创建的话题，避免影响当前状态
    setTimeout(() => {
      refreshConversationHistory();
    }, 500);
    
    // 验证话题是否成功创建并显示
    setTimeout(() => {
      const conversationHistoryComponent = conversationHistoryRef.value;
      if (conversationHistoryComponent) {
        console.log('6. 验证话题是否在列表中显示...');
        // 如果需要的话，可以添加额外的验证逻辑
      }
    }, 1000);
    
    console.log('=== 新话题创建完成 ===');
    Message.success('已创建新话题，请查看右侧话题列表');
  } catch (e) {
    console.error('创建新话题失败:', e);
    Message.error(`创建新话题失败: ${e.message || '未知错误'}`);
  }
}

// 创建临时知识库的函数
async function createTempKnowledgeBase() {
  try {
    const timestamp = formatTimestamp(Date.now());
    console.log('正在创建临时知识库...');
    
    const res: any = await resultControl(
      await urlResquest.createKb({
        kb_name: `临时知识库-${timestamp}`,
        description: '',
        kb_type: 'temporary' // 标记为临时知识库
      }));
      
    // 验证创建结果
    if (!res || !res.kb_id || res.kb_id.trim() === '') {
      console.error('创建临时知识库失败，返回的ID无效:', res);
      throw new Error('创建临时知识库失败，服务器返回的知识库ID无效');
    }
    
    console.log('成功创建临时知识库:', res.kb_id);
    
    // 更新知识库列表
    const kbList = await urlResquest.kbList();
    setKnowledgeBaseList(kbList.data);
    console.log('知识库列表已更新:', kbList.data);
    
    return res.kb_id;
  } catch (e) {
    console.error('创建临时知识库失败:', e);
    throw new Error(`创建临时知识库失败: ${e.msg || e.message || '未知错误'}`);
  }
}

// 创建问答记录的函数
async function createQaLog(params: { query: string; kb_ids: string[]; model: string }) {
  try {
    console.log('开始创建问答记录，参数:', params);
    
    const res: any = await resultControl(
      await urlResquest.createQaLog({
        query: params.query,
        kb_ids: params.kb_ids,
        model: params.model,
        result: '',  // 空的结果，待后续填充
        is_favorite: false,
        time_record: {
          total_time: 0,
          retrieval_time: 0,
          llm_time: 0
        },
        history: [],  // 空的历史记录，待后续填充
        condense_question: '',
        prompt: '',
        retrieval_documents: [],
        source_documents: []
      })
    );
    
    console.log('成功创建问答记录，返回结果:', res);
    
    // 验证返回结果
    if (!res || !res.qa_id) {
      console.error('创建问答记录返回的数据无效:', res);
      throw new Error('服务器返回的问答记录ID无效');
    }
    
    return res;
  } catch (e) {
    console.error('创建问答记录失败:', e);
    throw new Error(`创建问答记录失败: ${e.msg || e.message || '未知错误'}`);
  }
}

// 创建 Intersection Observer 对象
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      pageId.value++;
    }
  });
});

// 问答观察者
const qaObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      qaPageId.value++;
    }
  });
});

// 监听用户信息变化，重新初始化模型配置
watch(
  () => userInfo.value,
  async (newUserInfo, oldUserInfo) => {
    console.log('Chat.vue watch 触发, newUserInfo:', newUserInfo, 'oldUserInfo:', oldUserInfo);
    
    // 当用户信息发生变化时（比如重新登录），重新初始化模型配置
    if (newUserInfo && newUserInfo.userId && (!oldUserInfo || oldUserInfo.userId !== newUserInfo.userId)) {
      console.log('Chat.vue: 用户信息变化，刷新模型配置');
      // 延迟刷新模型配置，让ChatHeaderMenu先尝试
      setTimeout(async () => {
        await forceRefreshModelConfiguration();
      }, 1000);
    }
  },
  { immediate: true, deep: true }
);

// 监听路由变化，每次切换到聊天页面都刷新模型配置
watch(
  () => router.currentRoute.value.path,
  async (newPath, oldPath) => {
    console.log('=== Chat.vue 路由变化监听 ===');
    console.log('路由变化:', oldPath, '->', newPath);
    
    // 判断是否切换到了聊天页面
    if (newPath === '/home' || newPath.includes('/home')) {
      console.log('检测到切换到聊天页面，强制刷新模型配置');
      console.log('当前用户信息:', userInfo.value);
      console.log('当前模型配置:', chatSettingFormActive.value);
      
      // 延迟一下确保页面已经完全加载
      await new Promise(resolve => setTimeout(resolve, 200));
      
      console.log('开始执行强制刷新...');
      await forceRefreshModelConfiguration();
      console.log('强制刷新完成');
    } else {
      console.log('切换到非聊天页面，跳过模型配置刷新');
    }
  },
  { immediate: false }
);

onMounted(async () => {
  scrollBottom();
  
  // 添加全局点击事件监听器
  document.addEventListener('click', handleClickOutside);
  
  // 强制尝试初始化模型配置
  console.log('=== Chat.vue onMounted: 页面切换到聊天界面 ===');
  console.log('Chat.vue: 当前路由:', router.currentRoute.value.path);
  console.log('Chat.vue: 当前用户:', userInfo.value);
  
  // 等待一下再检查，确保所有组件都已加载
  await new Promise(resolve => setTimeout(resolve, 300));
  await forceRefreshModelConfiguration();
});

// 添加组件激活时的处理（keep-alive场景）
onActivated(async () => {
  console.log('=== Chat.vue onActivated: 聊天组件已激活 ===');
  console.log('Chat.vue: 当前路由:', router.currentRoute.value.path);
  
  // 每次激活都强制刷新模型配置
  await forceRefreshModelConfiguration();
});

// 强制刷新模型配置的函数 - 每次切换到聊天页面都执行
const forceRefreshModelConfiguration = async () => {
  console.log('=== Chat.vue: 开始强制刷新模型配置 ===');
  console.log('Chat.vue: 当前用户信息:', userInfo.value);
  
  // 检查用户信息是否可用
  if (!userInfo.value || !userInfo.value.userId) {
    console.log('Chat.vue: 用户信息未加载，等待用户信息...');
    
    // 等待用户信息加载，最多等待3秒
    for (let i = 0; i < 6; i++) {
      await new Promise(resolve => setTimeout(resolve, 500));
      if (userInfo.value && userInfo.value.userId) {
        console.log('Chat.vue: 用户信息已加载，继续刷新模型配置');
        break;
      }
    }
    
    if (!userInfo.value || !userInfo.value.userId) {
      console.error('Chat.vue: 等待超时，用户信息仍未加载');
      return;
    }
  }
  
  // 设置加载状态
  setAllChatSettingConfigured([{
    modelType: 'loading',
    modelName: '正在刷新模型配置...',
    apiModelName: '正在刷新模型配置...',
    customId: '',
    apiKey: '',
    apiBase: '',
    chunkSize: 800,
    serviceId: '',
    apiContextLength: 4096,
    maxToken: 1024,
    temperature: 0.5,
    top_P: 1.0,
    top_K: 40,
    context: 10,
    capabilities: {
      networkSearch: false,
      mixedSearch: false,
      onlySearch: false,
      rerank: false,
    },
    active: true,
    originalData: {}
  }]);
  
  // 强制重新获取模型配置，最多尝试5次
  for (let i = 0; i < 5; i++) {
    console.log(`Chat.vue: 第${i + 1}次尝试刷新模型配置`);
    
    try {
      await initializeModelConfig();
      
      // 验证获取结果
      const currentActiveModel = chatSettingFormActive.value;
      console.log(`Chat.vue: 第${i + 1}次刷新后的模型配置:`, currentActiveModel);
      
      if (currentActiveModel && 
          currentActiveModel.apiModelName && 
          currentActiveModel.apiModelName !== '正在刷新模型配置...' &&
          currentActiveModel.apiModelName !== '正在加载模型...' &&
          currentActiveModel.modelName !== '模型获取失败' &&
          currentActiveModel.modelName !== '模型配置错误' &&
          currentActiveModel.modelType !== 'error' &&
          currentActiveModel.modelType !== 'loading') {
        console.log('Chat.vue: 模型配置刷新成功，模型名称:', currentActiveModel.apiModelName);
        console.log('Chat.vue: 最终活跃模型完整信息:', currentActiveModel);
        return;
      }
      
      console.log('Chat.vue: 获取到的模型配置无效，继续重试');
      console.log('Chat.vue: 无效原因检查:');
      console.log('  - apiModelName:', currentActiveModel?.apiModelName);
      console.log('  - modelName:', currentActiveModel?.modelName); 
      console.log('  - modelType:', currentActiveModel?.modelType);
      console.log('  - 完整对象:', currentActiveModel);
    } catch (error) {
      console.error(`Chat.vue: 第${i + 1}次刷新失败:`, error);
    }
    
    // 递增等待时间再重试
    await new Promise(resolve => setTimeout(resolve, 500 * (i + 1)));
  }
  
  // 如果所有尝试都失败了，显示错误提示
  console.error('Chat.vue: 多次尝试后仍无法获取有效模型配置');
  Message.error('模型配置加载失败，请刷新页面重试');
};

onBeforeUnmount(() => {
  // 移除全局点击事件监听器
  document.removeEventListener('click', handleClickOutside);
  
  if (observeDom.value) {
    observer.unobserve(observeDom.value);
  }
  if (qaObserveDom.value) {
    qaObserver.unobserve(qaObserveDom.value);
  }
});

const like = throttle((item, e) => {
  item.like = !item.like;
  item.unlike = false;
  _czc.push(['_trackEvent', 'qanything', '问答页面', '点赞', '', '']);
  if (item.like) {
    e.target.parentNode.style.animation = 'shake ease-in .5s';
    const timer = setTimeout(() => {
      clearTimeout(timer);
      e.target.parentNode.style.animation = '';
    }, 600);
  }
}, 800);
const unlike = (item: IChatItem) => {
  item.unlike = !item.unlike;
  item.like = false;
  _czc.push(['_trackEvent', 'qanything', '问答页面', '点踩', '', '']);
};

//拷贝
const myCopy = (item: IChatItem) => {
  copy(item.answer)
    .then(() => {
      item.copied = !item.copied;
      Message.success(common.copySuccess);
      const timer = setTimeout(() => {
        clearTimeout(timer);
        item.copied = !item.copied;
      }, 1000);
    })
    .catch(() => {
      Message.error(common.copyFailed);
    });
};

const addQuestion = q => {
  QA_List.value.push({
    question: q,
    type: 'user',
    showEditIcon: false,
    isEditing: false,
    editingText: '',
  });
  scrollBottom();
};

const addAnswer = (question: string) => {
  // 暂时禁用引用图文功能 - 重置图片相关状态 - 如需重新启用请取消以下注释
  /*
  // 重置当前回答的图片路径记录和标题状态
  currentAnswerImagePaths.value.clear();
  currentAnswerHasImageTitle.value = false;
  console.log('开始新回答，重置图片路径记录和标题状态');
  */
  
  QA_List.value.push({
    answer: '',
    question,
    onlySearch: chatSettingFormActive.value.capabilities.onlySearch,
    type: 'ai',
    copied: false,
    like: false,
    unlike: false,
    source: [],
    showTools: false,
  });
};

const chatInfoClass = new ChatInfoClass();

const setObserveDom = value => {
  observeDom.value = value;
};

const setQaObserverDom = value => {
  qaObserveDom.value = value;
};

const updateChat = (title: string, chatId: number, knowledgeListSelect) => {
  try {
    updateHistoryList(title, chatId, knowledgeListSelect);
  } catch (e) {
    Message.error(e.msg || '更新对话失败');
  }
};

function checkKbSelect() {
  if (!selectList.value.length) {
    return;
  }
  // 删除知识库时不会删除对话里表中已经选中的知识库id  所以每次问答前都要校验一下这个知识库id还存不存在
  const list = [];
  selectList.value.forEach(kbId => {
    if (knowledgeBaseList.value.some(item => item.kb_id === kbId)) {
      list.push(kbId);
    }
  });
  selectList.value = list;
  // 如果当前对话选中的知识库有变化 就更新一下
  historyList.value.forEach(item => {
    if (
      chatId.value !== null &&
      item.historyId === chatId.value &&
      item.kbIds.join('') !== selectList.value.join('')
    ) {
      updateChat(item.title, item.historyId, selectList.value);
    }
  });
}

const stopChat = () => {
  if (ctrl) {
    ctrl.abort('停止对话');
  }
  typewriter.done();
  showLoading.value = false;
  QA_List.value[QA_List.value.length - 1].showTools = true;
};

// 问答前处理 判断创建对话
const beforeSend = title => {
  try {
    // 判断需不需要新建对话, 为null直接跳出
    if (chatId.value !== null) return;
    if (title.length > 100) {
      title = title.substring(0, 100);
    }
    // 当前对话id为新建的historyId
    chatId.value = addHistoryList(title);
    updateChat(title, chatId.value, selectList.value);
  } catch (e) {
    Message.error(e.msg || '创建对话失败');
  }
};

// Mention 的 配置项
const mentionOptions = ref<string[]>([]);
const getMentionOptions = async () => {
  const res: any = await resultControl(
    await urlResquest.getTags({
      kb_ids: selectList.value,
    })
  );
  mentionOptions.value = res.tags;
};
watch(
  () => selectList,
  () => {
    // getMentionOptions();
  },
  {
    immediate: true,
    deep: true,
  }
);

watch(
  () => tempId.value,
  () => {
    setTempDetail([])
    getTempDetail();
  }
);
// 统计几个 @ 超过10个报错
const computedCallNumber = (question: string) => {
  const atCount = (question.match(/@/g) || []).length;
  return atCount <= 10;
};
//发送问答消息
const send = async () => {
  if (!question.value.trim().length) {
    return;
  }
  if (showLoading.value) {
    Message.warning('正在聊天中...请等待结束');
    return;
  }
  // 检查模型配置是否正确
  if (!(await checkChatSetting())) {
    Message.error('模型设置错误，请先检查模型配置');
    return;
  }
  if (!computedCallNumber(question.value)) {
    Message.error('不可@超过10个');
    return;
  }

  checkKbSelect();
  // if (!selectList.value.length) {
  //   return Message.warning(common.chooseError);
  // } else {
  //   // 校验选中的知识库
  //   Message.info({
  //     content:
  //       common.type === 'zh'
  //         ? `已选择 ${selectList.value.length} 个知识库进行问答`
  //         : ` ${selectList.value.length} knowledge base has been selected`,
  //     icon: ' ',
  //   });
  // }
  const q = question.value;
  beforeSend(q);

  // 如果是新对话，创建qa_log并获取qa_id
  if (currentQaId.value === null && QA_List.value.length === 0) {
    try {
      const res: any = await createQaLog({
        query: question.value,
        kb_ids: selectList.value,
        model: chatSettingFormActive.value.apiModelName,
      });
      setCurrentQaId(res.qa_id);
    } catch (e) {
      console.error('创建qa_log失败', e);
    }
  } else if (currentQaId.value && QA_List.value.length === 0) {
    // 如果已有qa_id但是聊天列表为空（说明是新创建的话题），则更新话题标题为用户输入内容
    try {
      await urlResquest.updateQaLog({
        qa_id: currentQaId.value,
        update_data: {
          query: question.value
        }
      });
      console.log('更新话题标题为:', question.value);
      // 不立即刷新话题列表，避免影响当前对话显示
      // 在对话完成后再刷新
    } catch (e) {
      console.error('更新话题标题失败', e);
    }
  }

  question.value = '';
  addQuestion(q);
  // 更新最大的chatList
  // addChatList(chatId.value, QA_List.value);
  showLoading.value = true;
  thinkingLoading.value = true;
  ctrl = new AbortController();

  // 处理kb_ids，确保去重
  let kbIds = [...selectList.value];
  if (tempId.value && !kbIds.includes(tempId.value)) {
    kbIds.push(tempId.value);
  }
  // 进一步去重，防止其他地方的重复
  kbIds = [...new Set(kbIds)];

  const sendData = {
    kb_ids: kbIds,
    history: history.value,
    question: q,
    streaming: chatSettingFormActive.value.capabilities.onlySearch === false,
    networking: chatSettingFormActive.value.capabilities.networkSearch,
    product_source: 'saas',
    // rerank: chatSettingFormActive.value.capabilities.rerank,
    rerank: true,
    only_need_search_results: chatSettingFormActive.value.capabilities.onlySearch,
    // hybrid_search: chatSettingFormActive.value.capabilities.mixedSearch,
    hybrid_search: true,

    api_context_length: userSettings.value.apiContextLength,
    max_token: userSettings.value.maxToken,
    top_p: userSettings.value.top_P,
    temperature: userSettings.value.temperature,
    top_k: userSettings.value.top_K,

    api_base: chatSettingFormActive.value.apiBase,
    api_key: chatSettingFormActive.value.apiKey,
    model: chatSettingFormActive.value.modelType,
    chunk_size: chatSettingFormActive.value.chunkSize,
    qa_id: currentQaId.value,
  };

  // 如果是仅检索
  if (chatSettingFormActive.value.capabilities.onlySearch) {
    // 模型配置添加进去
    chatInfoClass.addChatSetting(chatSettingFormActive.value);
    addAnswer(q);
    try {
      const res: any = await resultControl(
        await urlResquest.sendQuestion(sendData, { signal: ctrl.signal })
      );
      if (res.code === 200) {
        QA_List.value[QA_List.value.length - 1].answer = res?.source_documents.length
          ? common.searchCompleted
          : common.searchNotFound;
        QA_List.value[QA_List.value.length - 1].source = res?.source_documents;
      }
    } catch (e) {
      console.log('出错', e);
      // Message.error(e.msg || '出错了');
      QA_List.value[QA_List.value.length - 1].answer = e.msg || 'error';
    }
    // 无论成不成功,结束后的操作
    showLoading.value = false;
    thinkingLoading.value = false;
    QA_List.value[QA_List.value.length - 1].showTools = true;
    // 更新最大的chatList
    // addChatList(chatId.value, QA_List.value);
    await nextTick(() => {
      scrollBottom();
    });
  } else {
    fetchEventSource(apiBase + '/local_doc_qa/local_doc_chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: ['text/event-stream', 'application/json'],
        Authorization: `Bearer ${Cookies.get('token')}`
      },
      openWhenHidden: true,
      body: JSON.stringify({
        user_id: userId,
        user_info: userPhone,
        ...sendData,
      }),
      signal: ctrl.signal,
      onopen(e: any) {
        console.log('open', e);
        addAnswer(q);
        if (e.ok && e.headers.get('content-type') === 'text/event-stream') {
          // 模型配置添加进去
          chatInfoClass.addChatSetting(chatSettingFormActive.value);
          typewriter.start();
        } else if (e.headers.get('content-type') === 'application/json') {
          typewriter.add('Error 请检查模型是否配置正确');
        }
      },
      onmessage(msg: { data: string }) {
        thinkingLoading.value = false;
        const res: any = JSON.parse(msg.data);
        if (res?.code == 200 && res?.response && res.msg === 'success') {
          // 中间的回答
          // QA_List.value[QA_List.value.length - 1].answer += res.result.response;
          // typewriter.add(res?.response.replaceAll('\n', '<br/>'));
          typewriter.add(res?.response);
          scrollBottom();
        } else {
          // 最后一次回答
          const timeObj = res.time_record.time_usage;
          delete timeObj['retriever_search_by_milvus'];
          chatInfoClass.addTime(res.time_record.time_usage);
          chatInfoClass.addToken(res.time_record.token_usage);
          chatInfoClass.addDate(Date.now());
        }

        if (res?.source_documents?.length) {
          QA_List.value[QA_List.value.length - 1].source = res?.source_documents;
        }

        // 暂时禁用引用图文功能 - 如需重新启用请取消以下注释
        /*
        if (res?.show_images?.length) {
          // 对图片进行去重处理，避免重复显示
          const filteredImages = filterAndDeduplicateImages(res.show_images);
          console.log('处理show_images, filteredImages:', filteredImages);
          
          filteredImages.map(item => {
            typewriter.add(item);
            console.log(QA_List.value.at(-1).answer);
          });
        }
        */
      },
      onclose(e: any) {
        console.log('close', e);
        typewriter.done();
        ctrl.abort();
        showLoading.value = false;
        thinkingLoading.value = false;
        QA_List.value[QA_List.value.length - 1].showTools = true;
        // 将chat info添加进回答中
        QA_List.value.at(-1).itemInfo = chatInfoClass.getChatInfo();
        // 更新最大的chatList
        // addChatList(chatId.value, QA_List.value);
        updateQaLog(QA_List.value).then(() => {
          refreshConversationHistory();
          nextTick(() => {
            scrollBottom();
          });
        });
      },
      onerror(err: any) {
        console.log('error', err);
        typewriter?.done();
        ctrl?.abort();
        showLoading.value = false;
        thinkingLoading.value = false;
        QA_List.value[QA_List.value.length - 1].showTools = true;
        Message.error(err.msg || '出错了');
        // 更新最大的chatList
        // addChatList(chatId.value, QA_List.value);
        updateQaLog(QA_List.value).then(() => {
          refreshConversationHistory();
          nextTick(() => {
            scrollBottom();
          });
        });
        throw err;
      },
    });
  }
};

// 注意：createQaLog 函数已经在上面定义过了，这里删除重复定义

// 更新qa_log的函数
const updateQaLog = async (update_data) => {
  try {
    const requestData = {
      qa_id: currentQaId.value,
      user_id: userId,
      update_data: {
        history: update_data
      }
    }

    const res = await resultControl(
      await urlResquest.updateQaLog(requestData)
    );
    return res;
  } catch (e) {
    Message.error(e.msg || '更新qa_log失败');
    console.log(e)
    throw e;
  }
};

const reAnswer = (item: IChatItem) => {
  question.value = item.question;
  send();
};

//点击查看是否显示详细来源
const showDetail = (item: IChatItem, index) => {
  item.source[index].showDetailDataSource = !item.source[index].showDetailDataSource;
};

const hideDetail = (item: IChatItem, index) => {
  item.source[index].showDetailDataSource = false;
};

const showSourceList = index => {
  showSourceIdxs.value.push(index);
};

const hideSourceList = index => {
  showSourceIdxs.value = showSourceIdxs.value.filter(item => item !== index);
};

// 分享
const shareChat = async () => {
  if (selectList.value.length === 0) return;
  try {
    // 创建机器人
    const { bot_id } = (await resultControl(
      await urlResquest.createBot({
        bot_name: 'bot-' + formatTimestamp(Date.now()),
        description: '来源: 知识库创建-' + formatTimestamp(Date.now()),
      })
    )) as any;
    // 将知识库变为现在这个
    await resultControl(
      await urlResquest.updateBot({
        bot_id,
        kb_ids: [...selectList.value],
        only_need_search_results: chatSettingFormActive.value.capabilities.onlySearch,
        networking: chatSettingFormActive.value.capabilities.networkSearch,
        api_base: chatSettingFormActive.value.apiBase,
        api_key: chatSettingFormActive.value.apiKey,

        // 使用用户本地设置
        api_context_length: userSettings.value.apiContextLength,
        max_token: userSettings.value.maxToken,
        chunk_size: userSettings.value.maxToken,
        top_p: userSettings.value.top_P,
        temperature: userSettings.value.temperature,
        top_k: userSettings.value.top_K,

        model: chatSettingFormActive.value.apiModelName,
        hybrid_search: chatSettingFormActive.value.capabilities.mixedSearch,
        // chunk_size: chatSettingFormActive.value.chunkSize,
        rerank: chatSettingFormActive.value.capabilities.rerank,
      })
    );
    setCopyUrlVisible(true);
    const { origin, pathname } = window.location;
    setWebUrl(`${origin + pathname}#/bots/${bot_id}/share`);
  } catch (e) {
    Message.error(e?.msg || '分享失败');
  }
};

//下载 清除聊天记录相关
const { showModal } = storeToRefs(useChat());
const confirmLoading = ref(false);
const content = ref('');
const type = ref('');
const downloadChat = () => {
  if (showLoading.value) return;
  type.value = 'download';
  showModal.value = true;
  content.value = common.saveTip;
};

const deleteChat = () => {
  if (showLoading.value) return;
  type.value = 'delete';
  showModal.value = true;
  content.value = common.clearTip;
};

const confirm = async () => {
  confirmLoading.value = true;
  if (type.value === 'download') {
    console.log('download');
    try {
      const ele = document.getElementById('chat-ul');
      const canvas = await html2canvas(ele as HTMLDivElement, {
        useCORS: true,
      });
      const imgUrl = canvas.toDataURL('image/png');
      const tempLink = document.createElement('a');
      tempLink.style.display = 'none';
      tempLink.href = imgUrl;
      tempLink.setAttribute('download', 'chat-shot.png');
      if (typeof tempLink.download === 'undefined') tempLink.setAttribute('target', '_blank');

      document.body.appendChild(tempLink);
      tempLink.click();
      document.body.removeChild(tempLink);
      window.URL.revokeObjectURL(imgUrl);
      Message.success('下载成功');
      Promise.resolve();
    } catch (e) {
      console.log(e);
      Message.error(e.message || e.msg || '出错了');
    }
  } else if (type.value === 'delete') {
    console.log('delete');
    // history.value = [];
    clearChatList(chatId.value);
    chatId.value = null;
    QA_List.value = [];
  }
  type.value = '';
  content.value = '';
  confirmLoading.value = false;
  showModal.value = false;
};

// 模型设置弹窗相关
const { showSettingModal } = storeToRefs(useChat());

const handleModalChange = newVal => {
  showSettingModal.value = newVal;
};

// 模型配置是否正确
const chatSettingForDialogRef = ref<InstanceType<typeof ChatSettingDialog>>();
const checkChatSetting = async () => {
  // 检查是否有活跃的模型配置
  const activeModel = chatSettingFormActive.value;
  
  console.log('=== checkChatSetting 验证开始 ===');
  console.log('activeModel:', activeModel);
  
  // 如果没有活跃模型，尝试刷新模型配置
  if (!activeModel) {
    console.error('未找到活跃模型配置，尝试刷新...');
    await forceRefreshModelConfiguration();
    
    // 重新获取活跃模型
    const retryActiveModel = chatSettingFormActive.value;
    if (!retryActiveModel) {
      console.error('刷新后仍未找到活跃模型配置');
      Message.error('未找到可用的模型配置，请联系管理员');
      return false;
    }
    
    console.log('刷新成功，获得活跃模型:', retryActiveModel);
    // 使用重新获取的模型继续验证
    return await validateModelConfig(retryActiveModel);
  }
  
  return await validateModelConfig(activeModel);
};

// 提取模型配置验证逻辑为单独函数
const validateModelConfig = async (activeModel) => {
  console.log('=== 开始验证模型配置 ===');
  console.log('完整模型对象:', activeModel);
  console.log('验证关键字段:');
  console.log('  - apiModelName:', activeModel.apiModelName);
  console.log('  - modelName:', activeModel.modelName);
  console.log('  - apiBase:', activeModel.apiBase);
  console.log('  - apiKey:', activeModel.apiKey ? '已设置' : '未设置');
  console.log('  - modelType:', activeModel.modelType);
  console.log('  - serviceId:', activeModel.serviceId);
  console.log('  - customId:', activeModel.customId);
  
  // 检查是否是错误状态的模型配置
  if (activeModel.modelType === 'error' || activeModel.modelType === 'loading') {
    console.error('验证失败：模型配置处于错误或加载状态，modelType:', activeModel.modelType);
    Message.error('模型配置异常，请刷新页面重试');
    return false;
  }
  
  // 如果模型信息无效（比如显示"正在加载模型..."等）
  const invalidModelNames = [
    '正在加载模型...',
    '正在刷新模型配置...',
    '请联系管理员配置模型',
    '请检查网络连接',
    '请刷新页面重试或联系管理员',
    '无可用模型',
    '模型加载失败',
    '模型获取失败',
    '模型配置错误'
  ];
  
  if (!activeModel.apiModelName || invalidModelNames.includes(activeModel.apiModelName) ||
      !activeModel.modelName || invalidModelNames.includes(activeModel.modelName)) {
    console.error('验证失败：模型配置包含无效名称');
    console.error('  - apiModelName:', activeModel.apiModelName);
    console.error('  - modelName:', activeModel.modelName);
    console.error('  - 无效名称列表:', invalidModelNames);
    Message.error('模型配置无效，请稍后重试或联系管理员');
    return false;
  }
  
  // 基本的模型配置验证
  if (!activeModel.apiBase && activeModel.modelType !== 'openAI') {
    console.error('验证失败：模型API路径未配置');
    console.error('  - apiBase:', activeModel.apiBase);
    console.error('  - modelType:', activeModel.modelType);
    Message.error('模型API路径未配置');
    return false;
  }
  
  if (!activeModel.apiKey && activeModel.modelType !== 'ollama') {
    console.error('验证失败：模型API密钥未配置');
    console.error('  - apiKey:', activeModel.apiKey ? '已设置' : '未设置');
    console.error('  - modelType:', activeModel.modelType);
    Message.error('模型API密钥未配置');
    return false;
  }
  
  console.log('基本验证通过，准备调用详细表单验证');
  
  // 如果基本检查通过，调用详细的表单验证
  const detailValidationResult = chatSettingForDialogRef.value?.handleOk() ?? true;
  console.log('详细表单验证结果:', detailValidationResult);
  
  if (detailValidationResult) {
    console.log('=== 模型配置验证完全通过 ===');
  } else {
    console.error('=== 详细表单验证失败 ===');
  }
  
  return detailValidationResult;
};

// 检查信息来源的文件是否支持窗口化渲染
let supportSourceTypes = [
  'md',
  'txt',
  'pdf',
  'jpg',
  'png',
  'jpeg',
  'doc',
  'docx',
  'xls',
  'xlsx',
  'ppt',
  'pptx',
  'jsonl',
  'csv',
  'eml',
];
const checkFileType = filename => {
  if (!filename) {
    return false;
  }
  const arr = filename.split('.');
  if (arr.length) {
    const suffix = arr.pop();
    if (supportSourceTypes.includes(suffix)) {
      return true;
    } else {
      return false;
    }
  } else {
    return false;
  }
};

const handleChatSource = file => {
  const isSupport = checkFileType(file.file_name);
  if (isSupport) {
    queryFile(file);
  }
};

async function queryFile(file) {
  try {
    setSourceUrl(null);
    const res: any = await resultControl(await urlResquest.getFile({ file_id: file.file_id }));
    console.log('queryFile', res);
    const suffix = file.file_name.split('.').pop();
    const b64Type = getB64Type(suffix);
    console.log('b64Type', b64Type);
    setSourceType(suffix);
    setSourceUrl(`data:${b64Type};base64,${res.file_base64}`);
    if (suffix === 'txt' || suffix === 'md' || suffix === 'csv' || suffix === 'eml') {
      const decodedTxt = atob(res.file_base64);
      const correctStr = decodeURIComponent(escape(decodedTxt));
      console.log('decodedTxt', correctStr);
      setTextContent(correctStr);
      setChatSourceVisible(true);
    } else {
      setChatSourceVisible(true);
    }
  } catch (e) {
    Message.error(e.msg || '获取文件失败');
  }
}

let b64Types = [
  'text/markdown', // md
  'text/plain', // txt
  'application/pdf', // pdf
  'image/jpeg', // jpg
  'image/png', // png
  'image/jpeg', // jpeg
  'application/msword', // doc
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // docx
  'application/vnd.ms-excel', // xls
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx
  'application/vnd.ms-powerpoint', // ppt
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // pptx
  'application/jsonl', // jsonl
  'text/csv', // csv
  'message/rfc822', // eml
];

function getB64Type(suffix) {
  const index = supportSourceTypes.indexOf(suffix);
  return b64Types[index];
}

// 清空多轮问答历史
function clearHistory() {
  // 先注了，不知道这方法干啥用的，也不敢动
  console.log('清空');
  // history.value = [];
}

const openFileUpload = () => {
  setModalVisible(true);
};

const handleKeydown = (e: KeyboardEvent) => {
  // 只处理 Enter 键
  if (e.key === 'Enter') {
    // 如果按下 shift + enter，则换行
    if (e.shiftKey) {
      // 允许默认行为（换行）
      return;
    }
    // 否则发送消息
    e.preventDefault();
    send();
  }
};

// 处理用户消息悬停
const handleUserMessageHover = (index: number, isHover: boolean) => {
  if (QA_List.value[index] && QA_List.value[index].type === 'user') {
    QA_List.value[index].showEditIcon = isHover;
  }
};

// 自动调整textarea高度和宽度
const autoResizeTextarea = (textarea: HTMLTextAreaElement) => {
  // 重置高度和宽度
  textarea.style.height = 'auto';
  textarea.style.width = 'auto';
  
  // 创建一个隐藏的div来测量文本的实际尺寸
  const measureDiv = document.createElement('div');
  measureDiv.style.position = 'absolute';
  measureDiv.style.visibility = 'hidden';
  measureDiv.style.whiteSpace = 'pre-wrap';
  measureDiv.style.wordWrap = 'break-word';
  measureDiv.style.padding = '13px 20px';
  measureDiv.style.fontSize = '14px';
  measureDiv.style.fontWeight = 'normal';
  measureDiv.style.lineHeight = '22px';
  measureDiv.style.fontFamily = textarea.style.fontFamily || 'inherit';
  measureDiv.style.maxWidth = 'calc(100vw - 200px)';
  measureDiv.style.minWidth = '100px';
  measureDiv.textContent = textarea.value || textarea.placeholder;
  
  document.body.appendChild(measureDiv);
  
  // 设置textarea的尺寸
  textarea.style.width = measureDiv.offsetWidth + 'px';
  textarea.style.height = measureDiv.offsetHeight + 'px';
  
  // 清理测量元素
  document.body.removeChild(measureDiv);
};

// 开始编辑用户消息
const startEdit = (index: number) => {
  const item = QA_List.value[index];
  if (item && item.type === 'user') {
    item.isEditing = true;
    item.editingText = item.question;
    item.showEditIcon = false;
    
    // 下一帧聚焦到编辑框并调整高度
    nextTick(() => {
      const textareas = document.querySelectorAll('.edit-textarea-native');
      const textarea = textareas[textareas.length - 1] as HTMLTextAreaElement;
      if (textarea) {
        // 自动调整高度
        autoResizeTextarea(textarea);
        
        // 聚焦并定位光标
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        
        // 添加输入事件监听器，实时调整高度
        textarea.addEventListener('input', () => {
          autoResizeTextarea(textarea);
        });
      }
    });
  }
};

// 取消编辑
const cancelEdit = (index: number) => {
  const item = QA_List.value[index];
  if (item && item.type === 'user') {
    item.isEditing = false;
    item.editingText = '';
    item.showEditIcon = false;
  }
};

// 确认编辑并重新发送
const confirmEdit = (index: number) => {
  const item = QA_List.value[index];
  if (item && item.type === 'user' && item.editingText.trim()) {
    // 取消编辑状态
    item.isEditing = false;
    item.showEditIcon = false;
    
    // 使用编辑后的文本重新发送消息
    question.value = item.editingText.trim();
    item.editingText = '';
    
    // 发送新消息
    send();
  }
};

// 处理编辑框的键盘事件
const handleEditKeydown = (e: KeyboardEvent, index: number) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    // Enter键确认编辑
    e.preventDefault();
    confirmEdit(index);
  } else if (e.key === 'Escape') {
    // Esc键取消编辑
    e.preventDefault();
    cancelEdit(index);
  }
};

// 点击页面其他地方取消编辑
const handleClickOutside = (e: Event) => {
  const target = e.target as HTMLElement;
  if (!target.closest('.edit-mode') && !target.closest('.edit-icon')) {
    // 取消所有正在编辑的消息
    QA_List.value.forEach((item, index) => {
      if (item.type === 'user' && item.isEditing) {
        cancelEdit(index);
      }
    });
  }
};

// 手动刷新对话历史列表
const refreshConversationHistory = () => {
  conversationHistoryRef.value?.fetchConversationHistory();
};

// 初始化模型配置
const initializeModelConfig = async () => {
  console.log('Chat.vue: 开始初始化模型配置');
  console.log('Chat.vue: 当前用户信息:', userInfo.value);
  
  if (!userInfo.value || !userInfo.value.userId) {
    console.log('Chat.vue: 用户信息未加载，跳过模型初始化');
    return;
  }

  try {
    if (userInfo.value.role === 'admin' || userInfo.value.role === 'superadmin') {
      // 管理员获取所有模型列表
      console.log('Chat.vue: 管理员用户，获取模型列表');
      const response = await urlResquest.getModelList({}, {});
      if (response && response.data && response.data.configs) {
        const modelList = response.data.configs;
        console.log('Chat.vue: 管理员获取到模型列表:', modelList);
        
        // 映射模型配置
        const customModels = modelList.map(model => ({
          modelType: model.model_endpoint || model.service_name || '',
          modelName: model.service_name || '未知模型',
          customId: model.config_id || '',
          apiKey: model.api_key || '',
          apiBase: model.api_proxy || '',
          chunkSize: 800,
          apiModelName: model.service_name || '未知模型',
          serviceId: model.service_id || '',
          apiContextLength: model.api_context_length || 4096,
          maxToken: Math.floor((model.max_token || 4096)),
          temperature: model.temperature || 0.5,
          top_P: model.top_p || 1.0,
          top_K: model.top_k || 40,
          context: model.context_length || 10,
          capabilities: {
            networkSearch: false,
            mixedSearch: false,
            onlySearch: false,
            rerank: false,
          },
          active: model.is_active === 1 || model.is_active === true,
          originalData: { ...model }
        }));

        // 确保至少有一个活跃模型
        const hasActiveModel = customModels.some(model => model.active);
        if (!hasActiveModel && customModels.length > 0) {
          console.log('Chat.vue: 没有活跃模型，设置第一个为活跃');
          customModels[0].active = true;
        }

        setAllChatSettingConfigured([...customModels]);
        console.log('Chat.vue: 管理员模型配置初始化完成');
        return; // 管理员直接返回，不执行普通用户逻辑
      } else {
        console.error('Chat.vue: 管理员获取模型列表失败:', response);
        throw new Error('获取模型列表失败');
      }
    } else {
      // 普通用户获取活跃模型
      console.log('Chat.vue: 普通用户，获取活跃模型');
      const response = await urlResquest.getActiveModel({}, {});
      if (response && response.code === 200 && response.data) {
        console.log('Chat.vue: 普通用户获取到活跃模型:', response.data);
        
        const activeModel = {
          modelType: response.data.model_endpoint || response.data.service_name || '',
          modelName: response.data.service_name || '未知模型',
          customId: response.data.config_id || '',
          apiKey: response.data.api_key || '',
          apiBase: response.data.api_proxy || '',
          chunkSize: 800,
          apiModelName: response.data.service_name || '未知模型',
          serviceId: response.data.service_id || '',
          apiContextLength: response.data.api_context_length || 4096,
          maxToken: Math.floor((response.data.max_token || 4096)),
          temperature: response.data.temperature || 0.5,
          top_P: response.data.top_p || 1.0,
          top_K: response.data.top_k || 40,
          context: response.data.context_length || 10,
          capabilities: {
            networkSearch: false,
            mixedSearch: false,
            onlySearch: false,
            rerank: false,
          },
          active: true, // 普通用户获取的就是活跃模型
          originalData: { ...response.data }
        };

        setAllChatSettingConfigured([activeModel]);
        console.log('Chat.vue: 普通用户模型配置初始化完成');
      } else {
        console.error('Chat.vue: 普通用户获取活跃模型失败:', response);
        throw new Error('获取活跃模型失败，请联系管理员配置');
      }
    }
  } catch (error) {
    console.error('Chat.vue: 模型配置初始化失败:', error);
    // 设置错误状态的模型配置
    setAllChatSettingConfigured([{
      modelType: 'error',
      modelName: '模型配置错误',
      apiModelName: '请刷新页面重试或联系管理员',
      customId: '',
      apiKey: '',
      apiBase: '',
      chunkSize: 800,
      serviceId: '',
      apiContextLength: 4096,
      maxToken: 1024,
      temperature: 0.5,
      top_P: 1.0,
      top_K: 40,
      context: 10,
      capabilities: {
        networkSearch: false,
        mixedSearch: false,
        onlySearch: false,
        rerank: false,
      },
      active: true,
      originalData: {}
    }]);
    throw error; // 重新抛出错误，让调用方知道失败
  }
};
</script>

<style lang="scss" scoped>
$avatar-width: 96px;

.container {
  position: relative;
  display: flex;
  // padding-top: 16px;
  // height: 100%;
  // margin-top: 48px;

  &.showSider {
    height: calc(100vh - 48px);
  }
}

.my-page {
  position: relative;
  height: 100%;
  width: 100%;
  margin: 0 auto;
  // padding: 28px 28px 0 28px;
  //border-radius: 12px 0 0 0;
  //border-top-color: #26293b;
  display: flex;
  flex-direction: column;
  background: $mainBgColor;
  overflow: hidden;
}

.chat {
  margin: 0 auto;
  width: 100%;
  background-color: #F8F8F8;
  //min-width: 500px;
  padding: 28px 0 0 0;
  flex: 1;
  overflow-y: auto;

  &.showSider {
    //height: calc(100vh - 280px);
  }

  #chat-ul {
    //padding-bottom: 20px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    background: $mainBgColor;
    overflow: hidden;
    background-color: #F8F8F8;
  }

  .avatar {
    width: 32px;
    height: 32px;
    margin-right: 16px;
  }

  .user {
    display: flex;
    flex-direction: row-reverse;
    justify-content: flex-start;
    margin-bottom: 16px;
    position: relative;

    .avatar {
      margin: 9px 0 0 16px;
    }

    .user-message-container {
      position: relative;
      margin-left: 48px;
      
      .question-text {
        padding: 13px 20px;
        font-size: 14px;
        font-weight: normal;
        line-height: 22px;
        color: #222222;
        background: #fff;
        border-radius: 12px;
        word-wrap: break-word;
        margin: 0;
      }

      .edit-mode {
        .edit-textarea-native {
          // 完全模仿原始消息框的样式和尺寸
          padding: 13px 20px;
          font-size: 14px;
          font-weight: normal;
          line-height: 22px;
          color: #222222;
          background: #fff;
          border-radius: 12px;
          border: none;
          word-wrap: break-word;
          resize: none;
          box-sizing: border-box;
          margin: 0 0 8px 0;
          width: auto;
          min-width: 100px;
          max-width: calc(100vw - 200px);
          font-family: inherit;
          overflow: hidden;
          
          &:hover {
            border: none;
            box-shadow: none;
            outline: none;
          }
          
          &:focus {
            border: none;
            box-shadow: none;
            outline: none;
          }
          
          &:active {
            border: none;
            box-shadow: none;
            outline: none;
          }
          
          &::placeholder {
            color: #999;
            opacity: 0.6;
          }
        }
        
        .edit-actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          margin-top: 8px;
          
          .arco-btn {
            height: 28px;
            padding: 0 12px;
            font-size: 12px;
          }
        }
      }

      .edit-icon {
        position: absolute;
        bottom: -8px;
        right: -8px;
        width: 24px;
        height: 24px;
        background-color: #4D71FF;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.2s ease;
        z-index: 10;
        
        svg {
          width: 12px;
          height: 12px;
          color: white;
        }
        
        &:hover {
          background-color: #3A5FFF;
        }
      }
    }

    &:hover .edit-icon {
      opacity: 1;
    }
  }

  .ai {
    margin: 16px 0px 28px 0;
    display: flex;

    img {
      margin-top: 10px;
    }

    .ai-content {
      display: flex;
      flex-direction: column;
      padding-right: 48px;
      min-width: 20%;

      .question-text {
        background: #fff;
        flex: 1;
        padding: 13px 20px;
        font-size: 14px;
        font-weight: normal;
        line-height: 22px;
        color: $title1;
        border-radius: 12px 12px 0 0;
        word-wrap: break-word;
      }

      .flashing {
        &:after {
          -webkit-animation: blink 1s steps(5, start) infinite;
          animation: blink 1s steps(5, start) infinite;
          content: '▋';
          margin-left: 0.25rem;
          vertical-align: baseline;
        }
      }

      .change-radius {
        border-radius: 12px;
      }
    }

    .source-total {
      padding: 10px 20px;
      background: #fff;
      display: flex;
      align-items: center;

      span {
        margin-right: 5px;
      }

      svg {
        width: 16px !important;
        height: 16px !important;
        cursor: pointer !important;
      }
    }

    .source-total-last {
      border-radius: 0px 0 12px 12px;
    }

    .source-list {
      background: #fff;
      border-radius: 0px 12px 12px 12px;
    }

    .data-source {
      padding: 13px 20px;
      font-size: 14px;
      line-height: 22px;
      color: $title1;

      .control {
        display: flex;
        align-items: center;
      }

      .score {
        margin-top: 26px;
      }

      .source-content {
        margin-top: 26px;
      }

      .tips {
        min-width: 78px;
        height: 22px;
        line-height: 22px;
        color: $title2;
        margin-right: 8px;
      }

      .file {
        color: $baseColor;
        margin-right: 8px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .filename-active {
        color: #5a47e5;
        text-decoration: underline;
        cursor: pointer;
      }

      svg {
        width: 14px;
        height: 14px;
        color: $baseColor;
        cursor: pointer;
      }

      a {
        color: #5a47e5;
        text-decoration: underline;
        cursor: pointer;
      }
    }

    .feed-back {
      display: flex;
      height: 20px;
      margin-top: 8px;

      .reload-box {
        display: flex;
        cursor: pointer;
        align-items: center;
        margin-right: auto;
        color: $baseColor;

        .reload-text {
          height: 22px;
          line-height: 22px;
        }
      }

      .tools {
        display: flex;
        align-items: center;

        svg {
          margin-left: 16px;
        }
      }

      svg {
        width: 16px !important;
        height: 16px !important;
        cursor: pointer !important;
      }
    }
  }
}

.stop-btn {
  display: flex;
  justify-content: center;
  padding: 18px 0;
  background-color: #F8F8F8;

  :deep(.ant-btn) {
    width: 92px;
    height: 32px;
    border: 1px solid #e2e2e2;
    color: $title2;
  }

  svg {
    width: 12px;
    height: 12px;
    margin-right: 4px;
  }

  .loading {
    animation: loading 3s infinite;
  }
}

.question-box {
  width: 100%;
  // margin: 32px 0;
  margin-bottom: 0px;

  .question {
    position: relative;
    max-width: calc(816px - $avatar-width);
    //width: 40%;
    //min-width: 550px;
    margin: 0 auto;
    display: flex;
    align-items: center;

    :deep(.ant-input-affix-wrapper) {
      width: 100%;
      max-width: 1108px;
      border-color: #e5e5e5;
      box-shadow: none !important;

      &:hover,
      &:focus,
      &:active {
        border-color: #5a47e5 !important;
        box-shadow: none !important;
      }
    }

    :deep(.ant-input:hover) {
      border-color: $baseColor;
    }

    :deep(.ant-input:focus) {
      border-color: $baseColor;
    }

    .send-box {
      position: relative;
      width: 100%;
      height: 100%;
      display: none;
      flex-direction: column;
      justify-content: flex-end;
      align-items: center;
      background-color: #fff;
      border: 1px solid #d9d9d9;
      border-radius: 18px;

      &:hover {
        border-color: $baseColor;
        transition: border-color 0.3s, height 0s;
      }

      &:not(:hover) {
        border-color: #d9d9d9;
        transition: border-color 0.3s;
      }

      &:focus {
        box-shadow: 0 0 0 2px rgba(5, 145, 255, 0.1);
      }

      .send-textarea {
        //position: absolute;
        //bottom: 0;
        min-height: 42px;
        line-height: 25px;
        padding: 11px 15px;
        display: flex;
        align-items: center;
        font-size: 14px;
        border-radius: 18px;
      }
    }

    .send-action {
      width: 100%;
      height: 40px;
      padding-right: 10px;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      color: #fff;
      z-index: 101;

      .isPreventClick {
        cursor: not-allowed !important;
      }

      .question-icon {
        cursor: pointer;
        padding: 8px;
        display: flex;
        margin-right: 16px;
        border-radius: 50%;
        background: #ffffff;
        //border: 1px solid #e5e5e5;
        color: #666666;

        &:hover {
          //border: 1px solid #5a47e5;
          background-color: #e5e5e5;
          color: $baseColor;
        }

        svg {
          width: 18px;
          height: 18px;
        }
      }

      :deep(.ant-btn-primary) {
        width: 36px;
        height: 26px;
        padding: 8px 10px 8px 8px;
        border-radius: 18px;
        display: flex;
        justify-content: center;
        align-items: center;
        background: $baseColor;
      }

      :deep(.ant-btn-primary:disabled) {
        //height: 36px;
        display: flex;
        justify-content: center;
        align-items: center;
        background: $baseColor;
        color: #fff !important;
        border-color: transparent !important;
      }

      svg {
        width: 24px;
        height: 24px;
      }
    }
  }
}

.scroll-btn-div {
  position: absolute;
  bottom: 120px;
  right: 32px;
  cursor: pointer;

  svg {
    width: 20px;
    height: 20px;
    margin-top: 5px;
  }
}

.sourceitem-leave,
// 离开前,进入后透明度是1
.sourceitem-enter-to {
  opacity: 1;
}

.sourceitem-leave-active,
.sourceitem-enter-active {
  transition: opacity 0.5s; //过度是.5s秒
}

.sourceitem-leave-to,
.sourceitem-enter {
  opacity: 0;
}

.question-container {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  padding: 0;
  margin: 0;
  border-top: 1px solid #D8D8D8;

  :deep(.full-width-textarea) {
    width: 100%;
    resize: none;
    padding-top: 20px;
  }

  :deep(.arco-textarea-wrapper) {
    width: 100%;
    margin: 0;
    padding: 0;
    background-color: #F8F8F8;
  }
}

.icon-container {
  position: absolute;
  top: 18px;
  left: 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  z-index: 20;

  .action-icon {
    font-size: 20px;
    color: #666666;
    cursor: pointer;

    &:hover {
      color: $baseColor;
    }
  }
}

.question-container-button {
  gap: 12px;
  position: absolute;
  bottom: 18px;
  right: 18px;
  display: flex;
  align-items: center;
  z-index: 20;
}

.loading-dots {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #666;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {

  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1);
  }
}
</style>
<style lang="scss">
@keyframes shake {
  0% {
    transform: rotate(0deg);
  }

  10% {
    transform: rotate(10deg);
  }

  20% {
    transform: rotate(20deg);
  }

  30% {
    transform: rotate(20deg);
  }

  40% {
    transform: rotate(20deg);
  }

  50% {
    transform: rotate(15deg);
  }

  60% {
    transform: rotate(0deg);
  }

  70% {
    transform: rotate(-15deg);
  }

  80% {
    transform: rotate(-30deg);
  }

  90% {
    transform: rotate(-15deg);
  }

  100% {
    transform: rotate(0deg);
  }
}

@keyframes blink {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes loading {
  0% {
    transform: rotate(0deg);
  }

  25% {
    transform: rotate(90deg);
  }

  50% {
    transform: rotate(180deg);
  }

  75% {
    transform: rotate(270deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.temp-file-container {
  display: flex;
  gap: 44px;
  margin: 16px 36px;

  .temp-file-item {
    position: relative;

    .temp-file-loading-container {
      position: absolute;
      top: 0;
      left: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;

      .icon-loading {
        font-size: 44px;
        color: #666666;
      }
    }

    .temp-file-item-icon {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;

      .arco-icon {
        font-size: 44px;
        color: #666666;
      }
    }

    .temp-file-item-name {
      max-width: 120px;
      text-align: center;
      margin-top: 8px;
      font-size: 14px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;

      &.status-green {
        color: #00B42A;
      }

      &.status-yellow {
        color: #FF7D00;
      }

      &.status-red {
        color: #F53F3F;
      }

      &.status-blue {
        color: #165DFF;
      }
    }
  }
}
</style>
