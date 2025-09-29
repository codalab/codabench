<dataset-create>
  <div class="ui container dataset-container">
    <h2 class="ui header">Create Dataset</h2>

    <form class="ui form {error: errors}" ref="form"  enctype="multipart/form-data">

      <!--  Errors  -->
      <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
          <div class="header">
              Errorn (s) creating dataset
          </div>
          <ul class="list">
              <li each="{ error, field in errors }">
                  <strong>{field}:</strong> {error}
              </li>
          </ul>
      </div>
      
      <!-- Name -->
      <div class="field required">
        <label>Name</label>
        <input id="dataset-name" type="text" name="name" ref="name" required placeholder="Enter dataset name" error="{errors.name}">
      </div>

      <!-- Description -->
      <div class="field required">
        <label>Description</label>
        <textarea id="dataset-description" name="description" ref="description" rows="4" required placeholder="Enter a description..." error="{errors.description}"></textarea>
      </div>

      <!-- Dataset Type -->
      <div class="field required">
        <label>Type</label>
        <select id="dataset-type" class="ui dropdown" name="type" ref="type" required error="{errors.type}"> 
          <option value="public_data" selected>Public Data</option>
          <option value="input_data">Input Data</option>
          <option value="reference_data">Reference Data</option>
        </select>
        <p class="form-note">
          NOTE: Only datasets with type: public data are listed on the Public Datasets page; input and reference data appear only in your Resources page.
        </p>
      </div>

      <!-- Dataset Public -->
      <div class="field">
        <label>Make Public</label>
        <div class="ui checkbox">
          <input type="checkbox" id="dataset-public" name="is_public" ref="is_public">
          <label for="dataset-public">List on Public Datasets page</label>
        </div>
        <p class="form-note">
          NOTE: Only datasets that are marked `public` are listed on the Public Datasets.
        </p>
      </div>


      <!-- Dataset License -->
      <div class="field required">
        <label>License</label>
        <select id="dataset-license" class="ui dropdown" name="license" ref="license" onchange="{on_license_change}" error="{errors.license}">
          <option value="">Select a License</option>
          <option value="CC0-1.0">Creative Commons Zero (CC0) 1.0</option>
          <option value="CC-BY-4.0">Creative Commons Attribution (CC BY) 4.0</option>
          <option value="CC-BY-SA-4.0">Creative Commons Attribution-ShareAlike (CC BY-SA) 4.0</option>
          <option value="CC-BY-NC-4.0">Creative Commons Attribution-NonCommercial (CC BY-NC) 4.0
          <option value="ODC-By">Open Data Commons Attribution License (ODC-By)</option>
          <option value="ODbL-1.0">Open Database License (ODbL) 1.0</option>
          <option value="MIT">MIT License</option>
          <option value="Apache-2.0">Apache License 2.0</option>
          <option value="GPL-3.0">GNU General Public License v3.0</option>
          <option value="BSD-3-Clause">BSD 3-Clause License</option>
          <option value="Research-Only">Research Use Only</option>
          <option value="N/A">N/A</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <!-- Custom License -->
      <div class="field" if="{show_custom_license}">
        <label>Custom License Name</label>
        <input id="custom-license" type="text" name="custom_license" ref="custom_license" placeholder="Enter license name" error="{errors.custom_license}">
      </div>

      <!-- File Upload -->
      <div class="field required">
        <label>Attach Dataset File (.zip only)</label>
        <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip" required></input-file>
      </div>

      <!-- Submit Button -->
      <button type="submit" class="ui button bg-codabench" onclick="{check_form}">
        <i class="bi bi-cloud-arrow-up-fill"></i> Submit Dataset
      </button>
    </form>
  </div>


  <script>
    var self = this
    self.mixin(ProgressBarMixin)

    self.errors = {}
    self.show_custom_license = false

    self.on_license_change = function (e) {
      self.show_custom_license = e.target.value === 'Other'
      self.update()
    }

    self.check_form = function (e) {
      e.preventDefault()

      // Reset upload progress, in case we're trying to re-upload or had errors      
      self.file_upload_progress_handler(undefined)

      // Form validation
      self.errors = {}
      var validate_data = get_form_data(self.refs.form)

      var required_fields = ['name', 'description','type', 'license', 'data_file']
      required_fields.forEach(field => {
        if (validate_data[field].trim() === '') {
            self.errors[field] = "This field is required"
        }
      })

      // Additional check for custom license if "Other" is selected
      if (validate_data['license'] === 'Other') {
        if (!validate_data['custom_license'] || validate_data['custom_license'].trim() === '') {
          self.errors['custom_license'] = "Please specify a custom license name"
        }
      }

      if (Object.keys(self.errors).length > 0) {
        // display errors and drop out
        self.update()
        return
      }

      // Call the progress bar wrapper and do the upload
      self.prepare_upload(self.upload)()
    }

    self.upload = function () {
      
      // Get form data
      var metadata = get_form_data(self.refs.form)

      // Remove data_file from form data (we don't want to send the file in the meta-data)
      delete metadata.data_file

      // Set is_public filed from the checkbox value
      metadata.is_public = self.refs.is_public.checked

      // Get data_file
      var data_file = self.refs.data_file.refs.file_input.files[0]

      // Upload using create_dataset API
      CODALAB.api.create_dataset(metadata, data_file, self.file_upload_progress_handler)
        .done(function (data) {
            toastr.success("Dataset successfully uploaded!")
            self.clear_form()
            setTimeout(function () {
              self.redirect_to_public_or_resources()
            }, 2000)
        })
        .fail(function (response) {
            if (response) {
                try {
                    var errors = JSON.parse(response.responseText)

                    // Clean up errors to not be arrays but plain text
                    Object.keys(errors).map(function (key, index) {
                        errors[key] = errors[key].join('; ')
                    })

                    self.update({errors: errors})
                } catch (e) {

                }
            }
            toastr.error("Creation failed, error occurred")
        })
        .always(function () {
            self.hide_progress_bar()
        })
    }

    self.clear_form = function () {

      self.refs.form.reset()

      // Reset errors and custom license visibility
      self.errors = {}
      self.show_custom_license = false

      self.update()
    }

    self.redirect_to_public_or_resources = function () {
      const urlParams = new URLSearchParams(window.location.search)
      const from = urlParams.get('from')

      if (from === 'public') {
          window.location.href = '/datasets/public/'
      } else {
          window.location.href = '/datasets/'
      }
    }
  </script>

  <style>
    .dataset-container {
      max-width: 700px;
      margin: 2rem auto;
      padding: 2rem;
      background: #fff;
      border: 1px solid #ddd;
      border-radius: 8px;
    }
    .form-note {
      font-style: italic;
      color: #888;
      font-size: 0.9rem;
      margin-top: 0.5rem;
    }
    input[type="file"] {
      border: 1px solid #ccc;
      padding: 0.75rem;
      border-radius: 4px;
    }
    .bg-codabench{
        background-color: #43637a !important;
        color: #fff !important;
    }
    .bg-codabench:hover {
      background-color: #2d3f4d !important;
    }
  </style>
</dataset-create>
