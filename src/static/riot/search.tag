<search>
    <div class="ui middle aligned stackable grid container">
        <div class="row centered">
            <div class="twelve wide column">
                <div class="ui form">
                    <div class="inline fields">
                        <div class="field">
                            <div class="ui floating labeled icon dropdown button">
                                <i class="filter icon"></i>
                                <span class="text">Any time</span>
                                <div class="menu">
                                    <div class="header">
                                        Timeframe
                                    </div>
                                    <div class="divider"></div>
                                    <div class="item">
                                        Active
                                    </div>
                                    <div class="item">
                                        Started past month
                                    </div>
                                    <div class="item">
                                        Started past year
                                    </div>
                                    <div class="divider"></div>
                                    <div class="header">
                                        Date range
                                    </div>
                                    <div class="ui left icon input">
                                        <i class="calendar icon"></i>
                                        <input type="text" name="search" placeholder="Start date">
                                    </div>
                                    <div class="ui left icon input">
                                        <i class="calendar icon"></i>
                                        <input type="text" name="search" placeholder="End date">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field">
                            <div class="ui floating labeled icon dropdown multiple button">
                                <i class="filter icon"></i>
                                <span class="text">Attributes (select many)</span>
                                <div class="menu">
                                    <div class="header">
                                        <i class="tags icon"></i>
                                        Competition filters
                                    </div>
                                    <div class="item">
                                        I'm in
                                    </div>
                                    <div class="item">
                                        Has not finished
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="field">
                            <div class="ui floating labeled icon dropdown button">
                                <i class="filter icon"></i>
                                <span class="text">Sorted by</span>
                                <div class="menu">
                                    <div class="item">
                                        Next deadline
                                    </div>
                                    <div class="item">
                                        Prize amount
                                    </div>
                                    <div class="item">
                                        Number of participants
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ui">
                    <div class="ui icon input fluid">
                        <input ref="search_field" class="prompt" type="text" placeholder="Keywords" oninput="{ input_updated }">
                        <i class="search icon"></i>
                    </div>
                </div>
            </div>
        </div>

        <div class="row centered">
            <div class="twelve wide column">
                <div class="ui divided items">
                    <search-result each="{ results }"></search-result>
                </div>
            </div>
        </div>

        <!--<div class="row centered">
            <div class="twelve wide column right aligned">
                <div class="ui pagination menu right aligned">
                    <a class="active item">
                        1
                    </a>
                    <div class="disabled item">
                        ...
                    </div>
                    <a class="item">
                        10
                    </a>
                    <a class="item">
                        11
                    </a>
                    <a class="item">
                        12
                    </a>
                </div>
            </div>
        </div>-->
    </div>

    <script>
        var self = this

        self.on('mount', function(){
            console.log(self)
        })

        self.input_updated = function () {
            delay(function () {
                self.search()
            }, 100)
        }

        self.search = function () {
            CODALAB.api.search(self.refs.search_field.value)
                .done(function(data) {
                    self.update({results: data})
                })
        }
    </script>

    <style>

    </style>
</search>

<search-result class="item">
    <div class="image">
        <img src="https://semantic-ui.com/images/wireframe/image.png">
    </div>
    <div class="content">
        <a class="header">{ title }</a>
        <div class="meta">
            <!--<span class="cinema">IFC</span>-->
        </div>
        <div class="description">
            <p>{ description }</p>
        </div>
        <div class="extra">
            <div class="ui right floated primary button">
                Participate
                <i class="right chevron icon"></i>
            </div>
        </div>
    </div>
</search-result>
