CODALAB.events = riot.observable()

CODALAB.api = {
    request: function (method, url, data) {
        if (method.toLowerCase() !== "get") {
            data = JSON.stringify(data)
        }

        return $.ajax({
            type: method,
            url: url,
            data: data,
            contentType: "application/json",
            dataType: 'json'
        })
    },

    search: function (query) {
        return CODALAB.api.request('GET', URLS.API + "query/?q=" + query)
    },

    /*---------------------------------------------------------------------
         Competitions
    ---------------------------------------------------------------------*/
    get_competition: function (pk) {
        return CODALAB.api.request('GET', URLS.API + "competitions/" + pk + "/")
    },
    get_competitions: function (query) {
        return CODALAB.api.request('GET', URLS.API + "competitions/", query)
    },
    create_competition: function (data) {
        return CODALAB.api.request('POST', URLS.API + "competitions/", data)
    },
    get_competition_creation_status: function (key) {
        return CODALAB.api.request('GET', `${URLS.API}competitions/creation_status/${key}/`)
    },
    update_competition: function (data, pk) {
        return CODALAB.api.request('PATCH', URLS.API + "competitions/" + pk + "/", data)
    },
    delete_competition: function (pk) {
        return CODALAB.api.request('DELETE', `${URLS.API}competitions/${pk}/`)
    },
    toggle_competition_publish: function (pk) {
        return CODALAB.api.request('POST', `${URLS.API}competitions/${pk}/toggle_publish/`)
    },
    re_run_phase_submissions: function (phase_pk) {
        return CODALAB.api.request('GET', `${URLS.API}phases/${phase_pk}/rerun_submissions/`)
    },
    manual_migration: function (phase_pk) {
        return CODALAB.api.request('POST', `${URLS.API}phases/${phase_pk}/manually_migrate/`)
    },
    submit_competition_registration: function (pk) {
        return CODALAB.api.request('POST', `${URLS.API}competitions/${pk}/register/`)
    },
    email_all_participants: (pk, message) => {
        return CODALAB.api.request('POST', `${URLS.API}competitions/${pk}/email_all_participants/`, {message: message})
    },
    get_front_page_competitions: function (data) {
        return CODALAB.api.request('GET', `${URLS.API}competitions/front_page/`, data)
    },
    get_competition_files: pk => {
        return CODALAB.api.request('GET', `${URLS.API}competitions/${pk}/get_files/`)
    },
    create_competition_dump: function (pk) {
        return CODALAB.api.request('POST', `${URLS.API}competitions/${pk}/create_dump/`)
    },
    /*---------------------------------------------------------------------
         Submissions
    ---------------------------------------------------------------------*/
    can_make_submissions: function (phase_id) {
        return CODALAB.api.request('GET', `${URLS.API}can_make_submission/${phase_id}`)
    },
    get_submissions: function (filters) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/`, filters)
    },
    get_submission: function (pk) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${pk}/`)
    },
    delete_submission: function (pk) {
        return CODALAB.api.request('DELETE', `${URLS.API}submissions/${pk}/`)
    },
    toggle_submission_is_public: function (pk) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${pk}/toggle_public/`)
    },
    cancel_submission: function (id) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${id}/cancel_submission/`)
    },
    re_run_submission: function (id) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${id}/re_run_submission/`)
    },
    get_submission_csv_URL: function (filters) {
        filters.format = "csv"
        return `${URLS.API}submissions/?${$.param(filters)}`
    },
    create_submission: function (submission_metadata) {
        return CODALAB.api.request('POST', URLS.API + "submissions/", submission_metadata)
    },
    get_submission_details: function (id) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${id}/get_details/`)
    },

    /*---------------------------------------------------------------------
         Leaderboards
    ---------------------------------------------------------------------*/
    add_submission_to_leaderboard: function (submission_pk) {
        return CODALAB.api.request('POST', URLS.API + "submissions/" + submission_pk + '/submission_leaderboard_connection/')
    },
    remove_submission_from_leaderboard: function (submission_pk) {
        return CODALAB.api.request('DELETE', URLS.API + "submissions/" + submission_pk + '/submission_leaderboard_connection/')
    },
    get_leaderboard_for_render: function (phase_pk) {
        return CODALAB.api.request('GET', `${URLS.API}phases/${phase_pk}/get_leaderboard`)
    },
    update_submission_score: function (pk, data) {
        return CODALAB.api.request('PATCH', `${URLS.API}submission_scores/${pk}/`, data)
    },
    /*---------------------------------------------------------------------
         Datasets
    ---------------------------------------------------------------------*/
    /*get_datasets: function (query, type, page) {
        return CODALAB.api.request('GET', URLS.API + `datasets/?q=${query || ''}&page=${page || 1}&type=${type || ''}`)
    },*/
    get_datasets: function (filters) {
        return CODALAB.api.request('GET', `${URLS.API}datasets/`, filters)
    },
    update_dataset: function (pk, data) {
        return CODALAB.api.request('PATCH', `${URLS.API}datasets/${pk}/`, data)
    },
    delete_dataset: function (pk) {
        return CODALAB.api.request('DELETE', `${URLS.API}datasets/${pk}/`)
    },
    delete_datasets: function(pk_list) {
        return CODALAB.api.request('POST', `${URLS.API}datasets/delete_many/`, pk_list)
    },
    /**
     * Creates a dataset
     * @param {object} metadata - name, description, type, data_file, is_public
     * @param {object} data_file - the actual file object to use
     * @param {function} progress_update_callback
     */
    create_dataset: function (metadata, data_file, progress_update_callback) {
        // Pass the requested file name for the SAS url
        metadata.request_sassy_file_name = data_file.name

        // This will be set on successful dataset creation, then used to complete the dataset upload
        var dataset = {}

        return CODALAB.api.request('POST', URLS.API + "datasets/", metadata)
            // We have an upload URL, so upload now..
            .then(function (result) {
                dataset = result
                return $.ajax({
                    type: 'PUT',
                    url: result.sassy_url,
                    data: data_file,
                    processData: false,
                    contentType: false,
                    beforeSend: function (request) {
                        if (STORAGE_TYPE === 'azure') {
                            request.setRequestHeader('x-ms-blob-type', 'BlockBlob')
                            request.setRequestHeader('x-ms-version', '2018-03-28')
                        }
                    },
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
            .then(function () {
                return CODALAB.api.request('PUT', URLS.API + "datasets/completed/" + dataset.key + "/")
            })
    },

    /*---------------------------------------------------------------------
         Tasks
    ---------------------------------------------------------------------*/
    get_tasks: function (filters) {
        return CODALAB.api.request('GET', URLS.API + 'tasks/', filters)
    },
    get_task: function (pk) {
        return CODALAB.api.request('GET', `${URLS.API}tasks/${pk}/`)
    },
    delete_task: function (id) {
        return CODALAB.api.request('DELETE', URLS.API + 'tasks/' + id + '/')
    },
    delete_tasks: function (pk_list) {
        return CODALAB.api.request('POST', URLS.API + 'tasks/delete_many/', pk_list)
    },
    update_task: function (pk, data) {
        return CODALAB.api.request('PATCH', `${URLS.API}tasks/${pk}/`, data)
    },
    create_task: (data) => {
        return CODALAB.api.request('POST', `${URLS.API}tasks/`, data)
    },

    /*---------------------------------------------------------------------
         Queues
    ---------------------------------------------------------------------*/
    get_queues: function (filters) {
        return CODALAB.api.request('GET', `${URLS.API}queues/`, filters)
    },
    get_queue: function (pk) {
        return CODALAB.api.request('GET', `${URLS.API}queues/${pk}/`)
    },
    delete_queue: function (id) {
        return CODALAB.api.request('DELETE', `${URLS.API}queues/${id}/`)
    },
    update_queue: function (data, pk) {
        return CODALAB.api.request('PATCH', `${URLS.API}queues/${pk}/`, data)
    },
    create_queue: (data) => {
        return CODALAB.api.request('POST', `${URLS.API}queues/`, data)
    },

    /*---------------------------------------------------------------------
         Users
    ---------------------------------------------------------------------*/
    user_lookup: (filters) => {
        return CODALAB.api.request('GET', `${URLS.API}user_lookup/`, filters)
    },
    /*---------------------------------------------------------------------
         Participants
    ---------------------------------------------------------------------*/
    get_participants: filters => {
        return CODALAB.api.request('GET', `${URLS.API}participants/`, filters)
    },
    update_participant_status: (pk, data) => {
        return CODALAB.api.request('PATCH', `${URLS.API}participants/${pk}/`, data)
    },
    email_participant: (pk, message) => {
        return CODALAB.api.request('POST', `${URLS.API}participants/${pk}/send_email/`, {message: message})
    },
    /*---------------------------------------------------------------------
         Analytics
    ---------------------------------------------------------------------*/
    get_analytics: (filters) => {
        return CODALAB.api.request('GET', `${URLS.API}analytics/`, filters)
    },
}
