<submission-limit>

    <div class="ui sixteen wide column submission-container">

        <div if="{isOrgScope()}" class="scope-banner">
            <i class="users icon"></i>
            Submission limits are shared by your organization
            <b if="{selected_phase.organization_name}">({selected_phase.organization_name})</b>
        </div>

        <div class="cols">
            <div class="col">
                <div class="col-content">
                    Number of submissions used for the day
                    <a class="help-icon" data-tooltip="The submission limit resets at midnight server time." data-position="right center">
                        <i class="grey question circle icon"></i>
                    </a>
                </div>
                <span if="{selected_phase.max_submissions_per_day > 0}" class="badge {badgeColor(selected_phase.used_submissions_per_day, selected_phase.max_submissions_per_day)}">
                    {selected_phase.used_submissions_per_day} out of {selected_phase.max_submissions_per_day}
                </span>
                <span if="{selected_phase.max_submissions_per_day == 0}" class="badge badge-green">
                    {selected_phase.used_submissions_per_day} out of ∞
                </span>
            </div>
            <div class="col">
                <div class="col-content">
                    Total submissions used by your organization
                </div>
                <span if="{selected_phase.max_submissions_per_person > 0}" class="badge {badgeColor(selected_phase.used_submissions_per_person, selected_phase.max_submissions_per_person)}">
                    {selected_phase.used_submissions_per_person} out of {selected_phase.max_submissions_per_person}
                </span>
                <span if="{selected_phase.max_submissions_per_person == 0}" class="badge badge-green">
                    {selected_phase.used_submissions_per_person} out of ∞
                </span>
            </div>
        </div>
    </div>

    <script>
        var self = this;
        self.selected_phase = {}

        self.isOrgScope = function() {
            return self.selected_phase.max_submissions_scope === 'organization';
        };

        self.badgeColor = function(used, max) {
            var percentage = (used / max) * 100;
            if (percentage < 5) return "badge-green";
            if (percentage < 25) return "badge-yellow";
            if (percentage < 50) return "badge-orange";
            if (percentage < 75) return "badge-pink";
            return "badge-red";
        };

        CODALAB.events.on('phase_selected', function (selected_phase) {
            self.selected_phase = selected_phase;
            self.update();
        });
    </script>

    <style type="text/stylus">
        .submission-container
            margin-top 1em
            background-color white
            padding 2em
            border solid 1px #dcdcdcdc

        .scope-banner
            margin-bottom 1.5em
            padding 0.7em 1em
            background-color #e3f2fd
            color #1565c0
            border-radius 5px

        .cols
            display flex

        .col
            flex 1
            display flex
            flex-direction column
            justify-content space-between

        .col-content
            font-weight bold
            text-align center

        .help-icon
            margin-left 0.4em

        .badge
            padding 0.5em 1em
            text-align center
            display inline-block
            width max-content
            margin 0 auto
            margin-top 0.5em
            border-radius 5px

        .badge-green
            background-color #a5d6a7

        .badge-yellow
            background-color #fff59d

        .badge-orange
            background-color #ffcc80

        .badge-pink
            background-color #ff80ab

        .badge-red
            background-color #e57373
    </style>
</submission-limit>