<competition-details>
    <div class="ui form">
        <div class="field required">
            <label>Title</label>
            <input>
        </div>

        <!--<div class="field required">
            <label>Logo</label>
            <input type="file">
        </div>-->


        <div class="field required">
            <label>Logo</label>


            <!-- This is the SINGLE FILE with NO OTHER OPTIONS example -->
            <!-- In the future, we'll have this type AND a type that is pre-filled with nice options -->
            <div class="ui left action file input">
                <button class="ui icon button" onclick="document.getElementById('form_file_logo').click()">
                    <i class="attach icon"></i>
                </button>
                <input id="form_file_logo" type="file" ref="logo">


                <!-- Drop down selector -->
                <!--<select class="dropdown fluid">
                    <option value="test">Test</option>
                    <option value="test">Test</option>
                </select>-->

                <!-- Just showing the file after it is uploaded -->
                <input value="{ logo_file_name }" readonly onclick="document.getElementById('form_file_logo').click()">

                <!--<div class="ui progress" data-percent="14" style="margin: 0; -ms-flex: 1 0 auto; flex: 1 0 auto;">
                    <div class="bar" style="height: 100%;">
                        <div class="progress">14%</div>
                    </div>
                </div>-->
            </div>
        </div>

        <div class="two fields">
            <div class="ui calendar field required" ref="calendar">
                <label>Start</label>
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text">
                </div>
            </div>

            <div class="ui calendar field" ref="calendar">
                <label>End</label>
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text">
                </div>
            </div>
        </div>

        <!--<div class="field required">
            <label>Description</label>
            <p>Uses <a href="https://simplemde.com/markdown-guide">markdown</a> formatting</p>
            <textarea class="markdown-editor" ref="description"></textarea>
        </div>-->
        <!--                        <div class="field"> -->
        <!--                            <label>Short Text</label> -->
        <!--                            <textarea rows="2"></textarea> -->
        <!--                        </div> -->
    </div>

    <script>
        var self = this

        // We temporarily store this to display it nicely to the user, could be a behavior we break out into its own
        // component later!
        self.logo_file_name = ''

        self.one("mount", function () {
            // datetime pickers
            $(self.refs.calendar).calendar({
                type: 'date',
                popupOptions: {
                    position: 'bottom left',
                    lastResort: 'bottom left',
                    hideOnScroll: false
                }
            })

            // awesome markdown editor
            $(self.refs.description).each(function (i, ele) {
                new SimpleMDE({element: ele})
            })

            // logo selection
            $(self.refs.logo).on('change', function(event){
                // Value comes like c:/fakepath/file_name.txt -- cut out everything but file_name.txt
                self.logo_file_name = self.refs.logo.value.replace(/\\/g, '/').replace(/.*\//, '')
                self.update()
            })
        })
    </script>
</competition-details>