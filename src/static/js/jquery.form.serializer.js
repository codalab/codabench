(function ($) {
    $.fn.serializeJSON = function (options) {
        var o = $.extend({}, options || {});

        var rselectTextarea = /select|textarea/i;
        var rinput = /text|hidden|password|search/i;

        var data = this.map(function () {
            return this.elements ? $.makeArray(this.elements) : this;
        })
            .filter(function () {
                return this.name && !this.disabled &&
                    (this.checked
                        || this.type === 'checkbox'
                        || rselectTextarea.test(this.nodeName)
                        || rinput.test(this.type));
            })
            .map(function (i, elem) {
                var val = $(this).val();
                return val == null ?
                    null :
                    $.isArray(val) ?
                        $.map(val, function (val, i) {
                            return {name: elem.name, value: val};
                        }) :
                        {
                            name: elem.name,
                            value: (this.type === 'checkbox') ? //moar ternaries!
                                (this.checked ? 'true' : 'false') :
                                val
                        };
            }).get();

        var indexed_array = {};

        $.map(data, function (n, i) {
            indexed_array[n['name']] = n['value'];
        });

        return indexed_array;
    };

})(jQuery);
