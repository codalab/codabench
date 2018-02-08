var CODALAB = {
    URLS: []  // Set in base.html
}

CODALAB.events = riot.observable()

var _upload_ajax = function(endpoint, form_data, progress_update_callback) {
    return $.ajax({
            type: 'POST',
            url: URLS.API + endpoint,
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
                            progress_update_callback(percent_complete);
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
        return _upload_ajax("submissions/", form_data, progress_update_callback)
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
    create_dataset: function (form_data, progress_update_callback) {
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
        return _upload_ajax("datasets/", form_data, progress_update_callback)

        /*IFC.api.get_upload_url(file, destination)
            .success(function (data) {
                var form = new FormData();
                var url = data['form_action'];

                // Remove our URL before making upload request form data
                delete data['form_action'];

                Object.keys(data).forEach(function (key) {
                    form.append(key, data[key])
                });
                form.append('file', file);

                $.ajax({
                    type: 'POST',
                    url: url,
                    data: form,
                    processData: false,
                    contentType: false,
                    xhr: function (xhr) {
                        var xhr = new window.XMLHttpRequest();
                        // Upload progress
                        xhr.upload.addEventListener("progress", function (event) {
                            if (event.lengthComputable) {
                                var percent_complete = event.loaded / event.total;
                                if (progress_update_callback) {
                                    progress_update_callback(percent_complete);
                                }
                            }
                        }, false);
                        return xhr;
                    }
                })
                    .success(function (data) {
                        data = xml_to_json(data);
                        success_callback(data);
                    })
                    .error(function () {
                        toastr.error("Could not upload to S3.");
                    });
            })
            .error(function () {
                toastr.error("Could not get URL for uploading.");
            });*/
    },
    /* We will use the following functions when we implement remote storage */
    get_upload_url: function (file, destination) {
        /*var form = new FormData();

        form.append('name', file.name);
        form.append('type', file.type);
        form.append('dest', destination);

        return $.ajax({
            type: 'POST',
            url: URL.pages.s3_direct,
            data: form,
            processData: false,
            contentType: false
        });*/
    },
    mark_dataset_upload_complete: function (id) {

    }
}
