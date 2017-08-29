/*-----------------------------------------------------------------------------
 Load in template niceties
 */
$(document).ready(function () {
    // header particles
    particlesJS.load('bg', CODALAB.URLS.assets.header_particles)

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

    // dropdowns (nice non-select ones!)
    $(".ui.dropdown").dropdown()
})

/*-----------------------------------------------------------------------------
 Mount all riotjs components
 */
riot.mount('*')
