
<template>

    <div class="studies_container">
        <VueFileAgent
          ref="vueFileAgent"
          :theme="'list'"
          :multiple="true"
          :deletable="false"
          :meta="true"
          :accept="'.csv'"
          :maxSize="'500MB'"
          :maxFiles="50"
          :helpText="'Choose fed raw csv files. Can be multiple day (as long as the dates in csv files is correct).'"
          :errorText="{
            type: 'Invalid file type. Only csv Allowed',
            size: 'Files should not exceed 500MB in size',
          }"
          @select="filesSelected($event)"
          v-model="fileRecords"
        ></VueFileAgent>
        <label for="cohort_id">Cohort ID</label>
        <input type="text" class="form-control" id="title" v-model="cohort_id">
        <button :disabled="!fileRecordsForUpload.length" @click="uploadFiles()">
        Upload {{ fileRecordsForUpload.length }} files
        </button>

        <br>
        <br>
        <p>after uploading, compute cohort data by hour, poke</p>
        <button :disabled=cal_running @click="calData()">Calculate</button>
        <!--
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
          !-->
    </div>
</template>

<script>
export default {
  data () {
    return {
      studies: [''],
      title: '',
      description: '',
      cohort_id: 1,
      fileRecords: [],
      uploadUrl: 'http://128.173.224.170:3000/api/files/',
      // uploadHeaders: { 'X-Test-Header': 'vue-file-agent' },
      fileRecordsForUpload: [], // maintain an upload queue
      cal_running: false
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
        const data = await response.json()
        this.studies.push(data)
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
    },
    async calData () {
      const sData = {}
      sData.cId = this.cohort_id
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sData)
      }
      const response = await fetch('http://128.173.224.170:3000/api/auto/proccal/', requestOptions)
      if (response.status === 201) {
        alert('calculate successful')
      } else {
        alert('fail, please contact admin')
      }
    },
    // for uploader
    async uploadFiles () {
      // Using the default uploader. You may use another uploader instead.
      let result = await this.$refs.vueFileAgent.upload(this.uploadUrl, this.uploadHeaders, this.fileRecordsForUpload)
      // Reset queue
      this.fileRecordsForUpload = []

      // Execute data load, (be atomic)
      const sData = {}
      sData.fileList = []
      for (var i = 0; i < result.length; i++) {
        sData.fileList.push(result[i].data.name)
      }
      sData.cId = this.cohort_id
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sData)
      }
      console.log(requestOptions)
      const response = await fetch('http://128.173.224.170:3000/api/auto/procdl/', requestOptions)
      if (response.status === 201) {
        alert('upload successful')
      } else {
        alert('fail, please upload again')
      }
    },
    // add files to queue
    filesSelected: function (fileRecordsNewlySelected) {
      var validFileRecords = fileRecordsNewlySelected.filter((fileRecord) => !fileRecord.error)
      this.fileRecordsForUpload = this.fileRecordsForUpload.concat(validFileRecords)
    },
    // delete related function
    onBeforeDelete: function (fileRecord) {
      var i = this.fileRecordsForUpload.indexOf(fileRecord)
      if (i !== -1) {
        this.fileRecordsForUpload.splice(i, 1)
        var k = this.fileRecords.indexOf(fileRecord)
        if (k !== -1) this.fileRecords.splice(k, 1)
      } else {
        if (confirm('Are you sure you want to delete?')) {
          this.$refs.vueFileAgent.deleteFileRecord(fileRecord)
        }
      }
    },
    deleteUploadedFile: function (fileRecord) {
      // Using the default uploader.
      // this.$refs.vueFileAgent.deleteUpload(this.uploadUrl, this.uploadHeaders, fileRecord)
    },
    fileDeleted: function (fileRecord) {
      var i = this.fileRecordsForUpload.indexOf(fileRecord)
      if (i !== -1) {
        this.fileRecordsForUpload.splice(i, 1)
      } else {
        this.deleteUploadedFile(fileRecord)
      }
    }
  },
  created () {
    // Fetch tasks on page load
    this.getData()
  }
}
</script>
