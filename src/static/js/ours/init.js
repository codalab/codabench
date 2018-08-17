$(document).ready(function () {
    /*-----------------------------------------------------------------------------
     Template niceties
     */
    // header particles
    particlesJS.load('bg', URLS.assets.header_particles)

    // fix menu when passed
    $('.masthead')
        .visibility({
            once: false,
            onBottomPassed: function () {
                $('.fixed.menu').transition('fade in')
            },
            onBottomPassedReverse: function () {
                $('.fixed.menu').transition('fade out')
            }
        })


    // create sidebar and attach to menu open
    $('.ui.sidebar').sidebar('attach events', '.toc.item')

    // Make base template dropdown not change text on selection
    $("#user_dropdown").dropdown({
        action: 'hide'
    })

    /*-----------------------------------------------------------------------------
     Riotjs
     */
    riot.mount('*')
})
