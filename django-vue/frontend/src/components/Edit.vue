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
    </div>
</template>

<script>
export default {
  data () {
    return {
      selectedOption: null,
      options: [],
      dropdown_cohort_text: 'Select Cohort'
    }
  },
  methods: {
    setCohort (num, name) {
      this.selectedOption = num
      this.dropdown_cohort_text = 'Cohort ' + num + ': ' + name
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
