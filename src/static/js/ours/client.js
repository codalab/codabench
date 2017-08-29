var CODALAB = {
    URLS: []  // Set in base.html
}

CODALAB.api = {
    request: function (method, url, data) {
        return $.ajax({
            type: method,
            url: url,
            data: data,
            contentType: "application/json",
            dataType: 'json'
        })
    },
    search: function (query) {
        return CODALAB.api.request('GET', CODALAB.URLS.API + "query/?q=" + query)
    }
}
