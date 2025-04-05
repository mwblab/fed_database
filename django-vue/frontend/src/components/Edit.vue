<template>
    <div class="edit_container">
        <h2>Edit Mouse Data</h2>
        <b-container class="bv-example-cohort">
            <b-row align-h="center">
                <b-col sm="2">
                    <b-dropdown variant="outline-primary" class="m-2" :text="dropdown_cohort_text"
                        v-if="options.length > 0">
                        <b-dropdown-item v-for="option in options" :key="option.cohort_id" :value="option.cohort_id"
                            @click="setCohort(option.cohort_id, option.cohort_name)">{{ "Cohort: " + option.cohort_name
                            }}</b-dropdown-item>
                    </b-dropdown>
                </b-col>
            </b-row>
            <b-row align-h="center" v-if="this.selectedOption > 0">
                <b-col sm="4" class="mt-3">
                    Upload Prefill File<input type="file" @change="handlePrefillFileUpload($event)" />
                    <b-button id="upload_doc" pill :pressed="true" variant="outline-info">Upload Format</b-button>
                    <b-popover target="upload_doc" triggers="hover">
                    <template #title>Excel .xlsx file</template>
                    <table border="1" cellpadding="8" cellspacing="0">
  <thead>
    <tr>
      <th>FED</th>
      <th>Mouse Name</th>
      <th>Sex</th>
      <th>Genotype</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>FED005</td>
      <td>CC1</td>
      <td>1</td>
      <td>WT</td>
    </tr>
    <tr>
      <td>FED010</td>
      <td>CC2</td>
      <td>1</td>
      <td>WT</td>
    </tr>
  </tbody>
</table>
                    </b-popover>
                </b-col>
            </b-row>
        </b-container>

        <b-table v-if="mouse_list.length > 0" hover :items="mouse_list" :fields="fields">
            <template v-for="field in editableFields" v-slot:[`cell(${field.key})`]="{ item }">
                <b-input v-bind:key="field.key" v-model="item[field.key]" />
            </template>
        </b-table>
        <p v-if="mouse_list.length > 0">
            Sex: Set 1 (Male) or 2 (Female) to show on the acquisition result. Set 0
            if no show.
        </p>
        <button v-if="mouse_list.length > 0" v-on:click="saveMouseList">
            Save Mouse Data
        </button>

        <br />
        <br />
        <div v-if="mouse_list.length > 0">
            <p>Delete mouse data</p>
            <input id="del_mouse_id" type="text" :style="{ width: '300px' }" v-model="del_mouse_id"
                placeholder="Mouse ID from the table below (E.g. 81)" />
            <input id="del_start_day" type="text" :style="{ width: '100px' }" v-model="del_start_day"
                placeholder="Start day: 30" />
            <input id="del_end_day" type="text" :style="{ width: '100px' }" v-model="del_end_day"
                placeholder="End day: 35" />
            <button v-if="del_mouse_id && del_start_day && del_end_day" v-on:click="delMouseData">
                Delete Mouse Data
            </button>
        </div>

        <hr />
        <hr />

        <h2>Add New Cohort</h2>
        <input id="new_cohort" type="text" :style="{ width: '250px' }" v-model="new_cohort_name"
            placeholder="New Cohort Name (20chars)" />
        <button v-if="new_cohort_name" v-on:click="addNewCohort">Add</button>

        <hr />
        <hr />

        <h2>Remove Cohort</h2>
        <input id="rm_cohort" type="text" :style="{ width: '250px' }" v-model="rm_cohort_name"
            placeholder="Remove Cohort Name (20chars)" />
        <button v-if="rm_cohort_name" v-on:click="RmCohort">Remove</button>
    </div>
</template>

<script>
export default {
  computed: {
    editableFields () {
      return this.fields.filter((field) => field.editable)
    }
  },
  data () {
    return {
      // for cohort dropdown list
      selectedOption: null,
      options: [],
      dropdown_cohort_text: 'Select Cohort',
      // for mouse list
      mouse_list: [],
      fields: [
        { key: 'mouse_id', label: 'ID' },
        { key: 'mouse_FED', label: 'FED' },
        { key: 'mouse_name', label: 'Mouse Name', editable: true },
        { key: 'mouse_sex', label: 'Sex', editable: true },
        { key: 'mouse_genotype', label: 'Genotype', editable: true },
        { key: 'mouse_FED_day', label: 'FED_DAY', tdClass: 'fed_day_sty' }
      ],
      // add new cohort
      new_cohort_name: null,
      rm_cohort_name: null,
      // del mouse data
      del_mouse_id: null,
      del_start_day: null,
      del_end_day: null
    }
  },
  methods: {
    async setCohort (num, name) {
      this.selectedOption = num
      this.dropdown_cohort_text = 'Cohort: ' + name
      await this.updateMouseList(num)
    },
    async refreshMouseList () {
      await this.updateMouseList(this.selectedOption)
    },
    async updateMouseList (num) {
      try {
        const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cohort_id: num })
        }
        const response = await fetch(
          'http://128.173.224.170:3000/api/auto/get_mouse_list/',
          requestOptions
        )
        const data = await response.json()
        this.mouse_list = data
      } catch (error) {
        console.log(error)
      }
    },
    async delMouseData () {
      if (
        confirm(
          'Are you sure? Delete Mouse ID=' +
                    this.del_mouse_id +
                    ' data from Day ' +
                    this.del_start_day +
                    ' to Day ' +
                    this.del_end_day
        )
      ) {
        try {
          var delData = {
            cohort_id: this.selectedOption,
            del_mouse_id: this.del_mouse_id,
            del_start_day: this.del_start_day,
            del_end_day: this.del_end_day
          }
          // console.log(delData)
          const requestOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(delData)
          }
          const response = await fetch(
            'http://128.173.224.170:3000/api/auto/del_mouse_data/',
            requestOptions
          )
          if (response.status === 201) {
            await this.makeToast('Delete: Successful!')
            await this.refreshMouseList()
          } else {
            await this.makeToast('Delete: Failed!')
          }
        } catch (error) {
          await this.makeToast('Delete: Failed!')
          console.log(error)
        }
      }
    },
    async saveMouseList () {
      try {
        const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.mouse_list)
        }
        const response = await fetch(
          'http://128.173.224.170:3000/api/auto/put_mouse_list/',
          requestOptions
        )
        if (response.status === 201) {
          await this.makeToast('Save: Successful!')
        } else {
          await this.makeToast('Save: Failed!')
        }
      } catch (error) {
        await this.makeToast('Save: Failed!')
        console.log(error)
      }
    },
    async addNewCohort () {
      if (this.new_cohort_name) {
        try {
          const requestOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.new_cohort_name)
          }
          const response = await fetch(
            'http://128.173.224.170:3000/api/auto/put_new_cohort/',
            requestOptions
          )
          if (response.status === 201) {
            await this.makeToast('Add New Cohort: Successful!')
            await this.refreshCohortList()
          } else {
            await this.makeToast('Add New Cohort: Failed!')
          }
        } catch (error) {
          await this.makeToast('Add New Cohort: Failed!')
          console.log(error)
        }
      }
    },
    async RmCohort () {
      if (this.rm_cohort_name) {
        try {
          const requestOptions = {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(this.rm_cohort_name)
          }
          const response = await fetch(
            'http://128.173.224.170:3000/api/auto/del_cohort/',
            requestOptions
          )
          if (response.status === 201) {
            await this.makeToast('Remove Cohort: Successful!')
            await this.refreshCohortList()
          } else {
            await this.makeToast('Remove Cohort: Failed!')
          }
        } catch (error) {
          await this.makeToast('Remove Cohort: Failed!')
          console.log(error)
        }
      }
    },
    async refreshCohortList () {
      fetch('http://128.173.224.170:3000/api/auto/get_cohort_list/')
        .then((response) => {
          if (!response.ok) {
            throw new Error('Network response was not ok')
          }
          return response.json()
        })
        .then((data) => {
          this.options = data
        })
        .catch((error) => {
          console.error('There was a problem fetching the options:', error)
        })
    },
    async handlePrefillFileUpload (e) {
      const file = e.target.files[0]
      const cId = this.selectedOption
      const formData = new FormData()
      formData.append('fileList', file) // Key name should match what your backend expects
      formData.append('cId', cId)

      const response = await fetch(
        'http://128.173.224.170:3000/api/auto/upload_prefill_file/',
        {
          method: 'POST',
          body: formData // No need to set Content-Type; browser will set it as multipart/form-data
        }
      )

      if (response.status === 201) {
        await this.makeToast('Upload: Successful!')
        await this.refreshMouseList()
        // this.upload_error_msgs = 'Upload: Successful!'
      } else {
        const edata = await response.json()
        await this.makeToast('Upload: Failed! Error message: ' + edata.message)
        // this.upload_error_msgs = edata.error + '\n' + edata.message + '\n'
      }
    },
    makeToast (msg, append = true) {
      this.$bvToast.toast(msg, {
        title: 'Notification',
        autoHideDelay: 4000,
        appendToast: append,
        variant: 'primary'
      })
    }
  },
  mounted () {
    // Make the request to fetch the options
    fetch('http://128.173.224.170:3000/api/auto/get_cohort_list/')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        return response.json()
      })
      .then((data) => {
        this.options = data
      })
      .catch((error) => {
        console.error('There was a problem fetching the options:', error)
      })
  }
}
</script>
<style>
.fed_day_sty {
    width: 500px;
    overflow: auto;
    word-break: break-word;
}
</style>
