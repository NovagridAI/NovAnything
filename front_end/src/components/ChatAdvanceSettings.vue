<template>
  <div class="settings-popover">
    <h3>高级参数</h3>
    
    <div class="param-item">
      <div class="param-header">
        <span>创意活跃度</span>
        <arco-tooltip content="控制回答的创意程度">
          <icon-question-circle />
        </arco-tooltip>
      </div>
      <div class="param-control">
        <arco-slider :default-value="0.7" :min="0" :max="1" :step="0.1" />
        <arco-input-number :min="0" :max="1" :step="0.1" :default-value="0.7" />
      </div>
    </div>
    
    <div class="param-item">
      <div class="param-header">
        <span>思维开放度</span>
        <arco-tooltip content="控制回答的多样性">
          <icon-question-circle />
        </arco-tooltip>
      </div>
      <div class="param-control">
        <arco-slider :default-value="1.0" :min="0" :max="1" :step="0.1" />
        <arco-input-number :min="0" :max="1" :step="0.1" :default-value="1.0" />
      </div>
    </div>
    
    <div class="param-item">
      <div class="param-header">
        <span>表述发散度</span>
        <arco-tooltip content="控制回答的发散程度">
          <icon-question-circle />
        </arco-tooltip>
      </div>
      <div class="param-control">
        <arco-slider :default-value="0.0" :min="0" :max="1" :step="0.1" />
        <arco-input-number :min="0" :max="1" :step="0.1" :default-value="0.0" />
      </div>
    </div>
    
    <div class="param-item">
      <div class="param-header">
        <span>词汇丰富度</span>
        <arco-tooltip content="控制词汇的多样性">
          <icon-question-circle />
        </arco-tooltip>
      </div>
      <div class="param-control">
        <arco-slider :default-value="0.0" :min="0" :max="1" :step="0.1" />
        <arco-input-number :min="0" :max="1" :step="0.1" :default-value="0.0" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { IconQuestionCircle } from '@arco-design/web-vue/es/icon';
</script>

<style lang="scss" scoped>
.settings-popover {
  width: 320px;
  padding: 8px;
  
  h3 {
    margin-top: 0;
    margin-bottom: 16px;
    font-size: 16px;
    font-weight: 500;
  }
  
  .param-item {
    margin-bottom: 16px;
    
    .param-header {
      display: flex;
      align-items: center;
      margin-bottom: 4px;
      
      span {
        font-weight: 500;
        margin-right: 4px;
      }
    }
    
    .param-control {
      display: flex;
      align-items: center;
      
      :deep(.arco-slider) {
        flex: 1;
        margin-right: 16px;
      }
      
      :deep(.arco-input-number) {
        width: 70px;
      }
    }
  }
}
</style> 