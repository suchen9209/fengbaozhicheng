<template>
  <div class="home">
    <h1>风暴之城蓝图助手</h1>
    <p>AI驱动的决策支持工具</p>
    <el-button type="primary" @click="$router.push('/analyze')">
      开始分析
    </el-button>
    <el-button @click="$router.push('/history')">
      查看历史
    </el-button>
  </div>
</template>

<script setup lang="ts">
// Home view component
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 20px;
  padding: 20px;
}

h1 {
  font-size: 2.5rem;
  color: #333;
  text-align: center;
}

p {
  font-size: 1.2rem;
  color: #666;
  text-align: center;
}

/* Mobile responsive styles */
@media (max-width: 768px) {
  .home {
    gap: 16px;
    padding: 16px;
  }

  h1 {
    font-size: 1.8rem;
  }

  p {
    font-size: 1rem;
  }

  .el-button {
    width: 100%;
    max-width: 300px;
  }
}

@media (max-width: 480px) {
  h1 {
    font-size: 1.5rem;
  }

  p {
    font-size: 0.9rem;
  }
}
</style>
