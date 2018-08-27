var CODALAB = {}

CODALAB.URLS = []  // Set in base.html
CODALAB.events = riot.observable()

// Private function, shouldn't be directly used
var _upload_ajax = function(endpoint, form_data, progress_update_callback) {
    return $.ajax({
        type: 'PUT',
        url: endpoint,
        data: form_data,
        processData: false,
        contentType: false,
        xhr: function (xhr) {
            var request = new window.XMLHttpRequest();

            // Upload progress
            request.upload.addEventListener("progress", function (event) {
                if (event.lengthComputable) {
                    var percent_complete = event.loaded / event.total;
                    if (progress_update_callback) {
                        progress_update_callback(percent_complete * 100);
                    }
                }
            }, false);
            return request;
        }
    })
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
        // Todo This should call chahub??
        return CODALAB.api.request('GET', URLS.API + "query/?q=" + query)
    },

    /*---------------------------------------------------------------------
         Competitions
    ---------------------------------------------------------------------*/
    get_competition: function (pk) {
        return CODALAB.api.request('GET', URLS.API + "competitions/" + pk + "/")
    },
    get_competitions: function (query) {
        // To not pass "undefined" in URL...
        query = query || ''
        return CODALAB.api.request('GET', URLS.API + "competitions/" + query)
    },
    create_competition: function (data) {
        return CODALAB.api.request('POST', URLS.API + "competitions/", data)
    },
    update_competition: function (data, pk) {
        return CODALAB.api.request('PATCH', URLS.API + "competitions/" + pk + "/", data)
    },

    /*---------------------------------------------------------------------
         Submissions
    ---------------------------------------------------------------------*/
    get_submissions: function (query, type) {
        // return CODALAB.api.request('GET', URLS.API + `submissions/?q=${query || ''}&type=${type || ''}`)
        return CODALAB.api.request('GET', URLS.API + `submissions/`)
    },
    delete_submission: function (id) {
        return CODALAB.api.request('DELETE', URLS.API + "submissions/" + id + "/")
    },
    create_submission: function (form_data, progress_update_callback) {
        // NOTE: this function takes a special "form_data" not like the normal
        // dictionary other methods take


        /*
            Set variable CODALAB.IS_SERVER_LOCAL_STORAGE = true or false via context variable

            Local storage:
                * POST to server

            Remote storage:
                * POST to server
                * Server returns SAS URL
                * PUT to SAS URL
                * POST to mark upload as done, so un-finished uploads can be pruned later

        */
        return _upload_ajax(URLS.API + "submissions/", form_data, progress_update_callback)
    },

    /*---------------------------------------------------------------------
         Datasets
    ---------------------------------------------------------------------*/
    get_datasets: function (query, type) {
        return CODALAB.api.request('GET', URLS.API + `datasets/?q=${query || ''}&type=${type || ''}`)
    },
    delete_dataset: function (id) {
        return CODALAB.api.request('DELETE', URLS.API + "datasets/" + id + "/")
    },
    create_dataset: function (form_data, progress_update_callback, success_callback, error_callback) {
        // NOTE: this function takes a special "form_data" not like the normal
        // dictionary other methods take

        // TODO: CHECK WHAT KIND OF STORAGE WE ARE!


        console.log(form_data)

        var payload = {};
        form_data.forEach(function(value, key){
            // Add everything but data_file to the form_data so we can get the SAS URL for uploading
            if(key === 'data_file') {
                payload['request_sassy_file_name'] = value.name
            } else {
                payload[key] = value
            }
        })

        // This will be set on successful dataset creation, then used to complete the dataset upload
        var dataset = {}
        console.log("Payload:")
        console.log(payload)

        return CODALAB.api.request('POST', URLS.API + "datasets/", payload)
            // We have an upload URL, so upload now..
            .then(function(result, result_status) {
                console.log(result)
                console.log("Result status: " + result_status)
                dataset = result

                return $.ajax({
                    type: 'PUT',
                    url: result.sassy_url,
                    data: form_data.get('data_file'),
                    processData: false,
                    contentType: false,
                    xhr: function (xhr) {
                        var request = new window.XMLHttpRequest();

                        // Upload progress
                        request.upload.addEventListener("progress", function (event) {
                            if (event.lengthComputable) {
                                var percent_complete = event.loaded / event.total;
                                if (progress_update_callback) {
                                    progress_update_callback(percent_complete * 100);
                                }
                            }
                        }, false);
                        return request;
                    }
                })
            })
            // Now we should complete the upload by telling Codalab! (so competition unpacking and such can start)
            .then(function(result, result_status) {
                console.log(result)
                console.log("Result status: " + result_status)

                return CODALAB.api.request('PUT', URLS.API + "datasets/completed/" + dataset.key + "/")

            })












        // For local storage we can directly upload
        //return _upload_ajax(URLS.API + "datasets/", form_data, progress_update_callback)
        //    .then(function() {
        //        console.log("THEN'd")
        //    })






        // First we need to get a signed URL

        // Then we upload to it














        // Actually, cancel direct uploads, we should make remote uploads for local storage work
        // we will eventually have to do that anyway.........








        // For remote storage we have to do...
        //  get_upload_url
        //  _upload_ajax
        //    when above is completed, mark_dataset_upload_complete
    },
}
