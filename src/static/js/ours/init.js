$(document).ready(function () {
    /*-----------------------------------------------------------------------------
     Template niceties
     */
    // Make base template dropdown not change text on selection
    $("#user_dropdown").dropdown({
        action: 'hide'
    })

    // Sidebar helpers
    $('#mobile_menu')
        .sidebar({
            transition: 'overlay'
        })
        .sidebar('attach events', '#hamburger_button');

    /*-----------------------------------------------------------------------------
     Riotjs
     */
    riot.mount('*')
})
