<competition-participation>
  <form class="ui form">
    <div class="field required">
      <label>Terms</label>
      <textarea class="markdown-editor" ref="terms" name="terms"></textarea>
    </div>
    <div class="field">
      <div class="ui checkbox">
        <input selenium="auto-approve" type="checkbox" name="registration_auto_approve" ref="registration_auto_approve" onchange="{form_updated}">
        <label>Auto approve registration requests
          <span data-tooltip="If left unchecked, registration requests must be manually approved by the benchmark creator or collaborators"
                data-inverted=""
                data-position="bottom center">
          <i class="help icon circle"></i></span>
        </label>
      </div>
    </div>
    <div class="field">
      <div class="ui checkbox">
          <input type="checkbox" name="allow_robot_submissions" ref="allow_robot_submissions" onchange="{form_updated}">
          <label>Allow robot submissions
              <span data-tooltip="If left unchecked, robot users will have to be manually approved by the benchmark creator or collaborators. This can be changed later."
                    data-inverted=""
                    data-position="bottom center">
              <i class="help icon circle"></i></span>
          </label>
      </div>
    </div>

    <!--  Whitelist emails list  -->
    <!--  Emails of users who do not require admin approval to enter the competition  -->
    <div class="field">
      <label>Whitelist Emails</label>
      <p>A list of emails (one per line) of users who do not require competition organizer's approval to enter this competition.</p>
      <div class="ui yellow message">
          <span><b>Note:</b></span><br>
          Only valid emails are allowed<br>
          Empty lines are not allowed
      </div>
      <textarea class="markdown-editor" ref="whitelist_emails" name="whitelist_emails"></textarea>
      <div class="error-message" style="color: red;"></div>
    </div>


    <!-- Participant Groups -->
    <div class="field">
      <label>Groupes</label>
      <div style="margin-bottom:8px;">
        <button type="button" class="ui tiny primary button" onclick="{ open_create_group }">
          <i class="plus icon"></i> Créer un groupe
        </button>
      </div>

      <div class="ui cards">
        <div class="card" each="{ group in available_groups }">
          <div class="content">
            <div class="header">
              <div class="ui checkbox">
                <input type="checkbox"
                      value="{ group.id }"
                      checked="{ selected_group_ids.indexOf(group.id) !== -1 }"
                      onchange="{ toggle_group.bind(this, group.id) }">
                <label>{ group.name }</label>
              </div>
            </div>

            <div class="meta group-meta" style="margin-top:0.4em;">
              <div class="group-labels">
                <span class="ui grey label">Queue: { group.queue || "Aucune" }</span>
                <span class="ui grey label">Membres: { group.members && group.members.length > 0 ? group.members.length : 0 }</span>
              </div>

              <div class="members-chips" if="{ group.members && group.members.length }">
                <span class="ui tiny label" each="{m in group.members}">
                  { m }
                </span>
              </div>

              <div class="group-actions">
                <button class="ui mini icon basic button edit-btn" title="Modifier" onclick="{ open_edit_group.bind(this, group) }">
                  <i class="edit icon"></i>
                </button>
                <button class="ui mini icon basic red button delete-btn" title="Supprimer" onclick="{ delete_group.bind(this, group) }">
                  <i class="trash icon"></i>
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

  </form>

    <!-- CREATE / EDIT GROUP MODAL -->
  <div ref="group_modal" class="ui small modal" style="display:none;">
    <i class="close icon" onclick="{ close_group_modal }"></i>
    <div class="header">{ editing_group ? 'Modifier le groupe' : 'Créer un groupe' }</div>
    <div class="content">
      <div class="ui form">
        <div class="field">
          <label>Nom</label>
          <input type="text" ref="group_name">
        </div>

        <div class="field">
          <label>Queue (optionnelle)</label>
          <select ref="group_queue" class="ui dropdown">
            <option value="">Aucune</option>
            <option each="{ q in available_queues }" value="{ q.id }">{ q.name }</option>
          </select>
        </div>

        <div class="field">
          <label>Membres (sélectionner)</label>

          <div style="display:flex; gap:.5rem; margin-bottom:.5rem; align-items:center;">
            <button type="button" class="ui mini button" onclick="{ select_all_users }">Select all</button>
            <button type="button" class="ui mini basic button" onclick="{ clear_user_selection }">Clear</button>
            <div class="ui right floated meta" style="margin-left:auto;">
              <span class="ui tiny basic label">Sélectionnées: <span ref="selected_count">0</span></span>
            </div>
          </div>

          <select ref="group_user_select" multiple class="ui fluid multiple search selection dropdown" style="width:100%;">
            <option each="{ u in available_users }" value="{ u.id }">{ u.username } &lt;{ u.email }&gt;</option>
          </select>

          <div class="ui segment" style="margin-top:.5rem;">
            <small class="muted">Tapez pour chercher des utilisateurs, sélectionnez plusieurs éléments.</small>
          </div>
        </div>

        <div class="ui error message" ref="group_modal_error" style="display:none;"></div>
      </div>
    </div>

    <div class="actions">
      <div class="ui cancel button" onclick="{ close_group_modal }">Annuler</div>
      <div class="ui primary button" onclick="{ submit_group }">{ editing_group ? 'Modifier' : 'Créer' }</div>
    </div>
  </div>

  <script>
    let self = this

    self.data = {}
    self.available_groups = []
    self.selected_group_ids = []
    self.available_queues = []
    self.available_users = []
    self.editing_group = null
    self._scheduledUpdate = false

    // init semantic UI elements + setup multi-select behaviour
    const initUI = () => {
      try { $('.ui.checkbox', self.root).checkbox() } catch(e) {}
      try { $('.ui.dropdown', self.root).dropdown() } catch(e) {}

      try {
        if (self.refs && self.refs.group_user_select) {
          $(self.refs.group_user_select).dropdown({
            allowAdditions: false,
            forceSelection: true,
            fullTextSearch: true,
            onChange: (value) => {
              const arr = (value || '').toString().trim()
              let count = 0
              if (arr.length) count = (arr + '').split(',').filter(Boolean).length
              try { self.refs.selected_count.textContent = count } catch(e){}
            }
          })
        }
      } catch(e) {}
    }

    const compPk = () => {
      try {
        if (self && self.opts) {
          if (self.opts.competition_id) return String(self.opts.competition_id)
          if (self.opts.competition_pk) return String(self.opts.competition_pk)
        }
      } catch(e){}
      try {
        const a = self.root && (self.root.getAttribute('competition_id') || self.root.getAttribute('competition-pk') || self.root.getAttribute('competition_pk'))
        if (a) return String(a)
      } catch(e){}
      const dom = document.getElementById('competition-id')
      if (dom && dom.dataset && dom.dataset.id) return String(dom.dataset.id)
      try {
        const cf = document.querySelector('competition-form[competition_id], competition-form[competition-pk], competition-form[competition_pk]')
        if (cf) {
          const v = cf.getAttribute('competition_id') || cf.getAttribute('competition-pk') || cf.getAttribute('competition_pk')
          if (v) return String(v)
        }
      } catch(e){}
      try {
        const parts = window.location.pathname.split('/').filter(Boolean)
        for (let i = 0; i < parts.length; i++) {
          if (/^\d+$/.test(parts[i])) return parts[i]
        }
      } catch(e){}
      return null
    }


    const parseJsonScriptElement = id => {
      const el = document.getElementById(id)
      if (!el || !el.textContent) return []
      try { return JSON.parse(el.textContent) } catch (err) { console.warn('Invalid JSON in #' + id, err); return [] }
    }

    self.on('mount', () => {
      self.available_groups = parseJsonScriptElement('available-groups') || []
      self.selected_group_ids = parseJsonScriptElement('selected-group-ids') || []
      self.available_queues = parseJsonScriptElement('available-queues') || []
      self.available_users = parseJsonScriptElement('available-users') || []

      self.markdown_editor = create_easyMDE(self.refs.terms)
      self.markdown_editor_whitelist = create_easyMDE(self.refs.whitelist_emails, false, false, '200px')

      // Si un event competition_loaded est arrivé avant le mount, l'appliquer maintenant
      try {
        if (self._pending_competition && self._pending_competition.terms) {
          try {
            if (self.markdown_editor && typeof self.markdown_editor.value === 'function') {
              self.markdown_editor.value(self._pending_competition.terms || '')
            }
            if (self.markdown_editor_whitelist && typeof self.markdown_editor_whitelist.value === 'function') {
              self.markdown_editor_whitelist.value(Array.isArray(self._pending_competition.whitelist_emails) && self._pending_competition.whitelist_emails.length > 0 ? self._pending_competition.whitelist_emails.join('\n') : '')
            }
            if (self.markdown_editor && self.markdown_editor.codemirror && typeof self.markdown_editor.codemirror.refresh === 'function') {
              self.markdown_editor.codemirror.refresh()
            }
          } catch(e) { console.warn('apply pending competition to editors failed', e) }
          delete self._pending_competition
          try { self.update(); self.form_updated() } catch(e){}
        }
      } catch(e) { console.warn('checking _pending_competition failed', e) }

      $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
          this.addEventListener('keyup', self.form_updated)
      })
      self.scheduleUpdate && self.scheduleUpdate()
      setTimeout(initUI, 0)
    })

    self.toggle_group = (group_id) => {
      const idx = self.selected_group_ids.indexOf(group_id)
      if (idx === -1) self.selected_group_ids.push(group_id)
      else self.selected_group_ids.splice(idx, 1)

      self.data = self.data || {}
      self.data.participant_groups = self.selected_group_ids.slice()

      CODALAB.events.trigger('competition_data_update', self.data)
      self.scheduleUpdate && self.scheduleUpdate()
    }

    self.form_updated = () => {
      self.data.registration_auto_approve = $(self.refs.registration_auto_approve).prop('checked')
      self.data.allow_robot_submissions = $(self.refs.allow_robot_submissions).prop('checked')
      self.data.terms = (self.markdown_editor && self.markdown_editor.value()) || (self.refs.terms && self.refs.terms.value) || ''


      // Get the content of the whitelist-emails textarea and split it into an array of email addresses
      let whitelist_emails_content = self.markdown_editor_whitelist && typeof self.markdown_editor_whitelist.value === 'function' ? self.markdown_editor_whitelist.value() : (self.refs.whitelist_emails && self.refs.whitelist_emails.value) || ''
      let email_addresses = whitelist_emails_content.trim() === '' ? [] : whitelist_emails_content.split('\n').map(email => email.trim())

      // Check for problematic emails
      let problematicEmailIndexes = []
      email_addresses.forEach((email, index) => {
        if (!self.isValidEmail(email)) {
            // If an email is invalid, store its index
            problematicEmailIndexes.push(index);
        }
      })

      // Email errors
      const errorDiv = self.root.querySelector('.error-message')
      if (problematicEmailIndexes.length > 0) {
        // Show an error message if there are invalid emails
        errorDiv.classList.add('ui', 'red', 'message')

        const errorMessage = document.createElement('strong')
        errorMessage.textContent = 'One or more email addresses are invalid'
        errorDiv.innerHTML = '' // Clear existing content
        errorDiv.appendChild(errorMessage)

        // Create an unordered list for error details
        const errorList = document.createElement('ul')

        problematicEmailIndexes.forEach((index) => {
            const problematicEmail = email_addresses[index]
            // Create a list item for each problematic email
            const listItem = document.createElement('li')
            listItem.textContent = `${problematicEmail}`
            errorList.appendChild(listItem)
        })

        // Append the error details (unordered list) to the 'error-message' div
        errorDiv.appendChild(errorList)
      } else {
          // Clear the error message and remove the classes if all emails are valid
          errorDiv.classList.remove('ui', 'red', 'message')
          errorDiv.textContent = ''
      }
      
      // Add to whitelist_emails when there is not problematic email address
      if(problematicEmailIndexes.length == 0){
          self.data.whitelist_emails = email_addresses
      }
      
      // set a boolean to true if all emails are valid
      let is_valid_emails = problematicEmailIndexes.length == 0
      let is_valid_terms = !!self.data.terms
      
      // set a valid boolean to true when all email are valid and terms are valid
      is_valid = is_valid_terms && is_valid_emails

      CODALAB.events.trigger('competition_is_valid_update', 'participation', is_valid)

      if (is_valid) {
          CODALAB.events.trigger('competition_data_update', self.data)
      }
    }

    // Function to validate an email address
    self.isValidEmail = function (email) {
      // Regular expression pattern to match a valid email address
      const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/

      // Test the email against the pattern and return the result (boolean)
      return emailPattern.test(email)
    }

    self.open_create_group = () => {
      self.editing_group = null
      try { self.refs.group_name.value = '' } catch(e){}
      try { $(self.refs.group_queue).dropdown('clear') } catch(e){}
      try { $(self.refs.group_user_select).dropdown('clear') } catch(e){}
      try { self.refs.selected_count.textContent = '0' } catch(e){}
      try { $(self.refs.group_modal).modal({closable:true}).modal('show') } catch(e) { self.refs.group_modal.style.display = 'block' }
      setTimeout(initUI, 0)
    }

    const membersToIds = (membersArr) => {
      if (!membersArr || !membersArr.length) return []
      const idsids = []
      const users = self.available_users || []
      membersArr.forEach(m => {
        const byId = users.find(u => String(u.id) === String(m))
        if (byId) { ids.push(String(byId.id)); return }
        const byUsername = users.find(u => u.username === m)
        if (byUsername) { ids.push(String(byUsername.id)); return }
        const byEmail = users.find(u => u.email === m)
        if (byEmail) { ids.push(String(byEmail.id)); return }
      })
      return ids
    }

    self.open_edit_group = (group) => {
      self.editing_group = group
      try { self.refs.group_name.value = group.name || '' } catch(e){}
      try {
        let queueId = null
        if (group.queue_id) queueId = group.queue_id
        else if (group.queue) {
          const qFound = (self.available_queues || []).find(x => x.name === group.queue)
          if (qFound) queueId = qFound.id
        }
        if (queueId) $(self.refs.group_queue).dropdown('set selected', queueId)
        else $(self.refs.group_queue).dropdown('clear')
      } catch(e){}

      try {
        const memberIds = membersToIds(group.members || [])
        if (memberIds.length) {
          $(self.refs.group_user_select).dropdown('set selected', memberIds)
          try { self.refs.selected_count.textContent = memberIds.length } catch(e){}
        } else {
          $(self.refs.group_user_select).dropdown('clear')
          try { self.refs.selected_count.textContent = '0' } catch(e){}
        }
      } catch(e){ console.warn('prefill members failed', e) }

      try { $(self.refs.group_modal).modal({closable:true}).modal('show') } catch(e) { self.refs.group_modal.style.display = 'block' }
      setTimeout(initUI, 0)
    }

    self.select_all_users = () => {
      try {
        const ids = (self.available_users || []).map(u => String(u.id))
        $(self.refs.group_user_select).dropdown('set selected', ids)
        try { self.refs.selected_count.textContent = ids.length } catch(e){}
      } catch(e){ console.warn('select all failed', e) }
    }

    self.clear_user_selection = () => {
      try {
        $(self.refs.group_user_select).dropdown('clear')
        try { self.refs.selected_count.textContent = '0' } catch(e){}
      } catch(e){ console.warn('clear selection failed', e) }
    }

    self.close_group_modal = () => {
      try { $(self.refs.group_modal).modal('hide') } catch(e) { self.refs.group_modal.style.display = 'none' }
    }

    // submit create / update group (Form POST instead of JSON)
    self.submit_group = () => {
      const name = (self.refs.group_name && self.refs.group_name.value || '').trim()
      if (!name) {
        if (self.refs.group_modal_error) {
          self.refs.group_modal_error.style.display = 'block'
          self.refs.group_modal_error.textContent = 'Le nom du groupe est requis.'
        }
        return
      }

      let queue_id = null
      try { queue_id = $(self.refs.group_queue).dropdown('get value') || null } catch(e) { queue_id = (self.refs.group_queue && self.refs.group_queue.value) || null }

      let user_ids = []
      try {
        const val = $(self.refs.group_user_select).dropdown('get value')
        if (Array.isArray(val)) user_ids = val.map(String)
        else if (typeof val === 'string' && val.length) user_ids = val.split(',').map(String)
      } catch(e) {
        try {
          const sel = self.refs.group_user_select
          for (let i = 0; i < sel.options.length; i++) if (sel.options[i].selected) user_ids.push(String(sel.options[i].value))
        } catch(e2){}
      }

      const pk = compPk()
      if (!pk) {
        if (self.refs.group_modal_error) {
          self.refs.group_modal_error.style.display = 'block'
          self.refs.group_modal_error.textContent = "Impossible de trouver l'ID de la compétition."
        }
        return
      }

      let url = '/competitions/' + pk + '/groups/create/'
      if (self.editing_group && self.editing_group.id) url = '/competitions/' + pk + '/groups/' + self.editing_group.id + '/update/'

      // Build FormData (classic Django POST format)
      const form = new FormData()
      form.append('name', name)
      if (queue_id) form.append('queue_id', queue_id)
      for (let i = 0; i < user_ids.length; i++) form.append('user_ids[]', user_ids[i])

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: form
      }).then(resp => {
        if (!resp.ok) throw resp
        return resp.json()
      }).then(data => {
        if (data && data.status === 'ok' && data.group) {
          const g = data.group
          let found = false
          for (let i = 0; i < self.available_groups.length; i++) {
            if (self.available_groups[i].id === g.id) {
              self.available_groups[i] = g
              found = true
              break
            }
          }
          if (!found) {
            self.available_groups.push(g)
            if (self.selected_group_ids.indexOf(g.id) === -1) self.selected_group_ids.push(g.id)
          }

          self.data = self.data || {}
          self.data.participant_groups = self.selected_group_ids.slice()
          CODALAB.events.trigger('competition_data_update', self.data)

          self.close_group_modal()
          self.scheduleUpdate && self.scheduleUpdate()
        } else {
          const err = (data && data.error) ? data.error : 'Erreur création/modification'
          if (self.refs.group_modal_error) {
            self.refs.group_modal_error.style.display = 'block'
            self.refs.group_modal_error.textContent = err
          }
        }
      }).catch(err => {
        console.error('group create/update error', err)
        if (self.refs.group_modal_error) {
          self.refs.group_modal_error.style.display = 'block'
          self.refs.group_modal_error.textContent = 'Erreur réseau lors de la création/modification du groupe.'
        }
      })
    }

    // delete group (POST form-style)
    self.delete_group = (group) => {
      if (!confirm('Supprimer le groupe "' + group.name + '" ?')) return
      const pk = compPk()
      if (!pk) return
      const url = '/competitions/' + pk + '/groups/' + group.id + '/delete/'

      // Use an empty FormData (server only expects POST; no body required but consistent)
      const form = new FormData()
      form.append('dummy', '1')

      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: form
      }).then(resp => {
        if (!resp.ok) throw resp
        return resp.json()
      }).then(data => {
        // remove from UI
        self.available_groups = self.available_groups.filter(x => x.id !== group.id)
        self.selected_group_ids = self.selected_group_ids.filter(x => x !== group.id)

        self.data = self.data || {}
        self.data.participant_groups = self.selected_group_ids.slice()
        CODALAB.events.trigger('competition_data_update', self.data)
        self.scheduleUpdate && self.scheduleUpdate()
      }).catch(err => {
        console.error('delete group error', err)
        alert('Erreur lors de la suppression du groupe.')
      })
    }

    CODALAB.events.on('competition_loaded', function (competition) {
        try {
          if (self.refs) {
            if (self.refs.registration_auto_approve) self.refs.registration_auto_approve.checked = competition.registration_auto_approve
            if (self.refs.allow_robot_submissions) self.refs.allow_robot_submissions.checked = competition.allow_robot_submissions
          }
        } catch(e){ console.warn('setting checkboxes failed', e) }

        // Si l'éditeur est prêt, appliquer tout de suite, sinon stocker en attente pour mount
        try {
          if (self.markdown_editor && self.markdown_editor.codemirror && typeof self.markdown_editor.codemirror.refresh === 'function') {
            try {
              if (typeof self.markdown_editor.value === 'function') self.markdown_editor.value(competition.terms || '')
              if (self.markdown_editor_whitelist && typeof self.markdown_editor_whitelist.value === 'function') {
                self.markdown_editor_whitelist.value(Array.isArray(competition.whitelist_emails) && competition.whitelist_emails.length > 0 ? competition.whitelist_emails.join('\n') : '')
              }
              self.markdown_editor.codemirror.refresh()
              self.update()
              self.form_updated()
            } catch(e){ console.warn('apply competition_loaded to editors failed', e) }
            return
          }
        } catch(e){ /* ignore */ }

        // stocker la compétition pour l'appliquer lorsque mount aura créé les éditeurs
        self._pending_competition = competition
    })

    CODALAB.events.on('update_codemirror', () => {
      try {
        if (self.markdown_editor && self.markdown_editor.codemirror && typeof self.markdown_editor.codemirror.refresh === 'function') {
          self.markdown_editor.codemirror.refresh()
        }
      } catch(e) { console.warn('update_codemirror failed', e) }
    })
  </script>


  <style>
    .ui.cards .card {
      width: 100%;
      margin-bottom: 1em;
    }
    .ui.cards .content .meta, .ui.cards .content .description {
      margin-top: 0.5em;
    }

    .group-meta {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      flex-wrap: wrap;
    }

    .group-labels {
      display:flex;
      gap:0.5rem;
      align-items:center;
    }

    .members-chips {
      display:flex;
      gap:0.35rem;
      flex-wrap:wrap;
      margin-left:0.5rem;
    }

    .members-chips .ui.tiny.label {
      background: #f3f4f5;
      border: 1px solid rgba(34,36,38,0.04);
      color: #333;
      padding: .25rem .45rem;
      font-size: 0.95rem;
    }

    .group-actions {
      margin-left: auto;
      display: flex;
      gap: 0.45rem;
      justify-content: flex-end;
      padding: 0.15rem 0.2rem;
    }

    .group-actions .ui.mini.icon.button {
      padding: 0.28em 0.36em;
      min-width: 2.3rem;
      min-height: 2.3rem;
      border-radius: 0.35rem;
      opacity: 0.98;
      box-shadow: none;
      line-height: 1;
      background-color: rgba(255,255,255,0.96);
      border: 1px solid rgba(34,36,38,0.06);
      transition: background-color .12s ease, transform .08s ease, box-shadow .12s ease;
      color: #333;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .group-actions .ui.mini.icon.button .icon {
      font-size: 0.95rem !important;
    }

    .group-actions .ui.mini.icon.button:hover {
      transform: translateY(-2px);
      background-color: rgba(0,0,0,0.06);
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
      opacity: 1;
    }

    .group-actions .ui.mini.icon.basic.button {
      background-color: rgba(250,250,250,0.92);
      border: 1px solid rgba(34,36,38,0.06);
    }

    .group-actions .delete-btn {
      color: #9f3a38;
    }
    .group-actions .edit-btn {
      color: #2b6f9e;
    }

    .group-actions .ui.mini.icon.button:focus {
      outline: 2px solid rgba(43,111,158,0.18);
      outline-offset: 2px;
    }

    .ui.dropdown.multiple { width: 100% !important; }
    .ui.modal { z-index: 10000; }
  </style>
</competition-participation>
