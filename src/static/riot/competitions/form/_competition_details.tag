<competition-details>
    <div class="ui form">
        <div class="field required">
            <label>Title</label>
            <input ref="title">
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
                <input id="form_file_logo" type="file" ref="logo" accept="image/*">


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
            <div class="ui calendar field required" ref="calendar_start">
                <label>Start</label>
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" ref="start">
                </div>
            </div>

            <div class="ui calendar field" ref="calendar_end">
                <label>End</label>
                <div class="ui input left icon">
                    <i class="calendar icon"></i>
                    <input type="text" ref="end">
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

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.data = {}

        // We temporarily store this to display it nicely to the user, could be a behavior we break out into its own
        // component later!
        self.logo_file_name = ''

        self.one("mount", function () {
            // datetime pickers
            var datetime_options = {
                type: 'date',
                popupOptions: {
                    position: 'bottom left',
                    lastResort: 'bottom left',
                    hideOnScroll: false
                },
                onHide: function () {
                    // Have to do this because onchange isn't fired when date is picked
                    self.form_update()
                }
            }
            var start_options = Object.assign({}, datetime_options, {endCalendar: self.refs.calendar_end})
            var end_options = Object.assign({}, datetime_options, {startCalendar: self.refs.calendar_start})

            $(self.refs.calendar_start).calendar(start_options)
            $(self.refs.calendar_end).calendar(end_options)

            // awesome markdown editor
            $(self.refs.description).each(function (i, ele) {
                new SimpleMDE({element: ele})
            })

            // logo selection
            $(self.refs.logo).on('change', function (event) {
                // Value comes like c:/fakepath/file_name.txt -- cut out everything but file_name.txt
                self.logo_file_name = self.refs.logo.value.replace(/\\/g, '/').replace(/.*\//, '')
                self.update()
            })

            // Form change events
            //self.fields.forEach(function (field) {
            //    self.refs[field].addEventListener('change', self.form_update)
            //    self.refs[field].addEventListener('keydown', self.form_update)
            //})
            $(':input', self.root).not('[type="file"]').not('button').not('[readonly]').each(function (i, field) {
                this.addEventListener('keydown', self.form_update)
            })

            // Capture and convert images to base64 for easy uploading
            $('input[type="file"]', self.root).change(function() {
                getBase64(this.files[0]).then(function(data) {
                    self.data['logo'] = data
                    self.form_update()
                })
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.form_update = function () {
            //get_form_data(self.root)

            var is_valid = true

            /*input_fields.forEach(function (field) {
                data[field] = self.refs[field].value
                if (!data[field]) {
                    is_valid = false
                }
            })*/

            // NOTE: logo is excluded here because it is converted to 64 upon changing
            self.data['title'] = self.refs.title.value

            if(!self.data['title'] || !self.data['logo']) {
                is_valid = false
            }


            CODALAB.events.trigger('competition_is_valid_update', 'details', is_valid)














            // IN THE DATA YOU SEND BACK, WE NEED TO HANDLE FormData for the logo file.....
            // *** so we should set formData.append('logo', data['logo'] = $(logo).files[0]) ***








            //if(is_valid) {
            CODALAB.events.trigger('competition_data_update', self.data)
            //}
        }
    </script>
</competition-details>