<publish-warning-modal>
    <div class="ui tiny modal publish-warning-modal" ref="modal">
        <div class="header">
            <div class="header-title-group">
                <span>Improve Your Competition Profile</span>
                <span class="step-badge" if="{ active_steps.length > 1 }">
                    { step_index + 1 } / { active_steps.length }
                </span>
            </div>
            <button type="button" class="modal-close-btn" onclick="{ close_modal }" aria-label="Close">
                <i class="close icon"></i>
            </button>
        </div>

        <div class="content">
            <p class="step-description">{ current_step.description }</p>

            <!-- Step: Tags -->
            <div class="step-panel step-tags" if="{ current_step.key === 'tags' }">
                <div class="selected-tags-bar">
                    <div class="tag-pills-container" if="{ selected_tags.length > 0 }">
                        <button type="button"
                                class="tag-pill active"
                                each="{ tag in selected_tags }"
                                onclick="{ toggle_tag }">
                            { tag.name }
                            <i class="delete icon"></i>
                        </button>
                    </div>
                    <span if="{ !selected_tags.length }" class="no-tags-placeholder">
                        No tags selected
                    </span>
                </div>

                <div class="tag-categories-scroll">
                    <div class="tag-category-group" each="{ cat in tags_by_category }">
                        <h5 class="category-title">{ cat.name }</h5>
                        <div class="tag-pills-container">
                            <button type="button"
                                    class="tag-pill { active: is_selected(tag) }"
                                    each="{ tag in cat.tags }"
                                    onclick="{ toggle_tag }">
                                { tag.name }
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Step: Organizer Contact Email -->
            <div class="ui form step-panel step-email" if="{ current_step.key === 'email' }">
                <div class="field { error: email_error }">
                    <label>Contact Email</label>
                    <input type="email"
                           ref="contact_email"
                           placeholder="contact@example.com"
                           value="{ contact_email }"
                           oninput="{ on_email_change }"
                           onkeydown="{ on_email_keydown }">
                    <div class="field-error-text" if="{ email_error }">
                        <i class="exclamation circle icon"></i>
                        <span>{ email_error }</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="actions">
            <div class="ui button" onclick="{ go_back_or_cancel }">
                { step_index > 0 ? 'Back' : 'Cancel' }
            </div>

            <div class="actions-right">
                <div class="ui basic button" if="{ !is_last_step() }" onclick="{ handle_skip }">Skip</div>
                <div class="ui primary button" onclick="{ handle_primary }">
                    { is_last_step() ? 'Publish' : 'Next' }
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this

        self.active_steps = []
        self.step_index = 0
        self.current_step = {}
        self.on_confirm = null

        self.tags_by_category = []
        self.tags_by_id = {}
        self.selected_tags = []

        self.contact_email = ''
        self.email_error = ''

        // Declarative step registry: add future publication check fields here
        self.step_configs = [
            {
                key: 'tags',
                description: 'No tags have been set for this competition. Here are some suggested tags to help participants find your competition.',
                is_missing: function (comp) {
                    return self.tags_by_category.length > 0 && (!comp.tags || comp.tags.length === 0)
                },
                reset: function () {
                    self.selected_tags = []
                },
                apply: function (payload) {
                    if (self.selected_tags.length > 0) {
                        payload.tags = self.selected_tags.map(function (t) { return t.id })
                    }
                }
            },
            {
                key: 'email',
                description: 'No organizer contact email has been provided. Adding one will allow participants to reach out to you for questions or support.',
                is_missing: function (comp) {
                    return !comp.contact_email || !comp.contact_email.trim()
                },
                reset: function () {
                    self.contact_email = ''
                    self.email_error = ''
                },
                validate: function () {
                    var email = self.contact_email.trim()
                    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                        self.email_error = 'Please enter a valid email address.'
                        return false
                    }
                    self.email_error = ''
                    return true
                },
                apply: function (payload) {
                    var email = self.contact_email.trim()
                    if (email) {
                        payload.contact_email = email
                    }
                },
                on_enter: function () {
                    setTimeout(function () {
                        if (self.refs.contact_email) {
                            self.refs.contact_email.value = self.contact_email
                            self.refs.contact_email.focus()
                        }
                    }, 50)
                }
            }
        ]

        self.one('mount', function () {
            $(self.refs.modal).modal({
                closable: false
            })

            CODALAB.api.get_tags()
                .done(function (tags) {
                    var categories = {}
                    self.tags_by_id = {}
                    tags.forEach(function (tag) {
                        self.tags_by_id[tag.id] = tag
                        if (!categories[tag.category_name]) {
                            categories[tag.category_name] = []
                        }
                        categories[tag.category_name].push(tag)
                    })
                    self.tags_by_category = Object.keys(categories).map(function (name) {
                        return { name: name, tags: categories[name] }
                    })
                })
        })

        self.set_step_index = function (index) {
            self.step_index = index
            self.current_step = self.active_steps[index]
            self.update()
            if (self.current_step.on_enter) {
                self.current_step.on_enter()
            }
        }

        self.is_last_step = function () {
            return self.step_index >= self.active_steps.length - 1
        }

        self.open = function (competition, on_confirm) {
            self.step_configs.forEach(function (step) {
                step.reset()
            })

            self.active_steps = self.step_configs.filter(function (step) {
                return step.is_missing(competition)
            })

            if (self.active_steps.length === 0) {
                return on_confirm({})
            }

            self.on_confirm = on_confirm
            self.set_step_index(0)
            $(self.refs.modal).modal('show')

            if (self.current_step.key === 'tags') {
                CODALAB.api.get_auto_tags({
                    id: competition.id,
                    title: competition.title,
                    description: competition.description,
                    pages: competition.pages
                }).done(function (data) {
                    if (self.current_step.key === 'tags' && !self.selected_tags.length && data.tags) {
                        self.selected_tags = data.tags
                            .map(function (id) { return self.tags_by_id[id] })
                            .filter(Boolean)
                        self.update()
                    }
                })
            }
        }

        self.is_selected = function (tag) {
            return self.selected_tags.indexOf(tag) !== -1
        }

        self.toggle_tag = function (e) {
            var idx = self.selected_tags.indexOf(e.item.tag)
            if (idx === -1) {
                self.selected_tags.push(e.item.tag)
            } else {
                self.selected_tags.splice(idx, 1)
            }
        }

        self.on_email_change = function (e) {
            self.contact_email = e.target.value
            if (self.email_error) {
                self.current_step.validate()
            }
        }

        self.on_email_keydown = function (e) {
            if (e.key === 'Enter') {
                e.preventDefault()
                self.handle_primary()
            }
        }

        self.close_modal = function () {
            self.current_step = {}
            $(self.refs.modal).modal('hide')
        }

        self.go_back_or_cancel = function () {
            if (self.step_index > 0) {
                self.set_step_index(self.step_index - 1)
            } else {
                self.close_modal()
            }
        }

        self.finish = function () {
            self.close_modal()
            var payload = {}
            self.active_steps.forEach(function (step) {
                step.apply(payload)
            })
            self.on_confirm(payload)
        }

        self.handle_skip = function () {
            self.current_step.reset()
            self.set_step_index(self.step_index + 1)
        }

        self.handle_primary = function () {
            if (self.current_step.validate && !self.current_step.validate()) {
                return
            }
            if (!self.is_last_step()) {
                return self.set_step_index(self.step_index + 1)
            }
            self.finish()
        }
    </script>
</publish-warning-modal>
