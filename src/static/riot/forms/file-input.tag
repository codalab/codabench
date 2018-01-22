<file-input>
    <!-- This is the SINGLE FILE with NO OTHER OPTIONS example -->
    <!-- In the future, we'll have this type AND a type that is pre-filled with nice options -->
    <div class="ui left action file input">
        <button class="ui icon button" onclick="{ click }">
            <i class="attach icon"></i>
        </button>
        <input type="file" ref="file_input" accept="{ opts.accept }">


        <!-- Drop down selector -->
        <!--<select class="dropdown fluid">
            <option value="test">Test</option>
            <option value="test">Test</option>
        </select>-->

        <!-- Just showing the file after it is uploaded -->
        <input value="{ file_name }" readonly onclick="{ click }">

        <!--<div class="ui progress" data-percent="14" style="margin: 0; -ms-flex: 1 0 auto; flex: 1 0 auto;">
            <div class="bar" style="height: 100%;">
                <div class="progress">14%</div>
            </div>
        </div>-->
    </div>
    <script>
        var self = this

        /*---------------------------------------------------------------------
         Init
        ---------------------------------------------------------------------*/
        self.file_name = ''

        self.one("mount", function () {

            // logo selection
            $(self.refs.file_input).on('change', function (event) {
                // Value comes like c:/fakepath/file_name.txt -- cut out everything but file_name.txt
                self.file_name = self.refs.file_input.value.replace(/\\/g, '/').replace(/.*\//, '')
                self.update()
            })
        })

        /*---------------------------------------------------------------------
         Methods
        ---------------------------------------------------------------------*/
        self.click = function () {
            self.refs.file_input.click()
        }
    </script>
</file-input>
