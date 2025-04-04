
<template>
    <div class="studies_container">

        <b-container class="bv-example-cohort">
           <b-row align-h="center">
                <b-col sm="2">
                    <b-dropdown variant="outline-primary" class="m-2" :text="dropdown_cohort_text" v-if="options.length > 0">
                         <b-dropdown-item v-for="option in options" :key="option.cohort_id" :value="option.cohort_id" @click="setCohort(option.cohort_id, option.cohort_name)">{{ 'Cohort: ' + option.cohort_name }}</b-dropdown-item>
                    </b-dropdown>
                </b-col>
           </b-row>
        </b-container>

        <br>
        <div v-if="cohort_id > 0">
        <VueFileAgent
          ref="vueFileAgent"
          :theme="'list'"
          :multiple="true"
          :deletable="false"
          :meta="true"
          :accept="'.csv'"
          :maxSize="'500MB'"
          :maxFiles="100"
          :helpText="'Choose fed raw csv files. '"
          :errorText="{
            type: 'Invalid file type. Only csv Allowed',
            size: 'Files should not exceed 500MB in size',
          }"
          @select="filesSelected($event)"
          v-model="fileRecords"
        ></VueFileAgent>
        <b-container class="bv-example-day">

        <div v-if="req_upload_loading">
             <b-button variant="primary" disabled>
                 <b-spinner small></b-spinner>
                 <span class="sr-only">Loading...</span>
             </b-button>
        </div>
        <div v-else>
          <b-button id="upload_but" pill variant="primary" :disabled="!fileRecordsForUpload.length" @click="uploadFiles()">
          Upload {{ fileRecordsForUpload.length }} files
          </b-button>
          <b-button id="upload_doc" pill :pressed="true" variant="outline-info">Supported Format</b-button>
          <b-popover target="upload_doc" triggers="hover">
          <template #title>Supported uploaded format</template>
          <p>Supported filename: FEDXXX_MMDDYY_XX_DX_CODE.csv <span class="text-danger">All characters in the filename should be capitalized. (except .csv)</span></p> <p>Supported CODE (test type): <strong>'FR1', 'FR3', '3R', 'PR', '3R_PR', 'PR_X', '3R_PR_X', 'QU', '3R_QU', 'QU_X', '3R_QU_X', 'E', 'RE', 'FF', 'FR5'</strong></p>
          </b-popover>
        </div>
        </b-container>

       <b-container fluid>
       <b-row class="mt-2 justify-content-md-center">
       <b-col sm="6">
         <b-form-textarea
           id="upload_error_textarea"
           v-model="upload_error_msgs"
           placeholder="Upload progress messages"
           plaintext
           rows="4"
         ></b-form-textarea>
       </b-col>
       </b-row>
       </b-container>

        <br>
        <!--<p>Step 2. after uploading, calculate cohort data by hour, poke</p>!-->
        <div v-if="req_cal_loading">
             <b-button variant="primary" disabled>
                 <b-spinner small></b-spinner>
                 <span class="sr-only">Loading...</span>
             </b-button>
        </div>
        <div v-else>
            <b-button pill variant="primary" :disabled=cal_running @click="calData()">Calculate</b-button>
            <br />
            * Calculate can only be run by one person. Running Calculate in parallel will cause incorrect results.
        </div>
        <br>
        <!--<p>Step 3. download acquisition csv of one cohort</p>!-->
        <br>

        <b-container class="bv-example-cri">

          <b-row align-h="center">
            <b-col sm="4">Latest Day</b-col>
            <b-col sm="2">
              <date-picker v-model="time_acq_picker" valueType="format"></date-picker>
            </b-col>
            <b-col sm="2">
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4">Number of Previous Days</b-col>
            <b-col sm="2">
              <b-form-input type="number" class="form-control" size="sm" id="time_acq_range" v-model="time_acq_range"></b-form-input>
            </b-col>
            <b-col sm="2">
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4">Filter out Test Type</b-col>
            <b-col sm="2">
              <b-form-select v-model="filter_selected" :options="filter_options"></b-form-select>
            </b-col>
            <b-col sm="2">
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4"></b-col>
            <b-col sm="2">M
            </b-col>
            <b-col sm="2">F
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4">Number of Pellets retrieved that day</b-col>
            <b-col sm="2">
            <b-form-input type="number" class="form-control" size="sm" id="cri_num_p_day_m_id" v-model="cri_num_p_day_m"></b-form-input>
            </b-col>
            <b-col sm="2">
            <b-form-input type="number" class="form-control" size="sm" id="cri_num_p_day_f_id" v-model="cri_num_p_day_f"></b-form-input>
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4">% Correct in the End of Day</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_end_day_acc_m_id" v-model="cri_end_day_acc_m"></b-form-input>
            </b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_end_day_acc_f_id" v-model="cri_end_day_acc_f"></b-form-input>
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4">% Correct in Rolling Average of 30 (CumAcc)</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_max_rol_avg30_m_id" v-model="cri_max_rol_avg30_m"></b-form-input>
            </b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_max_rol_avg30_f_id" v-model="cri_max_rol_avg30_f"></b-form-input>
            </b-col>
          </b-row>

          <b-row align-h="center">
            <b-col sm="4">Stable to % of Pellets Yesterday</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_stab_yes_m_id" v-model="cri_stab_yes_m"></b-form-input>
            </b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_stab_yes_f_id" v-model="cri_stab_yes_f"></b-form-input>
            </b-col>
          </b-row>

          <br>

          <b-row align-h="center">
            <b-col sm="4">Pellet Retrieval Time threshold</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_rt_thres_m_id" v-model="cri_rt_thres_m"></b-form-input>
            </b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_rt_thres_f_id" v-model="cri_rt_thres_f"></b-form-input>
            </b-col>
          </b-row>

          <br>

          <b-row align-h="center">
            <b-col sm="4">X% Correct in a Rolling Window of Y (Poke)</b-col>
            <b-col sm="2">
            </b-col>
            <b-col sm="2">
            </b-col>
          </b-row>
          <b-row align-h="center">
            <b-col sm="4">X% correct</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_rol_poke_m_id" v-model="cri_rol_poke_m"></b-form-input>
            </b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_rol_poke_f_id" v-model="cri_rol_poke_f"></b-form-input>
            </b-col>
          </b-row>
          <b-row align-h="center">
            <b-col sm="4">Window Y</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="cri_rol_poke_w_size_id" v-model="cri_rol_poke_w_size"></b-form-input>
            </b-col>
            <b-col sm="2">
            </b-col>
          </b-row>

          <br>

          <b-row align-h="center">
            <b-col sm="4">Exported excel filename</b-col>
            <b-col sm="2">
            <b-form-input type="text" class="form-control" size="sm" id="acq_table_export_filename_id" v-model="acq_table_export_filename"></b-form-input>
            </b-col>
            <b-col sm="2">
            </b-col>
          </b-row>

        </b-container>

        <br>
        <div v-if="req_acq_loading">
             <b-button pill variant="outline-secondary" disabled>
                 <b-spinner small></b-spinner>
                 <span class="sr-only">Loading...</span>
             </b-button>
        </div>
        <div v-else>
             <b-button pill variant="outline-secondary" @click="getAcqTable()">Show Acquisition Table</b-button>
             <!-- refactor from csv to xlsx -->
             <!-- https://docs.sheetjs.com/docs/demos/frontend/vue -->
             <!-- https://github.com/SheetJS/sheetjs/issues/664 -->
             <b-button pill variant="primary" class="button" @click="exportFile">Export XLSX</b-button>
        </div>

        <br>
        <div v-if="acq_table_ready">
          <b-table hover :items="acq_table_disp"></b-table>
          <b-table hover :items="acq_table_test_type"></b-table>
        </div>

        </div>

        <footer class="footer">
          <p>&copy; 2024 Fed Database v1.0.2-alpha. If there are any issues, please contact chinhui@vt.edu.</p>
        </footer>

    </div>
</template>

<script>
import { utils, writeFileXLSX } from 'xlsx'

export default {
  data () {
    return {
      studies: [''],
      cohort_id: -1,
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
      cri_rt_thres_m: 0,
      cri_rt_thres_f: 0,
      cri_rol_poke_m: 0.85,
      cri_rol_poke_f: 0.85,
      cri_rol_poke_w_size: 30,
      acq_table_tabs: [{'name': 'test'}],
      acq_table_disp: [],
      acq_table_test_type: [],
      acq_table_ready: false,
      acq_table_export_filename: 'acq_table',
      // for dropdown cohort list
      options: [],
      dropdown_cohort_text: 'Select Cohort',
      req_upload_loading: false,
      req_cal_loading: false,
      req_acq_loading: false,
      filter_selected: 'ALL',
      filter_options: [
        { value: 'ALL', text: 'Show All' },
        { value: 'FR1', text: 'FR1' },
        { value: 'FR3', text: 'FR3' },
        { value: '3R', text: '3R' },
        { value: 'PR', text: 'PR' },
        { value: '3R_PR', text: '3R_PR' },
        { value: 'QU', text: 'QU' },
        { value: '3R_QU', text: '3R_QU' },
        { value: 'E', text: 'E' },
        { value: 'RE', text: 'RE' },
        { value: 'FF', text: 'FF' },
        { value: 'FR5', text: 'FR5' }
      ],
      upload_error_msgs: null
    }
  },
  methods: {
    async setCohort (num, name) {
      this.cohort_id = num
      this.dropdown_cohort_text = 'Cohort: ' + name
    },
    makeToast (msg, append = true) {
      this.$bvToast.toast(msg, {
        title: 'Notification',
        appendToast: append,
        // noAutoHide: true,
        autoHideDelay: 8000,
        variant: 'primary'
      })
    },
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
      this.req_cal_loading = true
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sData)
      }
      const response = await fetch('http://128.173.224.170:3000/api/auto/proccal/', requestOptions)
      this.req_cal_loading = false
      if (response.status === 201) {
        await this.makeToast('Calculate: Successful!')
      } else {
        const edata = await response.json()
        await this.makeToast('Calculate: Failed! Error message: ' + edata.message)
      }
    },
    async getAcqTable () {
      // update acq_table variable
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
      sData.cri_rt_thres_m = this.cri_rt_thres_m
      sData.cri_rt_thres_f = this.cri_rt_thres_f
      sData.cri_filter_test_type = this.filter_selected
      sData.cri_rol_poke_m = this.cri_rol_poke_m
      sData.cri_rol_poke_f = this.cri_rol_poke_f
      sData.cri_rol_poke_w_size = this.cri_rol_poke_w_size
      this.req_acq_loading = true
      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sData)
      }
      const response = await fetch('http://128.173.224.170:3000/api/auto/procacq/', requestOptions)
      // console.log(this.acq_table)
      this.req_acq_loading = false
      if (response.status === 201) {
        // prepare acq disp
        this.acq_table_disp = []
        this.acq_table_test_type = []
        this.acq_table_tabs = await response.json()
        this.acq_table = this.acq_table_tabs[0][0]
        for (let i = 0; i < this.acq_table.length; i++) {
          if (this.acq_table[i]['fed'] === 'pseufed') {
            continue
          }

          var keys = Object.keys(this.acq_table[i])
          var tmpRow = Object.assign({}, this.acq_table[i])
          if (this.acq_table[i].data_type === 'acq_table') {
            // console.log(this.acq_table[i])

            // remove unnecessary cols
            delete tmpRow['data_type']
            delete tmpRow['threshold']
            // iter keys
            tmpRow['_cellVariants'] = []
            for (let j = 0; j < keys.length; j++) {
              if (keys[j].slice(-1) === ' ') {
                delete tmpRow[keys[j]]
              } else if (keys[j].slice(0, 1) === 'd') {
                if (parseInt(tmpRow[keys[j]]) === 1) {
                  tmpRow['_cellVariants'][keys[j]] = 'success'
                }
              }
            }
            // push to disp
            this.acq_table_disp.push(tmpRow)
          } else if (this.acq_table[i].data_type === 'test_type') {
            // remove unnecessary cols
            delete tmpRow['data_type']
            delete tmpRow['threshold']
            // iter keys
            tmpRow['_cellVariants'] = []
            for (let j = 0; j < keys.length; j++) {
              if (keys[j].slice(0, 1) === 'd') {
                if (tmpRow[keys[j]]) {
                  tmpRow['_cellVariants'][keys[j]] = 'warning'
                }
              }
            }
            // push to test type
            this.acq_table_test_type.push(tmpRow)
          }
        }
        await this.makeToast('Show: Successful!')
        this.acq_table_ready = 'true'
      } else {
        const edata = await response.json()
        await this.makeToast('Show: Failed! Error message: ' + edata.message)
      }
    },
    /* get state data and export to XLSX */
    async exportFile () {
      this.acq_table_tabs = ''
      await this.getAcqTable()
      if (this.acq_table_tabs !== '') {
        const wb = utils.book_new()
        if (this.filter_selected !== 'ALL') {
          const ws4 = utils.json_to_sheet(this.acq_table_tabs[1][0])
          utils.book_append_sheet(wb, ws4, this.filter_selected + '_Data1')
          const ws5 = utils.json_to_sheet(this.acq_table_tabs[1][1])
          utils.book_append_sheet(wb, ws5, this.filter_selected + '_Data2')
          const ws6 = utils.json_to_sheet(this.acq_table_tabs[1][2])
          utils.book_append_sheet(wb, ws6, this.filter_selected + '_Data3')
        }

        const ws1 = utils.json_to_sheet(this.acq_table_tabs[0][0])
        utils.book_append_sheet(wb, ws1, 'All_Data1')
        const ws2 = utils.json_to_sheet(this.acq_table_tabs[0][1])
        utils.book_append_sheet(wb, ws2, 'All_Data2')
        const ws3 = utils.json_to_sheet(this.acq_table_tabs[0][2])
        utils.book_append_sheet(wb, ws3, 'All_Data3')
        const ws4 = utils.json_to_sheet(this.acq_table_tabs[0][3])
        utils.book_append_sheet(wb, ws4, 'All_Data4')

        const ws7 = utils.json_to_sheet(this.acq_table_tabs[2][0])
        utils.book_append_sheet(wb, ws7, 'Metadata')

        writeFileXLSX(wb, this.acq_table_export_filename + '.xlsx')
      }
    },
    // for uploader
    async uploadFiles () {
      this.req_upload_loading = true

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
      this.req_upload_loading = false
      if (response.status === 201) {
        // await this.makeToast('Upload: Successful!')
        this.upload_error_msgs = 'Upload: Successful!'
      } else {
        const edata = await response.json()
        // await this.makeToast('Upload: Failed! Error message: ' + edata.message)
        this.upload_error_msgs = edata.error + '\n' + edata.message + '\n'
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
  },
  mounted () {
    // Make the request to fetch the options
    fetch('http://128.173.224.170:3000/api/auto/get_cohort_list/')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        return response.json()
      })
      .then(data => {
        this.options = data
      })
      .catch(error => {
        console.error('There was a problem fetching the options:', error)
      })
  }
}
</script>
