<template>
    <div class="edit_container">

        <b-container class="bv-example-cohort">
           <b-row align-h="center">
                <b-col sm="2">
                    <b-dropdown variant="outline-primary" class="m-2" :text="dropdown_cohort_text" v-if="options.length > 0">
                         <b-dropdown-item v-for="option in options" :key="option.cohort_id" :value="option.cohort_id" @click="setCohort(option.cohort_id, option.cohort_name)">{{ 'Cohort ' + option.cohort_id + ': ' + option.cohort_name }}</b-dropdown-item>
                    </b-dropdown>
                </b-col>
           </b-row>
        </b-container>

      <b-table v-if="mouse_list.length > 0" :items="mouse_list" :fields="fields">
          <template v-for="field in editableFields" v-slot:[`cell(${field.key})`]="{ item }">
            <b-input v-bind:key="field.key" v-model="item[field.key]" />
          </template>
      </b-table>
      <p v-if="mouse_list.length > 0">Sex: Set 1 (Male) or 2 (Female) to show on the acquisition result. Set 0 if no show.</p>
      <button v-if="mouse_list.length > 0" v-on:click="saveMouseList">Save</button>

    </div>
</template>

<script>
export default {
  computed: {
    editableFields () {
      return this.fields.filter(field => field.editable)
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
        { key: 'mouse_genotype', label: 'Genotype', editable: true }
      ]
    }
  },
  methods: {
    async setCohort (num, name) {
      this.selectedOption = num
      this.dropdown_cohort_text = 'Cohort ' + num + ': ' + name
      await this.updateMouseList(num)
    },
    async updateMouseList (num) {
      try {
        const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cohort_id: num })
        }
        const response = await fetch('http://128.173.224.170:3000/api/auto/get_mouse_list/', requestOptions)
        const data = await response.json()
        this.mouse_list = data
      } catch (error) {
        console.log(error)
      }
    },
    async saveMouseList () {
      try {
        const requestOptions = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.mouse_list)
        }
        const response = await fetch('http://128.173.224.170:3000/api/auto/put_mouse_list/', requestOptions)
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
