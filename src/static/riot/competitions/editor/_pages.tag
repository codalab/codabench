<competition-pages>
    <div class="ui centered grid">
        <div class="row">
            <div class="fourteen wide column">
                <table class="ui padded striped table">
                    <thead>
                    <tr>
                        <th colspan="2">Pages</th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr each="{page, index in pages}">
                        <td>{page.title}</td>
                        <td class="right aligned">
                            <a class="chevron">
                                <sorting-chevrons data="{ pages }"
                                                  index="{ index }"
                                                  onupdate="{ form_updated }"></sorting-chevrons>
                            </a>
                            <a class="icon-button"
                               onclick="{ view_page.bind(this, index)}">
                                <i class="grey eye icon"></i>
                            </a>
                            <a class="icon-button"
                               onclick="{ edit.bind(this, index) }">
                                <i class="blue edit icon"></i>
                            </a>
                            <a class="icon-button"
                               onclick="{ delete_page.bind(this, index) }">
                                <i class="red trash alternate outline icon"></i>
                            </a>
                        </td>
                    </tr>
                    <tr show="{pages.length === 0}">
                        <td class="center aligned" colspan="2">
                            <em>No pages added yet, at least 1 is required!</em>
                        </td>
                    </tr>
                    </tbody>
                    <tfoot>
                    <tr>
                        <th colspan="2" class="right aligned">
                            <button class="ui tiny inverted green icon button" onclick="{ add }">
                                <i class="add icon"></i> Add page
                            </button>
                        </th>
                    </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    </div>

    <div class="ui modal" ref="edit_modal">
        <i class="close icon"></i>
        <div class="header">
            Page form
        </div>
        <div class="content">
            <form class="ui form" onsubmit="{ save }">
                <div class="field required">
                    <label>Title</label>
                    <input selenium="title" ref="title"/>
                </div>

                <div class="field required">
                    <label>Content</label>
                    <textarea class="markdown-editor" ref="content"></textarea>
                </div>
            </form>
        </div>
        <div class="actions">
            <div class="ui button" onclick="{ close_edit }">Cancel</div>
            <div class="ui button primary" selenium="save1" onclick="{ save }">Save</div>
        </div>
    </div>


    <div class="ui modal" ref="view_modal">
        <i class="close icon"></i>
        <div class="header">
            Page Preview
        </div>
        <div class="scrolling content">
            <div ref="page_content">

            </div>
        </div>
        <div class="actions">
            <div class="ui button primary" onclick="{ edit.bind(this, selected_page_index) }">Edit</div>
            <div class="ui button" onclick="{ close_view }">Close</div>
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
            self.simple_markdown_editor = create_easyMDE(self.refs.content)

            // Modal callback to draw markdown on show
            $(self.refs.edit_modal).modal({
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
            $(self.refs.edit_modal).modal('show')
        }

        self.clear_form = function () {
            self.refs.title.value = ''
            self.simple_markdown_editor.value('')
        }

        self.close_edit = function () {
            $(self.refs.edit_modal).modal('hide')
        }
        self.close_view = function () {
            $(self.refs.view_modal).modal('hide')
        }

        self.edit = function (page_index) {
            self.selected_page_index = page_index
            var page = self.pages[page_index]
            self.refs.title.value = page.title
            self.refs.content.value = page.content
            self.simple_markdown_editor.value(page.content)

            $(self.refs.edit_modal).modal('show')
        }

        self.delete_page = function (page_index) {
            if (confirm("Are you sure you want to delete '" + self.pages[page_index].title + "'?")) {
                self.pages.splice(page_index, 1)
                self.form_updated()
            }
        }

        self.view_page = function (page_index) {
            self.selected_page_index = page_index
            $(self.refs.view_modal).modal('show')
            const rendered_content = renderMarkdownWithLatex(self.pages[page_index].content)
            self.refs.page_content.innerHTML = ""
            rendered_content.forEach(node => {
                self.refs.page_content.appendChild(node.cloneNode(true)); // Append each node
            });
        }

        self.form_updated = function () {
            var is_valid = true
            // Make sure we have at least 1 page and it has content
            if (self.pages.length === 0) {
                is_valid = false
            } else {
                var content = self.pages[0].content
                if (content === undefined || content === '') {
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

            $(self.refs.edit_modal).modal('hide')

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
            self.pages = _.orderBy(competition.pages, 'index')
            self.form_updated()
        })
    </script>
    <style type="text/stylus">
        .chevron, .icon-button
            cursor pointer
    </style>
</competition-pages>
