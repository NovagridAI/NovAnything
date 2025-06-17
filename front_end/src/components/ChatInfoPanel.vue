<!--
 * @Author: Ianarua 306781523@qq.com
 * @Date: 2024-07-29 10:00:43
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-05 16:08:44
 * @FilePath: front_end/src/components/ChatInfoPanel.vue
 * @Description: ai对话的消耗token和耗时, 还有当时对话的模型信息
 -->
<template>
  <div class="content">
    <div class="content-container">
      {{ outerInfo }}
      <arco-tooltip placement="bottom" color="#666666" overlay-class-name="tooltip-class" @click="openInfoModal">
        <template #content>
          <span>{{ common.modelInfoView }}</span>
        </template>
        <icon-question-circle />
      </arco-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { IChatItemInfo } from '@/utils/types';
import { formatTimestamp } from '@/utils/utils';
import SvgIcon from '@/components/SvgIcon.vue';
import { TypographyParagraph } from 'ant-design-vue';
import { Modal } from '@arco-design/web-vue'
import { IconQuestionCircle } from '@arco-design/web-vue/es/icon';
import { getLanguage } from '@/language';

const { common } = getLanguage();

interface IProps {
  chatItemInfo: IChatItemInfo;
}

const props = defineProps<IProps>();

const {
  timeInfo: timeInfoOrigin,
  tokenInfo,
  settingInfo: settingInfoOrigin,
  dateInfo: dateInfoOrigin,
} = toRefs(props.chatItemInfo);

const INFO_MAP = {
  // 时间相关
  'preprocess': '预处理',
  'condense_q_chain': '问题思考链',
  'retriever_search': '检索搜索',
  'web_search': '网络搜索',
  'rerank': '重排序',
  'reprocess': '重新处理',
  'llm_first_return': '语言模型首次返回',
  'first_return': '首次返回',
  'llm_completed': '语言模型完成',
  'obtain_images_time': '图片获取',
  'chat_completed': '聊天完成',

  // 模型相关
  'apiBase': '接口地址',
  'apiContextLength': '上下文长度',
  'apiKey': '接口密钥',
  'apiModelName': '模型名称',
  'context': '上下文',
  'maxToken': '最大Token',
  'temperature': '温度',
  'top_P': '采样率',
  'rewrite_completion_tokens': '重写完成Token数',
  'rewrite_prompt_tokens': '重写提示Token数',
  'tokens_per_second': '每秒Token数',

  // 其他信息
  'total_tokens': '总Token数',
  'prompt_tokens': '提示Token数',
  'completion_tokens': '完成Token数',
  'Model name': '模型名称',
  'date': '日期'
};

// 需要展示的time信息
const TIMEINFO = new Set([
  'preprocess',
  'condense_q_chain',
  'retriever_search',
  'web_search',
  'rerank',
  'reprocess',
  'llm_first_return',
  'first_return',
  'llm_completed',
  'obtain_images_time',
  'chat_completed',
]);

// 需要展示的模型信息
const MODELINFO = new Set([
  'apiBase',
  'apiContextLength',
  'apiKey',
  'apiModelName',
  'context',
  'maxToken',
  'temperature',
  'top_P',
]);

// 外层展示的所有信息
const OUTERINFO = new Set([
  'first_return',
  'chat_completed',
  'total_tokens',
  'prompt_tokens',
  'completion_tokens',
  'Model name',
  'date',
]);

// time会有多余的值传过来，所以需要过滤一下
const timeInfo = computed(() => {
  const obj = {};
  for (let i in timeInfoOrigin.value) {
    if (TIMEINFO.has(i)) {
      obj[i] = `${timeInfoOrigin.value[i].toFixed(2)}s`;
    }
  }
  return obj;
});

// 转换模型配置的格式，变为名称，处理模型能力
const settingInfo = computed(() => {
  // 获取名称（中、英）
  const getLabel = (key: string) => {
    return common[key + 'Label'];
  };
  const obj = {};
  for (let i in settingInfoOrigin.value) {
    if (MODELINFO.has(i)) {
      obj[getLabel(i)] = settingInfoOrigin.value[i];
    }
  }
  return obj;
});

// 格式化时间戳，变为2024/8/1 12:30:12 的格式
const dateInfo = computed(() => {
  return formatTimestamp(dateInfoOrigin.value);
});

// 将所有的信息整理到一个对象中
const infoObj = computed(() => {
  return {
    ...timeInfo.value,
    ...tokenInfo.value,
    ...settingInfo.value,
    date: dateInfo.value,
  };
});

// 过滤出外层展示的信息
const outerInfo = computed(() => {
  const obj = {};
  for (let i in infoObj.value) {
    if (OUTERINFO.has(i)) {
      obj[i] = infoObj.value[i];
    }
  }
  return formatInfo(obj);
});

const formatInfo = <T>(obj: T) => {
  return Object.entries(obj)
    .map(([key, value]) => `${INFO_MAP?.[key] ?? key}: ${value}`)
    .join(', ');
};

// 打开详细信息
const openInfoModal = () => {
  const formatTimeInfo = (timeData, keys) => {
    let formattedString = '';
    keys.forEach((key, index) => {
      formattedString += `${INFO_MAP?.[key] ?? key}: ${timeData[key]}`;
      if (index < keys.length - 1) {
        formattedString += ' + ';
      }
    });
    return formattedString;
  };
  Modal.info({
    title: `${common.modelInfoTitle}`,
    content: h('div', { style: { 'user-select': 'text' } }, [
      h(TypographyParagraph, {}, () => `${common.modelInfoTime}: ${formatInfo(timeInfo.value)}`),
      // h(
      //   TypographyParagraph,
      //   { mark: true },
      //   () => `${common.note}：${formatTimeInfo(
      //     timeInfo.value,
      //     [...TIMEINFO.values()].slice(0, 7)
      //   )} = first_return: ${timeInfo.value['first_return']}
      //   + 语言模型完成${timeInfo.value['llm_completed']}
      //   + obtain_images_time: ${timeInfo.value['obtain_images_time'] || '0.00s'}
      //   = chat_completed：${timeInfo.value['chat_completed']}`
      // ),
      h(TypographyParagraph, {}, () => `${common.modelInfoToken}: ${formatInfo(tokenInfo.value)}`),
      h(TypographyParagraph, {}, () => [
        `${common.modelInfoSetting}：`,
        ...Object.entries(settingInfo.value).map(([key, value]) => {
          if (key === 'API密钥' || key === 'API路径') return
          return h(TypographyParagraph, {}, () => `${key}: ${value}`)
        }
        ),
      ]),
    ]),
    width: '30%',
    maskClosable: true,
    centered: true,
  });
};
</script>

<style lang="scss" scoped>
.content {

  .arco-icon {
    font-size: 16px;
    color: $baseColor;
    cursor: pointer;
    margin-left: 6px;
  }



  .content-container {
    display: flex;
    font-size: 12px;
    color: #666;
    margin-top: 10px;
    border-top: 1px solid #999;
    justify-content: flex-start;
    align-items: center;
  }


  .tooltip-class {
    width: 500px !important;
  }
}
</style>
