<competition-pages>
    <button class="ui primary button modal-button" ref="modal_button">
        <i class="add circle icon"></i> Create new page
    </button>

    <div class="ui top vertical centered segment grid">

        <div class="five wide column">
            <div class="ui one cards">
                <a each="{page, index in pages}" class="green card">
                    <div class="content">
                        <sorting-chevrons data="{ pages }" index="{ index }"></sorting-chevrons>
                        <div class="header">{ page.name }</div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>
                <!--<a class="green card">
                    <div class="content">
                        <i class="right floated chevron down icon"></i>
                        <i class="right floated chevron up icon"></i>
                        <div class="header">Welcome!</div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>

                <a class="green card">
                    <div class="content">
                        <i class="right floated chevron down icon"></i>
                        <i class="right floated chevron up icon"></i>
                        <div class="header">How to determine something</div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>

                <a class="green card">
                    <div class="content">
                        <i class="right floated chevron down icon"></i>
                        <i class="right floated chevron up icon"></i>
                        <div class="header">Testing something</div>
                    </div>
                    <div class="extra content">
                        <span class="left floated like">
                            <i class="edit icon"></i>
                            Edit
                        </span>
                        <span class="right floated star">
                            <i class="delete icon"></i>
                            Delete
                        </span>
                    </div>
                </a>-->
            </div>
        </div>

        <div class="eleven wide column">
            <div class="ui text centered fluid">
                <h1>Welcome!</h1>
                <p>(This is the first page people will see upon visiting your competition!)</p>
            </div>

            <br><br>

            <img src="https://semantic-ui.com/images/wireframe/paragraph.png">
        </div>
    </div>


    <!--                    <div class="ui form"> -->
    <!--                        <div class="field"> -->
    <!--                            <label>Select page...</label> -->
    <!--                            <select class="ui dropdown"> -->
    <!--                                <option value="test">Test</option> -->
    <!--                                <option value="test">Test</option> -->
    <!--                                <option value="test">Test</option> -->
    <!--                                <option value="test">Test</option> -->
    <!--                            </select> -->
    <!--                        </div> -->
    <!--                    </div> -->

    <div class="ui modal" ref="modal">
        <i class="close icon"></i>
        <div class="header">
            Page form
        </div>
        <div class="content">

            <div class="ui form">
                <div class="field required">
                    <label>Name</label>
                    <input ref="name"/>
                </div>

                <div class="field required">
                    <label>Content</label>
                    <textarea class="markdown-editor" ref="content"></textarea>
                </div>
            </div>
        </div>
        <div class="actions">
            <div class="ui button">Cancel</div>
            <div class="ui button primary" onclick="{ save }">Save</div>
        </div>
    </div>

    <script>
        var self = this

        self.simple_markdown_editor = undefined
        self.pages = [
            {name: "Welcome!", content: ""},
            {name: 'asdf', content: 'asdf'}
        ]

        self.one("mount", function () {
            // modals
            $(self.refs.modal_button).click(function () {
                $(self.refs.modal).modal('show')
            })

            // awesome markdown editor
            self.simple_markdown_editor = new SimpleMDE({element: self.refs.content})
        })

        self.save = function() {
            $(self.refs.modal).modal('hide')

            self.pages.push({name: self.refs.name.value, content: self.refs.content.value})

            self.refs.name.value = ''
            self.simple_markdown_editor.value('')
        }
    </script>
</competition-pages>