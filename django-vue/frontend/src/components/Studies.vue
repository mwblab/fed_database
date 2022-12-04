
<template>

    <div class="studies_container">
        <p>Step 1. choose one cohort</p>
        <label for="cohort_id">Cohort ID</label>
        <input type="text" class="form-control" id="cohort_id" v-model="cohort_id">
        <br>
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
        <label for="num_day">Day</label>
        <input type="text" class="form-control" id="num_day_id" size="4" v-model="num_day">
        <button :disabled="!fileRecordsForUpload.length" @click="uploadFiles()">
        Upload {{ fileRecordsForUpload.length }} files
        </button>
        <br>
        <p>Step 2. after uploading, calculate cohort data by hour, poke</p>
        <button :disabled=cal_running @click="calData()">Calculate</button>
        <br>
        <p>Step 3. download acquisition csv of one cohort</p>
        <p>Latest Day and Previous Day Length</p>
        <date-picker v-model="time_acq_picker" valueType="format"></date-picker>
        <input type="text" class="form-control" id="time_acq_range" size="4" v-model="time_acq_range">
        <p>Number of Pellets retrieved that day
        M: <input type="text" class="form-control" id="cri_num_p_day_m_id" size="4" v-model="cri_num_p_day_m">
        F: <input type="text" class="form-control" id="cri_num_p_day_f_id" size="4" v-model="cri_num_p_day_f">
        </p>
        <p>End of Day % Correct
        M: <input type="text" class="form-control" id="cri_end_day_acc_m_id" size="4" v-model="cri_end_day_acc_m">
        F: <input type="text" class="form-control" id="cri_end_day_acc_f_id" size="4" v-model="cri_end_day_acc_f">
        </p>
        <p>% Correct in Rolling Average of 30
        M: <input type="text" class="form-control" id="cri_max_rol_avg30_m_id" size="4" v-model="cri_max_rol_avg30_m">
        F: <input type="text" class="form-control" id="cri_max_rol_avg30_f_id" size="4" v-model="cri_max_rol_avg30_f">
        </p>
        <p>Stable to % of Pellets Yesterday
        M: <input type="text" class="form-control" id="cri_stab_yes_m_id" size="4" v-model="cri_stab_yes_m">
        F: <input type="text" class="form-control" id="cri_stab_yes_f_id" size="4" v-model="cri_stab_yes_f">
        </p>
        <button @click="getAcqTable()">Prepare Acquisition Table</button>
        <download-csv
        class   = "btn btn-default"
        :data   = "acq_table"
        name    = "acq_table.csv">
        <button class="button" :disabled=!acq_table_ready>Download csv</button>
        </download-csv>
    </div>
</template>

<script>
export default {
  data () {
    return {
      studies: [''],
      cohort_id: 1,
      num_day: 21,
      fileRecords: [],
      uploadUrl: 'http://128.173.224.170:3000/api/files/',
      // uploadHeaders: { 'X-Test-Header': 'vue-file-agent' },
      fileRecordsForUpload: [], // maintain an upload queue
      cal_running: false,
      time_acq_picker: (new Date()).getFullYear() + '-' + (new Date().getMonth() + 1) + '-' + (new Date()).getDate(),
      time_acq_range: 10,
      cri_num_p_day_m: 60,
      cri_num_p_day_f: 50,
      cri_end_day_acc_m: 0.75,
      cri_end_day_acc_f: 0.75,
      cri_max_rol_avg30_m: 0.8,
      cri_max_rol_avg30_f: 0.8,
      cri_stab_yes_m: 0.2,
      cri_stab_yes_f: 0.2,
      acq_table: [{'name': 'test'}],
      acq_table_ready: false
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
    async getAcqTable () {
      // update acq_table variable
      // update csv filename
      const sData = {}
      sData.cId = this.cohort_id
      sData.time_acq_picker = this.time_acq_picker
      sData.time_acq_range = this.time_acq_range
      sData.cri_num_p_day_m = this.cri_num_p_day_m
      sData.cri_num_p_day_f = this.cri_num_p_day_f
      sData.cri_end_day_acc_m = this.cri_end_day_acc_m
      sData.cri_end_day_acc_f = this.cri_end_day_acc_f
      sData.cri_max_rol_avg30_m = this.cri_max_rol_avg30_m
      sData.cri_max_rol_avg30_f = this.cri_max_rol_avg30_f
      sData.cri_stab_yes_m = this.cri_stab_yes_m
      sData.cri_stab_yes_f = this.cri_stab_yes_f
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sData)
      }
      const response = await fetch('http://128.173.224.170:3000/api/auto/procacq/', requestOptions)
      this.acq_table = await response.json()
      // console.log(this.acq_table)
      if (response.status === 201) {
        alert('get acq successful')
        this.acq_table_ready = 'true'
      } else {
        alert('get acq fail, please contact admin')
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
      sData.numDay = this.num_day
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
