import { createApp } from 'vue'
import './assets/base.css'
import { RouterView } from 'vue-router'
import router from './router'

const app = createApp(RouterView)

app.use(router)

app.mount('#app')
