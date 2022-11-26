
<template>
    <div class="studies_container">
        <div class="add_study">
            <form v-on:submit.prevent="submitForm">
                <div class="form-group">
                <label for="title">Title</label>
                <input type="text" class="form-control" id="title" v-model="title">
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea class="form-control" id="description" v-model="description"></textarea>
            </div>
            <div class="form-group">
                <button type="submit">Add Study</button>
            </div>
        </form>
    </div>

        <div class="studies_content">
            <h1>Studies</h1>
            <ul class="studies_list">
                <li v-for="stu in studies" :key="stu.id">

                    <h2>{{ stu.studyDisplayName }}</h2>
                    <p>{{ stu.id }}</p>

                    <button @click="toggleTask(stu)">
                    toggle
                    </button>

                    <button @click="deleteTask(stu)">Delete</button>
                </li>

            </ul>
        </div>
    </div>
</template>

<script>
export default {
  data () {
    return {
      studies: [''],
      title: '',
      description: ''
    }
  },
  methods: {
    async getData () {
      try {
        // fetch tasks
        const response = await fetch('http://128.173.224.170:3000/api/auto/')
        // set the data returned as tasks
        this.studies = await response.json()
      } catch (error) {
        // log the error
        console.log(error)
      }
    },
    async submitForm () {
      try {
        // const article = { title: 'Vue POST Request Example', description: 'a desc', completed: false }
        // const response = await axios.post('http://128.173.224.170:3000/api/auto/', article)
        const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: 10, studyDisplayName: 'new study', studyDesc: 'new desc', startDate: '2022-11-24', endDate: '2022-11-24' })
        }

        console.log('to send post')
        const response = await fetch('http://128.173.224.170:3000/api/auto/', requestOptions)
        // const response = await this.$http.post('http://128.173.224.170:3000/api/auto/', {
        // studyDisplayName: this.title,
        //  studyDesc: this.description,
        //  completed: false
        // })
        const data = await response.json()

        this.studies.push(data)
        // this.title = ''
        // this.description = ''
      } catch (error) {
        console.log(error)
      }
    },
    async toggleTask (stu) {
      try {
        const requestOptions = {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: 10, studyDisplayName: 'PUT new study', studyDesc: 'PUT new desc', startDate: '2022-11-24', endDate: '2022-11-24' })
        }
        const response = await fetch(`http://128.173.224.170:3000/api/auto/${stu.id}/`, requestOptions)
        const data = await response.json()
        let taskIndex = this.studies.findIndex(t => t.id === stu.id)
        this.studies = this.studies.map((stu) => {
          if (this.studies.findIndex(t => t.id === stu.id) === taskIndex) {
            return data
          }
          return stu
        })
      } catch (error) {
        console.log(error)
      }
    }
  },
  created () {
    // Fetch tasks on page load
    this.getData()
  }
}
</script>
