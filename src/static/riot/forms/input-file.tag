<!-- Field class on initial definition to keep Semantic UI styling -->
<input-file class="field {error: opts.error}">
    <!-- This is the SINGLE FILE with NO OTHER OPTIONS example -->
    <!-- In the future, we'll have this type AND a type that is pre-filled with nice options -->
    <div class="ui left action file input" ref="submission_upload">
        <button type="button" class="ui icon button" onclick="{ open_file_selection }">
            <i class="attach icon"></i>
        </button>
        <input type="file" name="{ opts.name }" ref="file_input" accept="{ opts.accept }">

        <!-- Just showing the file after it is uploaded -->
        <input ref="file_input_display" readonly onclick="{ open_file_selection }">
    </div>

    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.one("mount", function () {
            // clean up name displaying
            $(self.refs.file_input)
                .on('change', function (event) {
                    // Value comes like c:/fakepath/file_name.txt -- cut out everything but file_name.txt
                    self.refs.file_input_display.value = self.refs.file_input.value.replace(/\\/g, '/').replace(/.*\//, '')
                    self.update()
                })
                .on('click', function() {
                    // Set the value of the input to null so the 'change' event fires even if the same
                    // file is selected!
                    self.refs.file_input.value = null
                })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.open_file_selection = function () {
            self.refs.file_input.click()
            // Re-enable the button after 5 seconds
            self.refs.submission_upload.style['display'] = 'none'
            setTimeout(function () {
                self.refs.submission_upload.style['display'] = ''
            }, 6000);
        }
    </script>
    <style>
        /* Make this component "div like" */
        :scope {
            display: block;
        }
    </style>
</input-file>
