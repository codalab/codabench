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
    get_competition: function (pk, secret_key) {

        if(secret_key == undefined || secret_key == 'None'){
            return CODALAB.api.request('GET', URLS.API + "competitions/" + pk + "/")
        }else{
            return CODALAB.api.request('GET', URLS.API + "competitions/" + pk + "/?secret_key="+secret_key)
        }
        
    },
    get_competitions: function (query) {
        return CODALAB.api.request('GET', URLS.API + "competitions/", query)
    },
    get_public_competitions: function (query) {
        return CODALAB.api.request('GET', URLS.API + "competitions/public/", query)
    },
    create_competition: function (data) {
        return CODALAB.api.request('POST', URLS.API + "competitions/", data)
    },
    get_competition_creation_status: function (id) {
        return CODALAB.api.request('GET', `${URLS.API}competitions/${id}/creation_status/`)
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
    submit_competition_registration: function (pk, secret_key) {
        // Create an object to hold the data to be sent in the POST request
        const requestData = {secret_key: secret_key}
        return CODALAB.api.request('POST', `${URLS.API}competitions/${pk}/register/`, requestData)
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
    create_competition_dump: function (pk, keys_instead_of_files) {
        return CODALAB.api.request('POST', `${URLS.API}competitions/${pk}/create_dump/`, {keys_instead_of_files: keys_instead_of_files})
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
    update_submission_fact_sheet: function (pk, data) {
        return CODALAB.api.request('PATCH', `${URLS.API}submissions/${pk}/update_fact_sheet/`, data)
    },
    delete_submission: function (pk) {
        return CODALAB.api.request('DELETE', `${URLS.API}submissions/${pk}/`)
    },
    soft_delete_submission: function (pk) {
        return CODALAB.api.request('DELETE', `${URLS.API}submissions/${pk}/soft_delete/`)
    },
    delete_many_submissions: function (pks) {
        return CODALAB.api.request('DELETE', `${URLS.API}submissions/delete_many/`, pks)
    },
    toggle_submission_is_public: function (pk) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${pk}/toggle_public/`)
    },
    cancel_submission: function (id) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${id}/cancel_submission/`)
    },
    run_submission: function (id) {
        return CODALAB.api.request('POST', `${URLS.API}submissions/${id}/run_submission/`)
    },
    re_run_submission: function (id) {
        return CODALAB.api.request('POST', `${URLS.API}submissions/${id}/re_run_submission/`)
    },
    re_run_many_submissions: function (data) {
        return CODALAB.api.request('POST', `${URLS.API}submissions/re_run_many_submissions/`, data)
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
    get_submission_detail_result: function (id) {
        return CODALAB.api.request('GET', `${URLS.API}submissions/${id}/get_detail_result/`)
    },
    download_many_submissions: function (pks) {
        console.log('Request bulk');
        const params = new URLSearchParams({ pks: JSON.stringify(pks) });
        const url = `${URLS.API}submissions/download_many/?${params}`;
        return fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.blob();
        }).then(blob => {
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = 'bulk_submissions.zip';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }).catch(error => {
            console.error('Error downloading submissions:', error);
        });
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
        return CODALAB.api.request('GET', `${URLS.API}phases/${phase_pk}/get_leaderboard/`)
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
    get_public_datasets: function (query) {
        return CODALAB.api.request('GET', URLS.API + "datasets/public/", query)
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
        metadata.file_name = data_file.name
        metadata.file_size = data_file.size

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
                    contentType: data_file.type === 'application/x-zip-compressed' ? 'application/zip' : data_file.type,
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
    upload_task: (data_file, progress_update_callback) => {
        var form_data = new FormData()
        form_data.append('file', data_file)
        return $.ajax({
            type: 'POST',
            url: URLS.API + 'tasks/upload_task/',
            data: form_data,
            processData: false,
            contentType: false,
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                // Track upload progress
                xhr.upload.addEventListener('progress', function (event) {
                    if (event.lengthComputable) {
                        var percent_complete = (event.loaded / event.total) * 100;
                        if (progress_update_callback) {
                            progress_update_callback(percent_complete);
                        }
                    }
                }, false);
                return xhr;
            }
        });
    },    
    share_task: (pk, data) => {
        return CODALAB.api.request('PATCH', `${URLS.API}tasks/${pk}/`, data)
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
    update_user_details: (id, data) => {
        return CODALAB.api.request('PATCH',`${URLS.API}users/${id}/`, data)
    },
    get_user_participant_organizations: () => {
        return CODALAB.api.request('GET',`${URLS.API}users/participant_organizations/`)
    },
    /*---------------------------------------------------------------------
         Organizations
    ---------------------------------------------------------------------*/
    create_organization: (data) => {
        return CODALAB.api.request('POST', `${URLS.API}organizations/`, data)
    },
    update_organization: (data, id) => {
        return CODALAB.api.request('PUT', `${URLS.API}organizations/${id}/`, data)
    },
    update_user_group: (data, id) => {
        return CODALAB.api.request('POST', `${URLS.API}organizations/${id}/update_member_group/`, data)
    },
    update_organization_invite: (data, method) => {
        return CODALAB.api.request(method, `${URLS.API}organizations/invite_response/`, data)
    },
    validate_organization_invite: (data) => {
        return CODALAB.api.request('POST', `${URLS.API}organizations/validate_invite/`, data)
    },
    invite_user_to_organization: (id, data) => {
        return CODALAB.api.request('POST', `${URLS.API}organizations/${id}/invite_users/`, data)
    },
    delete_organization_member: (id, data) => {
        return CODALAB.api.request('DELETE', `${URLS.API}organizations/${id}/delete_member/`, data)
    },
    delete_organization: (id) => {
        return CODALAB.api.request('DELETE', `${URLS.API}organizations/${id}/delete_organization/`)
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
    get_storage_usage_history: (filters) => {
        return CODALAB.api.request('GET', `${URLS.API}analytics/storage_usage_history/`, filters);
    },
    get_competitions_usage: (filters) => {
        return CODALAB.api.request('GET', `${URLS.API}analytics/competitions_usage/`, filters);
    },
    get_users_usage: (filters) => {
        return CODALAB.api.request('GET', `${URLS.API}analytics/users_usage/`, filters);
    },
    delete_orphan_files: () => {
        return CODALAB.api.request('DELETE', `${URLS.API}analytics/delete_orphan_files/`)
    },
    get_orphan_files: () => {
        return CODALAB.api.request('GET', `${URLS.API}analytics/get_orphan_files/`)
    },
    check_orphans_deletion_status: () => {
        return CODALAB.api.request('GET', `${URLS.API}analytics/check_orphans_deletion_status/`)
    },
    /*---------------------------------------------------------------------
         User Quota and Cleanup
    ---------------------------------------------------------------------*/
    get_user_quota_cleanup: () => {
        return CODALAB.api.request('GET', `${URLS.API}user_quota_cleanup/`)
    },
    get_user_quota: () => {
        return CODALAB.api.request('GET', `${URLS.API}user_quota/`)
    },
    delete_unused_tasks: () => {
        return CODALAB.api.request('DELETE', `${URLS.API}delete_unused_tasks/`)
    },
    delete_unused_datasets: () => {
        return CODALAB.api.request('DELETE', `${URLS.API}delete_unused_datasets/`)
    },
    delete_unused_submissions: () => {
        return CODALAB.api.request('DELETE', `${URLS.API}delete_unused_submissions/`)
    },
    delete_failed_submissions: () => {
        return CODALAB.api.request('DELETE', `${URLS.API}delete_failed_submissions/`)
    },
    /*---------------------------------------------------------------------
         User Account
    ---------------------------------------------------------------------*/
    request_delete_account: (data) => {
        return CODALAB.api.request('DELETE', `${URLS.API}delete_account/`, data)
    },
}
