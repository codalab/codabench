<competition-pages>
    <button class="ui primary button modal-button" onclick="{ add }">
        <i class="add circle icon"></i> Add page
    </button>

    <div class="ui top vertical centered segment grid">

        <div class="five wide column">
            <div class="ui one cards">
                <a each="{page, index in pages}" class="green card">
                    <div class="content">
                        <sorting-chevrons data="{ pages }" index="{ index }"></sorting-chevrons>
                        <div class="header" onclick="{ edit.bind(this, index) }">{ page.name }</div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like" onclick="{ edit.bind(this, index) }">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star" onclick="{ delete.bind(this, index) }">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>
            </div>
        </div>

        <div class="eleven wide column">
            <div class="ui text centered fluid">
                <h1>{ pages[0].name }</h1>
                <p>(This is the first page people will see upon visiting your competition!)</p>
            </div>

            <br><br>

            <img src="https://semantic-ui.com/images/wireframe/paragraph.png">
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
                    <label>Name</label>
                    <input ref="name"/>
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
        self.pages = [
            //{name: "Welcome!", content: ""}
            {name: "Welcome!", content: "welcome msg"}
            //{name: "sdafasdafds!", content: "asdfasdfasdfdasf"}
        ]

        self.one("mount", function () {
            // awesome markdown editor
            self.simple_markdown_editor = new SimpleMDE({
                element: self.refs.content,
                autoRefresh: true
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
            self.refs.name.value = ''
            self.simple_markdown_editor.value('')
        }

        self.close = function () {
            $(self.refs.modal).modal('hide')
        }

        self.edit = function (page_index) {
            self.selected_page_index = page_index
            var page = self.pages[page_index]
            self.refs.name.value = page.name
            self.refs.content.value = page.content
            self.simple_markdown_editor.value(page.content)

            $(self.refs.modal).modal('show')
        }

        self.delete = function (page_index) {
            if (self.pages.length == 1) {
                toastr.error("You cannot delete the first page in your competition! You need at least one page.")
            } else {
                if (confirm("Are you sure you want to delete '" + self.pages[page_index].name + "'?")) {
                    self.pages.splice(page_index, 1)
                }
            }
        }

        self.form_update = function () {
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
        }

        self.save = function (event) {
            if(event) {
                event.preventDefault()
            }

            $(self.refs.modal).modal('hide')

            var data = {
                name: self.refs.name.value,
                content: self.refs.content.value
            }

            if(self.selected_page_index === undefined) {
                self.pages.push(data)
            } else {
                self.pages[self.selected_page_index] = data
            }

            self.clear_form()
            self.form_update()
        }
    </script>
</competition-pages>