<dataset-detail>
  <div class="ui container dataset-container">
    <h2 class="ui header">Dataset Details</h2>

    <table class="ui celled table">
      <tbody if="{dataset}">
        <tr>
          <td><strong>Name</strong></td>
          <td>{dataset.name}</td>
        </tr>
        <tr>
          <td><strong>Description</strong></td>
          <td>{dataset.description}</td>
        </tr>
        <tr>
          <td><strong>Owner</strong></td>
          <td>{dataset.created_by}</td>
        </tr>
        <tr>
          <td><strong>Uploaded Date</strong></td>
          <td>{pretty_date(dataset.created_when)}</td>
        </tr>
        <tr>
          <td><strong>License</strong></td>
          <td>{dataset.license}</td>
        </tr>
        <tr>
          <td><strong>Downloads</strong></td>
          <td>{dataset.downloads}</td>
        </tr>
        <tr>
          <td><strong>Verified</strong></td>
          <td if="{dataset.is_verified}"><i class="bi bi-check-circle-fill green"></td>
          <td if="{!dataset.is_verified}">No</td>
        </tr>
        <tr>
          <td><strong>File Size</strong></td>
          <td>{pretty_bytes(dataset.file_size)}</td>
        </tr>
        <tr>
          <td colspan=2>
            <a class="ui button small primary" target="_blank" href="{URLS.DATASET_DOWNLOAD_BY_PK(dataset.id)}">
              <i class="bi bi-file-earmark-arrow-down-fill"></i> Download
            </a>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <script>
    var self = this
    self.dataset = {
        id: opts.id,
        name: opts.name,
        description: opts.description,
        license: opts.license,
        is_verified: opts.is_verified === 'True',
        created_when: opts.created_when,
        created_by: opts.created_by,
        file_size: opts.file_size,
        downloads: opts.downloads,
    }

    self.on('mount', () => {
        self.update()
    })

    self.pretty_date = date => luxon.DateTime.fromISO(date).toLocaleString(luxon.DateTime.DATE_FULL)

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
    .bg-codabench {
      background-color: #43637a !important;
      color: #fff !important;
    }
    .bg-codabench:hover {
      background-color: #2d3f4d !important;
    }
    table.ui.celled.table td {
      vertical-align: top;
    }
    .green{
      color: #009022ff;
    }
  </style>
</dataset-detail>
