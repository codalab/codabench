<consulting-my-listing>
  <div class="page-header">
    <h1 class="page-title">My Consulting Listing</h1>
    <a class="consulting-btn" href="{URLS.CONSULTING_PUBLIC}">Back to Consulting</a>
  </div>

  <!-- Explains the page to a user without a listing, e.g. one coming straight from the user menu -->
  <p class="consulting-blurb" if="{!loading && !listing}">
    Codabench provides a <a href="{URLS.CONSULTING_PUBLIC}">consulting page</a> where independent consultants can list
    the help they offer to benchmark and competition organizers. If you offer such services, you are welcome to add
    your own listing here. Please note that Codabench only lists these services: it is not involved in, and takes no
    responsibility for, any arrangement between consultants and their clients.
  </p>

  <div class="loading-indicator" show="{loading}">
    <div class="spinner"></div>
  </div>

  <div class="listing-panel" show="{!loading}">

    <!-- Status messages -->
    <div class="ui icon info message" if="{!listing}">
      <i class="info circle icon"></i>
      <div class="content">
        Fill in the form below to add your listing. It will be shown on the consulting page once an admin has approved it.
      </div>
    </div>
    <div class="ui icon warning message" if="{is_pending()}">
      <i class="exclamation triangle icon"></i>
      <div class="content">
        Your listing is pending review. You cannot edit it until an admin has reviewed it.
      </div>
    </div>
    <!-- Deactivating only hides the listing from the public page; it can still be edited and removed -->
    <div class="ui icon warning message" if="{listing && !listing.is_active}">
      <i class="exclamation triangle icon"></i>
      <div class="content">
        Your listing has been deactivated by an administrator and is not shown publicly.
      </div>
    </div>
    <div class="ui icon warning message" if="{listing && listing.status === 'approved'}">
      <i class="exclamation triangle icon"></i>
      <div class="content">
        <span if="{listing.is_active}">Your listing is live.</span>
        Saving changes sends it back for review<span if="{listing.is_active}">, and it will be hidden from the consulting page until an admin approves it again</span>.
      </div>
    </div>
    <div class="ui icon negative message" if="{listing && listing.status === 'rejected'}">
      <i class="times circle icon"></i>
      <div class="content">
        <div class="header">Your listing was rejected</div>
        <p>Reason: <em>{listing.rejection_reason}</em> (You can edit it and submit it for review again.)</p>
      </div>
    </div>

    <!-- Read-only view, while pending: the same card as on the consulting page, -->
    <!-- but with the description always open (no arrow) -->
    <div class="listing-card" show="{is_pending()}">
      <div class="card-info">
        <div class="card-picture">
          <img src="{listing && listing.picture}">
        </div>
        <h4 class="heading">{listing && listing.title}</h4>
        <div class="card-links" if="{listing}">
          <a if="{listing.website_url}" href="{listing.website_url}" target="_blank" rel="noopener" title="Website"><i class="bi bi-globe"></i></a>
          <a if="{listing.linkedin_url}" href="{listing.linkedin_url}" target="_blank" rel="noopener" title="LinkedIn"><i class="bi bi-linkedin"></i></a>
          <a if="{listing.github_url}" href="{listing.github_url}" target="_blank" rel="noopener" title="GitHub"><i class="bi bi-github"></i></a>
        </div>
      </div>
      <div class="card-description" ref="readonly_description"></div>
    </div>

    <!-- Add / edit form -->
    <form class="ui form" show="{!is_pending()}" onsubmit="{save}">
      <div class="required field">
        <label>Title</label>
        <input type="text" ref="title" maxlength="150" placeholder="Title" oninput="{on_form_change}">
      </div>
      <div class="required field">
        <label>Picture (max 5 MB)</label>
        <label show="{listing && listing.picture}">
          Uploaded Picture: <a href="{listing && listing.picture}" target="_blank">{picture_name(listing && listing.picture)}</a>
        </label>
        <div class="ui left action file input">
          <button class="ui icon button" type="button" onclick="{open_picture_dialog}">
            <i class="attach icon"></i>
          </button>
          <input type="file" ref="picture" accept="image/*" onchange="{on_picture_change}">

          <!-- Just showing the file after it is selected -->
          <input value="{picture_file_name}" readonly onclick="{open_picture_dialog}">
        </div>
      </div>
      <div class="three fields">
        <div class="field">
          <label>Website URL</label>
          <input type="text" ref="website_url" placeholder="https://www.xyz.com" oninput="{on_form_change}">
        </div>
        <div class="field">
          <label>LinkedIn URL</label>
          <input type="text" ref="linkedin_url" placeholder="https://www.linkedin.com/in/john-doe" oninput="{on_form_change}">
        </div>
        <div class="field">
          <label>GitHub URL</label>
          <input type="text" ref="github_url" placeholder="https://github.com/john-doe" oninput="{on_form_change}">
        </div>
      </div>
      <div class="required field">
        <label>Description</label>
        <textarea ref="description"></textarea>
      </div>

      <div class="ui negative message" if="{errors.length > 0}">
        <ul class="list">
          <li each="{error in errors}">{error}</li>
        </ul>
      </div>

      <button type="submit" class="ui primary button" disabled="{!can_save()}">{listing ? 'Save and resubmit for review' : 'Submit for review'}</button>
    </form>

    <!-- Removing is in its own red banner, so it is clear that it is a dangerous action -->
    <div class="ui negative message remove-banner" if="{listing}">
      <div>
        <div class="header">Remove listing</div>
        <p>This permanently deletes your listing and this action cannot be undone.</p>
      </div>
      <button class="ui red button" onclick="{remove}">Remove listing</button>
    </div>
  </div>

  <script>
    var self = this
    self.loading = true
    self.saving = false
    self.listing = null
    self.errors = []
    self.picture_file_name = ''
    // Newly selected picture file
    self.picture_file = null
    self.MAX_PICTURE_SIZE = 5 * 1024 * 1024  // 5 MB, same limit as the API

    self.FIELD_LABELS = {
        title: 'Title',
        picture: 'Picture',
        website_url: 'Website URL',
        linkedin_url: 'LinkedIn URL',
        github_url: 'GitHub URL',
        description: 'Description'
    }

    self.one("mount", function () {
        self.markdown_editor = create_easyMDE(self.refs.description)
        // Re-render so the save button follows changes to the description
        self.markdown_editor.codemirror.on('change', function () {
            self.update()
        })

        CODALAB.api.get_my_consulting_listing()
            .done(function (response) {
                // Empty response (204) when the user has no listing
                self.set_listing(response || null)
            })
            .fail(function (response) {
                toastr.error(`Could not load your consulting listing (status ${response.status})`)
            })
            .always(function () {
                self.loading = false
                self.update()
            })
    })

    self.is_pending = function () {
        return !!self.listing && self.listing.status === 'pending'
    }

    // Nothing to do here: riot re-renders after every event handler, which updates the save button
    self.on_form_change = function () {
    }

    // True when the form differs from the saved listing
    self.has_changes = function () {
        // Newlines are saved as \r\n (multipart form data) but the editor returns \n
        const saved_description = self.listing.description.replace(/\r\n/g, '\n')
        return !!self.picture_file
            || self.refs.title.value !== self.listing.title
            || self.refs.website_url.value !== self.listing.website_url
            || self.refs.linkedin_url.value !== self.listing.linkedin_url
            || self.refs.github_url.value !== self.listing.github_url
            || self.markdown_editor.value() !== saved_description
    }

    self.can_save = function () {
        if (self.saving) {
            return false
        }
        // A new listing can always be submitted
        if (!self.listing) {
            return true
        }
        // An existing one only when something was changed
        return self.has_changes()
    }

    self.set_listing = function (listing) {
        self.listing = listing
        self.errors = []
        self.picture_file = null
        self.picture_file_name = ''
        self.refs.picture.value = ''

        self.refs.title.value = listing ? listing.title : ''
        self.refs.website_url.value = listing ? listing.website_url : ''
        self.refs.linkedin_url.value = listing ? listing.linkedin_url : ''
        self.refs.github_url.value = listing ? listing.github_url : ''
        self.markdown_editor.value(listing ? listing.description : '')
        $(self.refs.readonly_description).html(listing ? render_markdown(listing.description) : '')
        self.update()
    }

    self.picture_name = function (url) {
        return url ? url.split('?')[0].replace(/\\/g, '/').replace(/.*\//, '') : ''
    }

    self.open_picture_dialog = function () {
        self.refs.picture.click()
    }

    self.on_picture_change = function (e) {
        const file = e.target.files[0]
        if (!file) {
            self.picture_file_name = ''
            self.picture_file = null
            return
        }
        if (file.size > self.MAX_PICTURE_SIZE) {
            toastr.error("The picture must be 5 MB or smaller")
            e.target.value = ''
            self.picture_file_name = ''
            self.picture_file = null
            return
        }
        self.picture_file_name = file.name
        self.picture_file = file
    }

    self.save = function (e) {
        e.preventDefault()
        if (!self.can_save()) {
            return
        }

        // Sent as multipart form data, so the picture is uploaded as a file
        const data = new FormData()
        data.append('title', self.refs.title.value)
        data.append('website_url', self.refs.website_url.value)
        data.append('linkedin_url', self.refs.linkedin_url.value)
        data.append('github_url', self.refs.github_url.value)
        data.append('description', self.markdown_editor.value())
        // On edit the picture is only sent when a new one was selected
        if (self.picture_file) {
            data.append('picture', self.picture_file)
        }

        self.errors = []
        self.saving = true

        const request = self.listing
            ? CODALAB.api.update_my_consulting_listing(data)
            : CODALAB.api.create_my_consulting_listing(data)

        request
            .done(function (response) {
                toastr.success("Listing submitted for review")
                self.set_listing(response)
                window.scrollTo({top: 0, behavior: 'smooth'})
            })
            .fail(function (response) {
                self.errors = self.parse_errors(response)
            })
            .always(function () {
                self.saving = false
                self.update()
            })
    }

    self.parse_errors = function (response) {
        const errors = []
        _.forEach(response.responseJSON, function (messages, field) {
            const message = _.isArray(messages) ? messages.join(' ') : messages
            errors.push(field === 'detail' ? message : `${self.FIELD_LABELS[field] || field} - ${message}`)
        })
        return errors.length > 0 ? errors : [`Could not save listing (status ${response.status})`]
    }

    self.remove = function () {
        if (!confirm("Are you sure you want to remove your consulting listing?")) {
            return
        }
        CODALAB.api.delete_my_consulting_listing()
            .done(function () {
                toastr.success("Listing removed")
                window.location.href = URLS.CONSULTING_PUBLIC
            })
            .fail(function (response) {
                toastr.error(`Could not remove listing (status ${response.status})`)
            })
    }
  </script>
</consulting-my-listing>
