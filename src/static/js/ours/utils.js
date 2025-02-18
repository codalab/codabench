/* ----------------------------------------------------------------------------
 CSRF wrapper for ajax
 ----------------------------------------------------------------------------*/

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


/* ----------------------------------------------------------------------------
 Delay timer
 ----------------------------------------------------------------------------*/
// This helper function buffers a task to only execute after a delay has been met.
//
// Like, if you're typing in an autocomplete field it should wait until you're
// finished typing before it sends the request
window.delay = (function () {
    var timer = 0;
    return function (callback, ms) {
        clearTimeout(timer);
        timer = setTimeout(callback, ms);
    };
})();

/* ----------------------------------------------------------------------------
 Time Utils
 ----------------------------------------------------------------------------*/
function timeSince(date) {

    var seconds = Math.floor((new Date() - date) / 1000);

    var interval = Math.floor(seconds / 31536000);

    if (interval > 1) {
        return interval + " years";
    }
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) {
        return interval + " months";
    }
    interval = Math.floor(seconds / 86400);
    if (interval > 1) {
        return interval + " days";
    }
    interval = Math.floor(seconds / 3600);
    if (interval > 1) {
        return interval + " hours";
    }
    interval = Math.floor(seconds / 60);
    if (interval > 1) {
        return interval + " minutes";
    }
    return Math.floor(seconds) + " seconds";
}

function pretty_date(date_string) {
    if (!!date_string) {
        return luxon.DateTime.fromISO(date_string).toLocaleString(luxon.DateTime.DATETIME_FULL)
    } else {
        return ''
    }
}

function pretty_bytes(bytes, decimalPlaces = 1, suffix = "B", binary = false) {

    // Ensure bytes is a valid number
    bytes = parseFloat(bytes)
    if (isNaN(bytes) || bytes < 0) {
        return "" // Return empty string for invalid or negative values
    }

    const factor = binary ? 1024.0 : 1000.0;
    const units = binary ? ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi'] : ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z'];

    for (const unit of units) {
        if (Math.abs(bytes) < factor || unit === units[units.length - 1]) {
            return bytes.toFixed(decimalPlaces) + ' ' + unit + suffix;
        }
        bytes /= factor;
    }
    return bytes.toFixed(decimalPlaces) + ' ' + units[units.length - 1] + suffix;
}

/* ----------------------------------------------------------------------------
 Form data helpers
 ----------------------------------------------------------------------------*/
function get_form_fields(base_element) {
    //return $(':input', self.root).not('button').not('[readonly]').each(function (i, field) {
    //    console.log(field)
    //})
    form_fields = $(':input', base_element).not('button').not('[readonly]')
    // Calendars come through as read-only and jQuery leaves them out
    calendars = $('.two.fields .ui.calendar.field input[type="text"]')
    readonly_calendars = $('.two.fields .ui.calendar.field [readonly]')
    // If calendars is readonly_calendars, then append them to form_fields
    if (calendars.length === readonly_calendars.length) {
        var isIdentical = true;
        calendars.each(function(index) {
          if (!$(this).is(readonly_calendars.eq(index))) {
            isIdentical = false;
            return false; // exit the loop
          }
        });
        
        if (isIdentical) {
            form_fields = form_fields.add(calendars)
        } else {
        //   console.log("The two sets are not identical.");
        }
      } else {
        // console.log("The two sets have different lengths and are not identical.");
      }

    return form_fields
}

function get_form_data(base_element) {
    var fields = get_form_fields(base_element)
    var data = {}
    fields.each(function (i, field) {
        if (!!field.name) {
            data[field.name] = $(field).val()
        }
    })
    return data
}

function set_form_data(data, base_element) {
    var fields = get_form_fields(base_element)
    fields.each(function (i, field) {
        if (!!field.name) {
            $(field).val(data[field.name])
        }
    })
}

const easyMDE_rendering_config = {
    markedOptions: {
        sanitize: true,
        sanitizer: function (input) {
            return sanitize_HTML(input)
        }
    }
}

function create_easyMDE(element, showToolBar = true, showStatusBar = true, editorHeight = '300px') {

    var toolbarIcons = []
    if(showToolBar){
        toolbarIcons = ["bold", "italic", "heading", "|", "quote", "unordered-list", "ordered-list", "|", "link", "image", "|", "preview", "guide"]
    }
    let statusItems =  ["lines", "words", "cursor"]


    var markdown_editor = new EasyMDE({
        element: element,
        autoRefresh: true,
        forceSync: true,
        toolbar: toolbarIcons,
        renderingConfig: easyMDE_rendering_config,
        status: showStatusBar ? statusItems : showStatusBar,
        minHeight: editorHeight || '300px' // Adjust the height, default is 300
    })
    element.EASY_MDE = markdown_editor
    return markdown_editor
}

function sanitize_HTML(input, extra_settings) {
    extra_settings = extra_settings || {}
    input = input || ''
    extra_settings.FORBID_TAGS = _.union(extra_settings.FORBID_TAGS, ['style'])
    extra_settings.FORBID_ATTR = _.union(extra_settings.FORBID_ATTR, ['style'])

    return DOMPurify.sanitize(input, extra_settings)
}

function render_markdown(input, extra_settings) {
    extra_settings = extra_settings || {}
    input = input || ''
    if(EasyMDE.prototype.options === undefined) {
        EasyMDE.prototype.options = {
            renderingConfig: easyMDE_rendering_config
        }
    }
    return sanitize_HTML(EasyMDE.prototype.markdown(input), extra_settings)
}

function getBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.readAsDataURL(file)
        reader.onload = () => resolve(reader.result)
        reader.onerror = error => reject(error)
    })
}

/*
    A simple, lightweight jQuery plugin for creating sortable tables.
    https://github.com/kylefox/jquery-tablesort
    Version 0.0.11
*/

(function($) {
    $.tablesort = function ($table, settings) {
        var self = this;
        this.$table = $table;
        this.$thead = this.$table.find('thead');
        this.settings = $.extend({}, $.tablesort.defaults, settings);
        this.$sortCells = this.$thead.length > 0 ? this.$thead.find('th:not(.no-sort)') : this.$table.find('th:not(.no-sort)');
        this.$sortCells.on('click.tablesort', function() {
            self.sort($(this));
        });
        this.index = null;
        this.$th = null;
        this.direction = null;
    };

    $.tablesort.prototype = {

        sort: function(th, direction) {
            var start = new Date(),
                self = this,
                table = this.$table,
                rowsContainer = table.find('tbody').length > 0 ? table.find('tbody') : table,
                rows = rowsContainer.find('tr').has('td, th'),
                cells = rows.find(':nth-child(' + (th.index() + 1) + ')').filter('td, th'),
                sortBy = th.data().sortBy,
                sortedMap = [];

            var unsortedValues = cells.map(function(idx, cell) {
                if (sortBy)
                    return (typeof sortBy === 'function') ? sortBy($(th), $(cell), self) : sortBy;
                return ($(this).data().sortValue != null ? $(this).data().sortValue : $(this).text());
            });
            if (unsortedValues.length === 0) return;

            //click on a different column
            if (this.index !== th.index()) {
                this.direction = 'asc';
                this.index = th.index();
            }
            else if (direction !== 'asc' && direction !== 'desc')
                this.direction = this.direction === 'asc' ? 'desc' : 'asc';
            else
                this.direction = direction;

            direction = this.direction == 'asc' ? 1 : -1;

            self.$table.trigger('tablesort:start', [self]);
            self.log("Sorting by " + this.index + ' ' + this.direction);

            // Try to force a browser redraw
            self.$table.css("display");
            // Run sorting asynchronously on a timeout to force browser redraw after
            // `tablesort:start` callback. Also avoids locking up the browser too much.
            setTimeout(function() {
                self.$sortCells.removeClass(self.settings.asc + ' ' + self.settings.desc);
                for (var i = 0, length = unsortedValues.length; i < length; i++)
                {
                    sortedMap.push({
                        index: i,
                        cell: cells[i],
                        row: rows[i],
                        value: unsortedValues[i]
                    });
                }

                sortedMap.sort(function(a, b) {
                    return self.settings.compare(a.value, b.value) * direction;
                });

                $.each(sortedMap, function(i, entry) {
                    rowsContainer.append(entry.row);
                });

                th.addClass(self.settings[self.direction]);

                self.log('Sort finished in ' + ((new Date()).getTime() - start.getTime()) + 'ms');
                self.$table.trigger('tablesort:complete', [self]);
                //Try to force a browser redraw
                self.$table.css("display");
            }, unsortedValues.length > 2000 ? 200 : 10);
        },

        log: function(msg) {
            if(($.tablesort.DEBUG || this.settings.debug) && console && console.log) {
                console.log('[tablesort] ' + msg);
            }
        },

        destroy: function() {
            this.$sortCells.off('click.tablesort');
            this.$table.data('tablesort', null);
            return null;
        }

    };

    $.tablesort.DEBUG = false;

    $.tablesort.defaults = {
        debug: $.tablesort.DEBUG,
        asc: 'sorted ascending',
        desc: 'sorted descending',
        compare: function(a, b, settings) {
            // Convert the values to numbers for proper sorting
            if (!isNaN(parseFloat(a)) && !isNaN(parseFloat(b))) {
                var a = parseFloat(a);
                var b = parseFloat(b);
            }
            if (a > b) {
                return 1;
            } else if (a < b) {
                return -1;
            } else {
                return 0;
            }
        }
    };

    $.fn.tablesort = function(settings) {
        var table, sortable, previous;
        return this.each(function() {
            table = $(this);
            previous = table.data('tablesort');
            if(previous) {
                previous.destroy();
            }
            table.data('tablesort', new $.tablesort(table, settings));
        });
    };

})(window.Zepto || window.jQuery);
