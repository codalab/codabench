<submission-management>
    <div class="segment-box">
        <div class="segment-header">
            <div class="segment-title">
                My Submissions
            </div>
        </div>
        <div class="segment-content">
            <div id="daily-sub-progress" class="ui indicating progress" data-value="3" data-total="5">
                <div class="bar"></div>
            </div>
            <div class="label"><strong>Daily Submissions:</strong> 3 of 5</div>
            <div id="total-sub-progress" class="ui indicating progress" data-value="15" data-total="100">
                <div class="bar"></div>
            </div>
            <div class="label"><strong>Total Submissions:</strong> 15 of 100</div>
        </div>
    </div>
<div class="table-wrapper">
        <table class="ui unstackable compact striped table">
            <thead>
            <tr>
                <th>#</th>
                <th>ID</th>
                <th>Score</th>
                <th>Filename</th>
                <th>Submission date</th>
                <th>Status</th>
                <th>Estimated Duration</th>
                <th>Cancel</th>
                <th>Detailed Results</th>
                <th><i class="ui check icon"></i></th>
            </tr>
            </thead>
            <tbody>
            <tr>
                <td>1</td>
                <td>101</td>
                <td>19.00213</td>
                <td>09/14/2018</td>
                <td>submission(1).zip</td>
                <td>Complete</td>
                <td>00:19:18.192</td>
                <td></td>
                <td>
                    <div class="ui button"><i class="ui plus icon"></i></div>
                </td>
                <td></td>
            </tr>
            </tbody>
        </table>
</div>

    <script>
        $(document).ready(function () {
            $('#daily-sub-progress')
                .progress({
                    label: 'ratio',
                    text: {
                        ratio: '{value} of {total}'
                    }
                })

            $('#total-sub-progress')
                .progress({
                    label: 'ratio',
                    text: {
                        ratio: '{value} of {total}'
                    }
                })
        })
    </script>

    <style type="text/stylus">
        .segment-box
            display grid
            grid-template-columns 1fr 1fr
            border solid gainsboro 1px
            border-radius 3px
            grid-template-areas "segment-header segment-header" "segment-content segment-content" "segment-content segment-content"

        .segment-header
            grid-area segment-header
            border-bottom solid 1px gainsboro
            background-color #f6f6f6
            color #b2b2b2
            padding 10px 0 10px 20px

        .segment-content
            grid-area segment-content

            .ui.progress:first-child
                margin 1em 1em 0 1em

            .progress
                height initial
                margin 1em 1em 0 1em

            .label
                margin 0.5em 1em

        .ui.table
            white-space nowrap
            width 100%
            border-color gainsboro

            th
                color #b2b2b2
                font-weight 100
                background-color #f6f6f6

        .table-wrapper
            overflow-x auto
            overflow-y hidden
            margin 1em auto

    </style>
</submission-management>