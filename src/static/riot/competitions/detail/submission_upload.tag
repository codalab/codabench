<submission-upload>





    <div class="ui sixteen wide column submission-container">
        <h1>Submission upload</h1>

        <pre ref="submission_output">
            <virtual each="{ line in lines }">
                { line }
            </virtual>
        </pre>
        <!--
<pre>Starting upload...upload completed!
Waiting for job to be picked up...picked up!

Output from prediction:
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdfa
    asdf
    asdf
    asdf
    a
    ew
    awef
    f
    32
    q23a
    f23
    fa
    23
    3fq2
    12
    3
    q
    asdf
    af
    q
    32f
    a23f
    aef
    a
    32
    a
    asd
    fa

    32f
    a
    fas
    df
    q23f
    as
    fd


Output from scoring:
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf
    asdfasdf

</pre>-->
    </div>
    <script>
        var self = this

        self.lines = []

        self.one('mount', function() {
            var loop = function() {
                self.lines.push('asdf')
                self.update()
                self.refs.submission_output.scrollTop = self.refs.submission_output.scrollHeight
                setTimeout(loop, 100)
            }
            loop()
        })
    </script>

    <style type="text/stylus">
        :scope
            display block
            width 100%
            height 100%

        code
            background: hsl(220, 80%, 90%)

        .submission-container
            max-height 60vh

        pre
            white-space pre-wrap
            background #1b1c1d
            color #efefef
            max-height 60vh
            overflow-y scroll
            padding 15px
        pre::-webkit-scrollbar
            background-color #efefef
        pre::-webkit-scrollbar-button
            background-color #828282
        pre::-webkit-scrollbar-track
            background-color green
        pre::-webkit-scrollbar-track-piece
            background-color #efefef
        pre::-webkit-scrollbar-thumb
            background-color #575757
            border-radius 0
    </style>
</submission-upload>