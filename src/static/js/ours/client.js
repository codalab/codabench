var CODALAB = {
    URLS: []  // Set in base.html
}

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

    get_competitions: function (query) {
        // To not pass "undefined" in URL...
        query = query || ''
        return CODALAB.api.request('GET', URLS.API + "competitions/" + query)
    }

    // get_metrics: function () {
    //     return CODALAB.api.request('GET', URLS.API + "leaderboards_metrics")
    // },
    // create_metric: function (data) {
    //     return CODALAB.api.request('POST', URLS.API + "leaderboards_metrics/", data)
    // },
    // update_metric: function (pk, data) {
    //     return CODALAB.api.request('PUT', URLS.API + "leaderboards_metrics/" + pk + "/", data)
    // },
    // delete_metric: function (pk) {
    //     return CODALAB.api.request('DELETE', URLS.API + "leaderboards_metrics/" + pk + "/")
    // },
    // get_columns: function () {
    //     return CODALAB.api.request('GET', URLS.API + "leaderboards_columns")
    // },
    // create_column: function (data) {
    //     return CODALAB.api.request('POST', URLS.API + "leaderboards_columns/", data)
    // },
    // update_column: function(pk, data) {
    //     return CODALAB.api.request('PUT', URLS.API + "leaderboards_columns/" + pk + "/", data)
    // },
    // delete_column: function(pk) {
    //     return CODALAB.api.request('DELETE', URLS.API + "leaderboards_columns/" + pk + "/")
    // },
    // get_leaderboards: function () {
    //     return CODALAB.api.request('GET', URLS.API + "leaderboards_leaderboards")
    // },
    // create_leaderboard: function (data) {
    //     return CODALAB.api.request('POST', URLS.API + "leaderboards_leaderboards/", data)
    // },
    // update_leaderboard: function (pk, data) {
    //     return CODALAB.api.request('PUT', URLS.API + "leaderboards_leaderboards/" + pk + "/", data)
    // },
    // delete_leaderboard: function (pk) {
    //     return CODALAB.api.request('DELETE', URLS.API + "leaderboards_leaderboards/" + pk + "/")
    // },
}
