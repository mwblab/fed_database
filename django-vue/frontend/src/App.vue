<template>
  <div id="app">
    <Studies />
  </div>
</template>

<script>
import Studies from './components/Studies.vue'
export default {
  name: 'App',
  components: {
    Studies
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
