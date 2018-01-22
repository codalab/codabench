var CODALAB = {
    URLS: []  // Set in base.html
}

CODALAB.events = riot.observable()

CODALAB.api = {
    request: function (method, url, data) {
        return $.ajax({
            type: method,
            url: url,
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: 'json'
        })
    },

    search: function (query) {
        // TODO: This should call chahub??
        return CODALAB.api.request('GET', URLS.API + "query/?q=" + query)
    },

    /*---------------------------------------------------------------------
         Competitions
    ---------------------------------------------------------------------*/
    get_competitions: function (query) {
        // To not pass "undefined" in URL...
        query = query || ''
        return CODALAB.api.request('GET', URLS.API + "competitions/" + query)
    },

    /*---------------------------------------------------------------------
         Datasets
    ---------------------------------------------------------------------*/
    get_datasets: function() {
        return CODALAB.api.request('GET', URLS.API + "datasets/")
    },
    delete_dataset: function(id) {
        return CODALAB.api.request('DELETE', URLS.API + "datasets/" + id + "/")
    }
}
