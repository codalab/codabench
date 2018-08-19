<competition-upload>


    <div class="ui grid container">
        <div class="eight wide column centered form-empty">
            <div class="ui segment">
                <h1 class="ui header">
                    Competition upload
                    <div class="sub header">
                        For more information on creating bundles, please visit the <a href="">Wiki</a>!
                    </div>
                </h1>

                <div class="ui message error" show="{ Object.keys(errors).length > 0 }">
                    <div class="header">
                        Error(s) creating dataset
                    </div>
                    <ul class="list">
                        <li each="{ error, field in errors }">
                            <strong>{field}:</strong> {error}
                        </li>
                    </ul>
                </div>

                <form class="ui form {error: errors}" ref="form" onsubmit="{ save }">
                    <input-file name="data_file" error="{errors.data_file}" accept=".zip"></input-file>

                    <div class="ui grid">
                        <div class="sixteen wide column right aligned">
                            <button class="ui button" type="submit">
                                <i class="upload icon"></i> Upload
                            </button>
                        </div>
                    </div>
                </form>

                <div class="ui indicating progress" ref="progress">
                    <div class="bar">
                        <div class="progress">{ upload_progress }%</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var self = this
    </script>

    <style type="text/stylus">
        :scope
            padding 50px

        .header
            margin-bottom 35px !important
    </style>
</competition-upload>
