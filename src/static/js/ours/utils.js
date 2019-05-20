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
 timeSince
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

/* ----------------------------------------------------------------------------
 Form data helpers
 ----------------------------------------------------------------------------*/
function get_form_fields(base_element) {
    //return $(':input', self.root).not('button').not('[readonly]').each(function (i, field) {
    //    console.log(field)
    //})
    return $(':input', base_element).not('button').not('[readonly]')
}

function get_form_data(base_element) {
    var fields = get_form_fields(base_element)
    var data = {}
    fields.each(function (i, field) {
        if (!!field.name) {
            //console.log("@@@@@")
            //console.log(field)
            data[field.name] = $(field).val()
        }
        //console.log(field.name + " -> " + $(field).val())
    })
    return data
}

function set_form_data(data, base_element) {
    var fields = get_form_fields(base_element)
    fields.each(function (i, field) {
        if (!!field.name) {
            //console.log("@@@@@")
            //console.log(field)
            console.log(field.name + " -> " + data[field.name])
            $(field).val(data[field.name])
        }
    })
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
