<dataset-create>
  <div class="ui container dataset-container">
    <h2 class="ui header">Create Dataset</h2>

    <form class="ui form" onsubmit="{submit_form}" enctype="multipart/form-data">
      
      <!-- Dataset Name -->
      <div class="field">
        <label>Dataset Name</label>
        <input id="dataset-name" type="text" name="name" required placeholder="Enter dataset name">
      </div>

      <!-- Description -->
      <div class="field">
        <label>Description</label>
        <textarea id="dataset-description" name="description" rows="4" required placeholder="Enter a description..."></textarea>
      </div>

      <!-- Dataset Type -->
      <div class="field">
        <label>Dataset Type</label>
        <select id="dataset-type" class="ui dropdown" name="type" required>
          <option value="public_data" selected>Public Data</option>
          <option value="input_data">Input Data</option>
          <option value="reference_data">Reference Data</option>
        </select>
        <p class="form-note">
          NOTE: Public data is shown on the public datasets page. Input and reference data can only be viewed in your Resources page.
        </p>
      </div>

      <!-- Dataset License -->
      <div class="field">
        <label>License</label>
        <select id="dataset-license" class="ui dropdown" name="license" onchange="{on_license_change}">
          <option value="MIT">MIT License</option>
          <option value="Apache-2.0">Apache License 2.0</option>
          <option value="GPL-3.0">GNU GPLv3</option>
          <option value="BSD-3-Clause">BSD 3-Clause</option>
          <option value="CC-BY-4.0">Creative Commons BY 4.0</option>
          <option value="N/A">N/A</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <!-- Custom License -->
      <div class="field" if="{show_custom_license}">
        <label>Custom License Name</label>
        <input id="custom-license" type="text" name="custom_license" placeholder="Enter license name">
      </div>

      <!-- File Upload -->
      <div class="field">
        <label>Upload Dataset (.zip only)</label>
        <input-file name="data_file" ref="data_file" error="{errors.data_file}" accept=".zip" required></input-file>
      </div>

      <!-- Submit Button -->
      <button type="submit" class="ui button bg-codabench">
        <i class="upload icon"></i> Submit Dataset
      </button>
    </form>
  </div>

  <script>
    var self = this
    self.show_custom_license = false

    self.on_license_change = function (e) {
      self.show_custom_license = e.target.value === 'Other'
      self.update()
    }

    self.submit_form = function (e) {
      e.preventDefault()
      const formData = new FormData(e.target)

      const payload = {
        name: formData.get('name'),
        description: formData.get('description'),
        type: formData.get('type'),
        license: formData.get('license') === 'Other'
          ? formData.get('custom_license')
          : formData.get('license'),
        file: formData.get('file')
      }

      console.log('Submitting dataset:', payload)
      alert('Dataset submitted (mock)!')
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
        background-color: #2d3f4d !important;
        color: #fff !important;
    }
    .bg-codabench:hover {
      background-color: rgba(67, 99, 122, 1) !important;
    }
  </style>
</dataset-create>
