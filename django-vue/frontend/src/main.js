// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'

import VueFileAgent from 'vue-file-agent'
import VueFileAgentStyles from 'vue-file-agent/dist/vue-file-agent.css'
// import Vuetify from 'vuetify'
// import 'vuetify/dist/vuetify.min.css' // Ensure you are using css-loader
import DatePicker from 'vue2-datepicker'
import 'vue2-datepicker/index.css'

// import bootstrap
import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)

Vue.use(VueFileAgent)
Vue.use(VueFileAgentStyles)

Vue.use(DatePicker)

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>',
  render: h => h(App)
})
