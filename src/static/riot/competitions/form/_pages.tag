<competition-pages>
    <button class="ui primary button modal-button" onclick="{ add }">
        <i class="add circle icon"></i> Add page
    </button>

    <div class="ui top vertical centered segment grid">

        <div class="five wide column">
            <div class="ui one cards">
                <a each="{page, index in pages}" class="green card">
                    <div class="content">
                        <sorting-chevrons data="{ pages }" index="{ index }" onupdate="{ form_updated }"></sorting-chevrons>
                        <div class="header" onclick="{ edit.bind(this, index) }">{ page.title }</div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like" onclick="{ edit.bind(this, index) }">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star" onclick="{ delete_page.bind(this, index) }">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>
            </div>
        </div>

        <div class="eleven wide column">
            <div class="ui text centered fluid">
                <h1>{ pages[0] ? pages[0].title : null }</h1>
                <div class="ui segment page-content" show="{pages[0]}">
                    <div ref="page_content">

                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="ui modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Page form
        </div>
        <div class="content">
            <form class="ui form" onsubmit="{ save }">
                <div class="field required">
                    <label>Title</label>
                    <input ref="title"/>
                </div>

                <div class="field required">
                    <label>Content</label>
                    <textarea class="markdown-editor" ref="content"></textarea>
                </div>
            </form>
        </div>
        <div class="actions">
            <div class="ui button" onclick="{ close }">Cancel</div>
            <div class="ui button primary" onclick="{ save }">Save</div>
        </div>
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.simple_markdown_editor = undefined
        self.selected_page_index = undefined
        self.pages = []

        self.one("mount", function () {
            // awesome markdown editor
            self.simple_markdown_editor = new EasyMDE({
                element: self.refs.content,
                autoRefresh: true,
                hideIcons: ["preview", "side-by-side", "fullscreen"]
            })

            // Modal callback to draw markdown on show
            $(self.refs.modal).modal({
                onShow: function () {
                    setTimeout(function () {
                        self.simple_markdown_editor.codemirror.refresh()
                    }.bind(self.simple_markdown_editor), 10)
                }
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.add = function () {
            // we're not editing any more, if we were
            self.selected_page_index = undefined

            self.clear_form()
            $(self.refs.modal).modal('show')
        }

        self.clear_form = function () {
            self.refs.title.value = ''
            self.simple_markdown_editor.value('')
        }

        self.close = function () {
            $(self.refs.modal).modal('hide')
        }

        self.edit = function (page_index) {
            self.selected_page_index = page_index
            var page = self.pages[page_index]
            self.refs.title.value = page.title
            self.refs.content.value = page.content
            self.simple_markdown_editor.value(page.content)

            $(self.refs.modal).modal('show')
        }

        self.delete_page = function (page_index) {
            if (self.pages.length == 1) {
                toastr.error("You cannot delete the first page in your competition! You need at least one page.")
            } else {
                if (confirm("Are you sure you want to delete '" + self.pages[page_index].title + "'?")) {
                    self.pages.splice(page_index, 1)
                    self.form_updated()
                }
            }
        }

        self.form_updated = function () {
            var is_valid = true

            // Make sure we have at least 1 page and it has content
            if (self.pages.length == 0) {
                is_valid = false
            } else {
                var content = self.pages[0].content
                if (content == undefined || content === '') {
                    is_valid = false
                }
            }

            CODALAB.events.trigger('competition_is_valid_update', 'pages', is_valid)

            if(is_valid) {
                // Format data nicely, insert indexes so they can be saved
                var indexed_pages = self.pages.map(function(page, index) {
                    page.index = index
                    return page
                })
                self.refs.page_content.innerHTML = sanitize_HTML(self.simple_markdown_editor.markdown(indexed_pages[0].content))
                CODALAB.events.trigger('competition_data_update', {pages: indexed_pages})
            }
        }

        self.save = function (event) {
            if(event) {
                event.preventDefault()
            }

            var data = {
                title: self.refs.title.value,
                content: self.simple_markdown_editor.value()
            }

            if(data.content === '') {
                toastr.error("Cannot save, content is required for a page to save")
                return
            }

            $(self.refs.modal).modal('hide')

            if(self.selected_page_index === undefined) {
                self.pages.push(data)
            } else {
                self.pages[self.selected_page_index] = data
            }

            self.clear_form()
            self.form_updated()
        }

        /*---------------------------------------------------------------------
         Events
        ---------------------------------------------------------------------*/
        CODALAB.events.on('competition_loaded', function(competition){
            self.pages = competition.pages
            self.form_updated()
        })
    </script>
    <style type="text/stylus">
        .page-content
            max-height: 500px;
            overflow: auto;
    </style>
</competition-pages>
